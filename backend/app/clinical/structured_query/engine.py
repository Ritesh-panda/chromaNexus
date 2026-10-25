import re
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.app.models.clinical_entity import LabResult
from backend.app.models.report import MedicalReport
from backend.app.clinical.terminology.biomarkers import resolve_biomarker, BIOMARKER_CATALOG
from backend.app.clinical.structured_query.models import (
    StructuredQueryType,
    TrendDirection,
    TimeWindow,
    MeasurementPoint,
    StructuredQueryIntent,
    StructuredTrendResult,
)

logger = logging.getLogger(__name__)


def parse_clinical_numeric(value_str: Optional[str]) -> Optional[float]:
    """
    Safely extracts a numeric float value from lab result strings like '5.8', '105 mg/dL', '< 0.05'.
    """
    if not value_str:
        return None
    m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", str(value_str).strip())
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def parse_reference_range(range_str: Optional[str]) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parses clinical reference range strings like '3.5 - 5.1', '< 100', '> 60', '70-99 mg/dL'.
    Returns (low, high, raw_string).
    """
    if not range_str or not str(range_str).strip() or range_str.lower() in ["none", "n/a", "unavailable", "unknown"]:
        return None, None, "unavailable"

    cleaned = str(range_str).strip()
    # Match range 'low - high' or 'low to high'
    range_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:-|to)\s*([0-9]+(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
    if range_match:
        try:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return low, high, cleaned
        except ValueError:
            pass

    # Match '< high' or '<= high'
    lt_match = re.search(r"<(?:\s*=)?\s*([0-9]+(?:\.[0-9]+)?)", cleaned)
    if lt_match:
        try:
            return 0.0, float(lt_match.group(1)), cleaned
        except ValueError:
            pass

    # Match '> low' or '>= low'
    gt_match = re.search(r">(?:\s*=)?\s*([0-9]+(?:\.[0-9]+)?)", cleaned)
    if gt_match:
        try:
            return float(gt_match.group(1)), None, cleaned
        except ValueError:
            pass

    return None, None, cleaned


def are_units_compatible(unit1: Optional[str], unit2: Optional[str]) -> bool:
    """
    Validates unit compatibility. Case-insensitive standard comparison.
    Never compares incompatible units without validated conversion.
    """
    if not unit1 or not unit2:
        return False
    u1 = unit1.strip().lower()
    u2 = unit2.strip().lower()
    if u1 == u2:
        return True
    # Compatible equivalent synonyms
    equivalents = [
        {"meq/l", "mmol/l"},
        {"mg/dl", "mg/100ml"},
        {"ug/dl", "mcg/dl"},
        {"miu/l", "uiu/ml", "u/l"},
        {"ng/ml", "ug/l"},
    ]
    for eq in equivalents:
        if u1 in eq and u2 in eq:
            return True
    return False


class StructuredClinicalQueryEngine:
    """
    Production Structured Clinical Query & Longitudinal Trends Engine for ChronaNexus.
    Executes deterministic parameterized SQL queries for the authenticated patient,
    computes chronological trends, detects conflicts and unit mismatches, and
    generates grounded, non-diagnostic narrative summaries with traceable citations.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def execute_query(self, intent: StructuredQueryIntent, patient_id: str) -> StructuredTrendResult:
        if not patient_id or not str(patient_id).strip():
            raise ValueError("A valid authenticated patient identity is required to execute clinical queries.")

        clean_patient_id = str(patient_id).strip()

        # Handle multi-analyte queries first
        if intent.is_multi_analyte:
            if intent.query_type == StructuredQueryType.ALL_INCREASING:
                return self._execute_multi_analyte_trend(clean_patient_id, target_direction=TrendDirection.INCREASING)
            elif intent.query_type == StructuredQueryType.ALL_DECREASING:
                return self._execute_multi_analyte_trend(clean_patient_id, target_direction=TrendDirection.DECREASING)

        # Single analyte query
        return self._execute_single_analyte_query(intent, clean_patient_id)

    def _execute_single_analyte_query(self, intent: StructuredQueryIntent, patient_id: str) -> StructuredTrendResult:
        analyte_term = intent.analyte_term
        canonical_name = intent.canonical_name

        # If generic latest query without explicit analyte, resolve to patient's most recent lab test
        if not analyte_term:
            if getattr(intent, "is_generic_latest", False):
                latest_rec = self.db.query(LabResult).filter(LabResult.patient_id == patient_id).order_by(LabResult.test_date.desc()).first()
                if latest_rec:
                    analyte_term = latest_rec.test_name
                    canonical_name = latest_rec.canonical_name or latest_rec.test_name
                    intent.loinc_code = latest_rec.loinc_code
                else:
                    return StructuredTrendResult(
                        query_type=intent.query_type or StructuredQueryType.LATEST_VALUE,
                        analyte_name="Laboratory Measurement",
                        canonical_name="Laboratory Measurement",
                        trend_direction=TrendDirection.NOT_FOUND,
                        has_sufficient_data=False,
                        narrative_summary="No recorded laboratory measurements were found in your verified medical records.",
                        citations=[]
                    )
            else:
                return StructuredTrendResult(
                    query_type=intent.query_type or StructuredQueryType.LATEST_VALUE,
                    analyte_name="Measurement",
                    canonical_name="Measurement",
                    trend_direction=TrendDirection.NOT_FOUND,
                    has_sufficient_data=False,
                    narrative_summary="No matching laboratory measurements were found in your verified medical records.",
                    citations=[]
                )

        analyte_term = analyte_term or "measurement"
        canonical_name = canonical_name or analyte_term.capitalize()

        # 1. Fetch matching measurements from database with Report provenance
        points = self._fetch_analyte_measurements(patient_id, analyte_term, intent.loinc_code)

        # Handle Missing Measurement
        if not points:
            return StructuredTrendResult(
                query_type=intent.query_type or StructuredQueryType.LATEST_VALUE,
                analyte_name=analyte_term,
                canonical_name=canonical_name,
                loinc_code=intent.loinc_code,
                trend_direction=TrendDirection.NOT_FOUND,
                has_sufficient_data=False,
                narrative_summary=f"No recorded measurements for {canonical_name} ({analyte_term}) were found in your verified medical records.",
                citations=[]
            )

        # 2. Check for conflicting measurements across facilities/reports
        conflicts = self._detect_conflicts(points)

        # 3. Apply time window filtering if specified
        filtered_points = points
        time_window_str = None
        if intent.time_window:
            filtered_points, time_window_str = self._apply_time_window(points, intent.time_window)

        if not filtered_points:
            # All measurements fell outside the requested time window
            latest_all = points[-1]
            return StructuredTrendResult(
                query_type=intent.query_type or StructuredQueryType.MEASUREMENT_HISTORY,
                analyte_name=analyte_term,
                canonical_name=canonical_name,
                loinc_code=intent.loinc_code,
                latest_measurement=latest_all,
                all_measurements=points,
                trend_direction=TrendDirection.NOT_FOUND,
                has_sufficient_data=False,
                time_window_applied=time_window_str,
                narrative_summary=(
                    f"No {canonical_name} measurements were recorded during the requested period ({time_window_str}). "
                    f"Your most recent result outside this window was {latest_all.value} {latest_all.unit} on {latest_all.test_date} at {latest_all.facility}."
                ),
                citations=self._build_citations([latest_all])
            )

        # Chronological sort: oldest to newest
        filtered_points.sort(key=lambda p: (p.test_date, p.id))

        latest_pt = filtered_points[-1]
        previous_pt = filtered_points[-2] if len(filtered_points) >= 2 else None

        # 4. Reference range evaluation for latest measurement
        ref_low, ref_high, ref_raw = parse_reference_range(latest_pt.reference_range)
        ref_status = "unavailable"
        if latest_pt.numeric_value is not None:
            if ref_low is not None and ref_high is not None:
                if latest_pt.numeric_value < ref_low:
                    ref_status = "low"
                elif latest_pt.numeric_value > ref_high:
                    ref_status = "elevated"
                else:
                    ref_status = "normal"
            elif ref_high is not None:
                ref_status = "elevated" if latest_pt.numeric_value > ref_high else "normal"
            elif ref_low is not None:
                ref_status = "low" if latest_pt.numeric_value < ref_low else "normal"

        # 5. Unit Compatibility & Trend Direction
        direction = TrendDirection.INSUFFICIENT_DATA
        abs_change = None
        pct_change = None
        unit_mismatch = False

        if previous_pt is not None:
            if not are_units_compatible(latest_pt.unit, previous_pt.unit):
                unit_mismatch = True
                direction = TrendDirection.INCOMPATIBLE_UNITS
            elif latest_pt.numeric_value is not None and previous_pt.numeric_value is not None:
                abs_change = round(latest_pt.numeric_value - previous_pt.numeric_value, 2)
                if previous_pt.numeric_value != 0:
                    pct_change = round((abs_change / previous_pt.numeric_value) * 100.0, 1)

                # Direction determination
                threshold = max(0.01, abs(previous_pt.numeric_value) * 0.01)
                if abs_change > threshold:
                    direction = TrendDirection.INCREASING
                elif abs_change < -threshold:
                    direction = TrendDirection.DECREASING
                else:
                    direction = TrendDirection.STABLE

        # If conflicts exist and user asked for comparison across facilities
        if conflicts and (intent.query_type == StructuredQueryType.COMPARISON_ACROSS_SOURCES or "discrepanc" in intent.raw_query.lower()):
            direction = TrendDirection.CONFLICTING

        # 6. Build Narrative Summary
        narrative = self._generate_narrative_summary(
            intent=intent,
            canonical_name=canonical_name,
            latest=latest_pt,
            previous=previous_pt,
            all_pts=filtered_points,
            direction=direction,
            abs_change=abs_change,
            pct_change=pct_change,
            ref_raw=ref_raw,
            ref_status=ref_status,
            conflicts=conflicts,
            unit_mismatch=unit_mismatch,
            time_window_str=time_window_str
        )

        # 7. Collect relevant Citations
        cited_points = [latest_pt]
        if intent.query_type == StructuredQueryType.HIGHEST_VALUE:
            valid_pts = [p for p in filtered_points if p.numeric_value is not None]
            if valid_pts:
                max_pt = max(valid_pts, key=lambda p: p.numeric_value)
                if max_pt not in cited_points:
                    cited_points.insert(0, max_pt)
        elif intent.query_type == StructuredQueryType.LOWEST_VALUE:
            valid_pts = [p for p in filtered_points if p.numeric_value is not None]
            if valid_pts:
                min_pt = min(valid_pts, key=lambda p: p.numeric_value)
                if min_pt not in cited_points:
                    cited_points.insert(0, min_pt)
        elif previous_pt and previous_pt not in cited_points:
            cited_points.append(previous_pt)
        for c in conflicts:
            if c not in cited_points:
                cited_points.append(c)

        citations = self._build_citations(cited_points)

        return StructuredTrendResult(
            query_type=intent.query_type or StructuredQueryType.LATEST_VALUE,
            analyte_name=analyte_term,
            canonical_name=canonical_name,
            loinc_code=intent.loinc_code,
            latest_measurement=latest_pt,
            previous_measurement=previous_pt,
            all_measurements=filtered_points,
            trend_direction=direction,
            absolute_change=abs_change,
            percentage_change=pct_change,
            unit=latest_pt.unit,
            reference_range=ref_raw if ref_status != "unavailable" else None,
            reference_range_status=ref_status,
            conflicting_measurements=conflicts,
            incompatible_units_detected=unit_mismatch,
            has_sufficient_data=len(filtered_points) >= 2,
            time_window_applied=time_window_str,
            narrative_summary=narrative,
            citations=citations
        )

    def _fetch_analyte_measurements(
        self,
        patient_id: str,
        analyte_term: str,
        loinc_code: Optional[str]
    ) -> List[MeasurementPoint]:
        """
        Executes parameterized database query retrieving all matching lab results for patient.
        """
        q = self.db.query(LabResult, MedicalReport).outerjoin(
            MedicalReport, LabResult.source_report_id == MedicalReport.id
        ).filter(LabResult.patient_id == patient_id)

        # Target LOINCs
        target_loincs = set()
        if loinc_code:
            target_loincs.add(loinc_code)
        defn = resolve_biomarker(analyte_term)
        if defn and defn.loinc_code:
            target_loincs.add(defn.loinc_code)

        # Matching filters
        search_terms = {analyte_term.lower()}
        if defn:
            search_terms.add(defn.canonical_name.lower())
            for s in defn.synonyms:
                search_terms.add(s.lower())

        records = q.all()
        points: List[MeasurementPoint] = []

        for lab, rep in records:
            t_name = lab.test_name.lower()
            c_name = (lab.canonical_name or "").lower()
            l_code = lab.loinc_code or ""

            match = False
            if l_code and l_code in target_loincs:
                match = True
            elif any(term in t_name or term in c_name for term in search_terms):
                match = True
            else:
                # Resolve dynamically
                r_defn = resolve_biomarker(lab.test_name)
                if r_defn and r_defn.loinc_code in target_loincs:
                    match = True

            if not match:
                continue

            facility = lab.hospital_name or (rep.hospital_name if rep else "Clinical Laboratory")
            report_title = rep.title if rep else f"Report #{lab.source_report_id or 'General'}"

            points.append(MeasurementPoint(
                id=lab.id,
                test_name=lab.test_name,
                canonical_name=lab.canonical_name or defn.canonical_name if defn else lab.test_name,
                value=lab.value,
                numeric_value=parse_clinical_numeric(lab.value),
                unit=lab.unit,
                test_date=lab.test_date,
                facility=facility,
                source_report_id=lab.source_report_id,
                source_report_title=report_title,
                reference_range=lab.reference_range,
                status=lab.status or "normal",
                page_number=lab.source_page_number or 1
            ))

        points.sort(key=lambda p: (p.test_date, p.id))
        return points

    def _apply_time_window(self, points: List[MeasurementPoint], window: TimeWindow) -> Tuple[List[MeasurementPoint], str]:
        if not points:
            return [], window.descriptor or "specified window"

        if window.days is not None:
            # Use newest date among points as anchor
            newest_date_str = max(p.test_date for p in points)
            try:
                newest_dt = datetime.fromisoformat(newest_date_str.split("T")[0])
            except Exception:
                newest_dt = datetime.now()

            cutoff_dt = newest_dt - timedelta(days=window.days)
            cutoff_str = cutoff_dt.strftime("%Y-%m-%d")

            filtered = [p for p in points if p.test_date >= cutoff_str]
            return filtered, f"last {window.descriptor or f'{window.days} days'}"

        elif window.start_date and window.end_date:
            filtered = [p for p in points if window.start_date <= p.test_date <= window.end_date]
            return filtered, window.descriptor or f"{window.start_date} to {window.end_date}"

        return points, "all recorded history"

    def _detect_conflicts(self, points: List[MeasurementPoint]) -> List[MeasurementPoint]:
        """
        Detects conflicting readings across facilities or reports (e.g. within 7 days with distinct values).
        """
        if len(points) < 2:
            return []

        conflicts = []
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                p1 = points[i]
                p2 = points[j]
                if p1.facility != p2.facility or p1.source_report_id != p2.source_report_id:
                    # Check date proximity (< 14 days) and value discrepancy
                    try:
                        d1 = datetime.fromisoformat(p1.test_date.split("T")[0])
                        d2 = datetime.fromisoformat(p2.test_date.split("T")[0])
                        if abs((d1 - d2).days) <= 14 and p1.numeric_value != p2.numeric_value:
                            if p1 not in conflicts:
                                conflicts.append(p1)
                            if p2 not in conflicts:
                                conflicts.append(p2)
                    except Exception:
                        pass
        return conflicts

    def _generate_narrative_summary(
        self,
        intent: StructuredQueryIntent,
        canonical_name: str,
        latest: MeasurementPoint,
        previous: Optional[MeasurementPoint],
        all_pts: List[MeasurementPoint],
        direction: TrendDirection,
        abs_change: Optional[float],
        pct_change: Optional[float],
        ref_raw: str,
        ref_status: str,
        conflicts: List[MeasurementPoint],
        unit_mismatch: bool,
        time_window_str: Optional[str]
    ) -> str:
        q_type = intent.query_type or StructuredQueryType.LATEST_VALUE
        ref_clause = ""
        if ref_status != "unavailable":
            ref_clause = f" (Normal range: {ref_raw}, status: {ref_status})"
        else:
            ref_clause = " (Reference range was not documented in the report)"

                # 0. Extremum queries
        if q_type == StructuredQueryType.HIGHEST_VALUE:
            valid_pts = [p for p in all_pts if p.numeric_value is not None]
            target_pt = max(valid_pts, key=lambda p: p.numeric_value) if valid_pts else latest
            ref_c = f" (Normal range: {target_pt.reference_range}, status: {target_pt.status})" if target_pt.reference_range else ""
            return (
                f"Your highest recorded {canonical_name} reading was {target_pt.value} {target_pt.unit} "
                f"on {target_pt.test_date} at {target_pt.facility}{ref_c}."
            )

        if q_type == StructuredQueryType.LOWEST_VALUE:
            valid_pts = [p for p in all_pts if p.numeric_value is not None]
            target_pt = min(valid_pts, key=lambda p: p.numeric_value) if valid_pts else latest
            ref_c = f" (Normal range: {target_pt.reference_range}, status: {target_pt.status})" if target_pt.reference_range else ""
            return (
                f"Your lowest recorded {canonical_name} reading was {target_pt.value} {target_pt.unit} "
                f"on {target_pt.test_date} at {target_pt.facility}{ref_c}."
            )

        # 1. Latest Value query
        if q_type == StructuredQueryType.LATEST_VALUE:
            return (
                f"Your latest recorded {canonical_name} result was {latest.value} {latest.unit} "
                f"on {latest.test_date} at {latest.facility}{ref_clause}."
            )

        # 2. Previous Alongside Latest
        if q_type == StructuredQueryType.PREVIOUS_AND_LATEST:
            if not previous:
                return (
                    f"Your latest {canonical_name} result was {latest.value} {latest.unit} "
                    f"on {latest.test_date} at {latest.facility}{ref_clause}. "
                    f"Only one measurement is documented in your records; no previous reading exists for comparison."
                )
            if unit_mismatch:
                return (
                    f"Your latest {canonical_name} result was {latest.value} {latest.unit} on {latest.test_date} at {latest.facility}{ref_clause}. "
                    f"Your previous result was {previous.value} {previous.unit} on {previous.test_date} at {previous.facility}. "
                    f"Note: A direct numerical comparison cannot be computed because the two reports used incompatible units ({latest.unit} vs {previous.unit})."
                )
            delta_str = f"({abs_change:+g} {latest.unit}" + (f", {pct_change:+g}%)" if pct_change is not None else ")")
            return (
                f"Your latest {canonical_name} result was {latest.value} {latest.unit} on {latest.test_date} at {latest.facility}{ref_clause}. "
                f"Your previous result was {previous.value} {previous.unit} on {previous.test_date} at {previous.facility}, "
                f"representing an absolute change of {delta_str}."
            )

        # 3. Conflicting Sources Comparison
        if q_type == StructuredQueryType.COMPARISON_ACROSS_SOURCES or direction == TrendDirection.CONFLICTING:
            if conflicts:
                items_str = "; ".join(f"{c.value} {c.unit} on {c.test_date} at {c.facility}" for c in conflicts)
                return (
                    f"Your records show conflicting {canonical_name} results across different reports and facilities: {items_str}. "
                    f"Both measurements are preserved accurately from their respective clinical sources."
                )
            elif previous:
                return (
                    f"Comparing your {canonical_name} results across reports: "
                    f"{previous.value} {previous.unit} on {previous.test_date} at {previous.facility}, and "
                    f"{latest.value} {latest.unit} on {latest.test_date} at {latest.facility}."
                )

        # 4. Reference range comparison query
        if q_type == StructuredQueryType.REFERENCE_RANGE_COMPARISON:
            if ref_status == "unavailable":
                return (
                    f"Your latest {canonical_name} was {latest.value} {latest.unit} on {latest.test_date} at {latest.facility}. "
                    f"A reference range was not documented in this report."
                )
            return (
                f"Your latest {canonical_name} was {latest.value} {latest.unit} on {latest.test_date} at {latest.facility}. "
                f"The reference range is {ref_raw}, which places your reading in the {ref_status} range."
            )

        # 5. Trend / Direction of Change / Time Window
        if not previous:
            return (
                f"Your latest {canonical_name} was {latest.value} {latest.unit} on {latest.test_date} at {latest.facility}{ref_clause}. "
                f"Only a single measurement exists in your records, so a trend direction cannot be established."
            )

        if unit_mismatch:
            return (
                f"Your {canonical_name} was recorded as {previous.value} {previous.unit} on {previous.test_date} at {previous.facility} "
                f"and {latest.value} {latest.unit} on {latest.test_date} at {latest.facility}. "
                f"Because the units differ ({previous.unit} vs {latest.unit}), a numerical trend direction cannot be computed."
            )

        window_note = f" over the {time_window_str}" if time_window_str else ""
        delta_str = f"{abs_change:+g} {latest.unit}" + (f" ({pct_change:+g}%)" if pct_change is not None else "")
        return (
            f"Your {canonical_name} has been {direction.value}{window_note}, moving from "
            f"{previous.value} {previous.unit} on {previous.test_date} at {previous.facility} to "
            f"{latest.value} {latest.unit} on {latest.test_date} at {latest.facility} (change: {delta_str}){ref_clause}."
        )

    def _execute_multi_analyte_trend(self, patient_id: str, target_direction: TrendDirection) -> StructuredTrendResult:
        """
        Executes multi-analyte query (e.g. 'Which of my recorded lab values have increased?')
        across all patient lab results.
        """
        q = self.db.query(LabResult, MedicalReport).outerjoin(
            MedicalReport, LabResult.source_report_id == MedicalReport.id
        ).filter(LabResult.patient_id == patient_id).order_by(LabResult.test_date.asc())

        records = q.all()

        # Group by canonical analyte
        by_analyte: Dict[str, List[MeasurementPoint]] = {}
        for lab, rep in records:
            c_name = lab.canonical_name or lab.test_name
            facility = lab.hospital_name or (rep.hospital_name if rep else "Clinical Laboratory")
            report_title = rep.title if rep else f"Report #{lab.source_report_id or 'General'}"
            pt = MeasurementPoint(
                id=lab.id,
                test_name=lab.test_name,
                canonical_name=c_name,
                value=lab.value,
                numeric_value=parse_clinical_numeric(lab.value),
                unit=lab.unit,
                test_date=lab.test_date,
                facility=facility,
                source_report_id=lab.source_report_id,
                source_report_title=report_title,
                reference_range=lab.reference_range,
                status=lab.status or "normal"
            )
            by_analyte.setdefault(c_name, []).append(pt)

        matching_analytes = []
        cited_points = []

        for analyte, pts in by_analyte.items():
            pts.sort(key=lambda p: (p.test_date, p.id))
            if len(pts) >= 2:
                latest = pts[-1]
                prev = pts[-2]
                if are_units_compatible(latest.unit, prev.unit) and latest.numeric_value is not None and prev.numeric_value is not None:
                    delta = latest.numeric_value - prev.numeric_value
                    threshold = max(0.01, abs(prev.numeric_value) * 0.01)

                    if target_direction == TrendDirection.INCREASING and delta > threshold:
                        pct = round((delta / prev.numeric_value) * 100.0, 1) if prev.numeric_value != 0 else 0
                        matching_analytes.append({
                            "analyte": analyte,
                            "previous_value": f"{prev.value} {prev.unit}",
                            "previous_date": prev.test_date,
                            "latest_value": f"{latest.value} {latest.unit}",
                            "latest_date": latest.test_date,
                            "change": f"{delta:+g} {latest.unit} ({pct:+g}%)"
                        })
                        cited_points.extend([prev, latest])
                    elif target_direction == TrendDirection.DECREASING and delta < -threshold:
                        pct = round((delta / prev.numeric_value) * 100.0, 1) if prev.numeric_value != 0 else 0
                        matching_analytes.append({
                            "analyte": analyte,
                            "previous_value": f"{prev.value} {prev.unit}",
                            "previous_date": prev.test_date,
                            "latest_value": f"{latest.value} {latest.unit}",
                            "latest_date": latest.test_date,
                            "change": f"{delta:+g} {latest.unit} ({pct:+g}%)"
                        })
                        cited_points.extend([prev, latest])

        direction_label = "increased" if target_direction == TrendDirection.INCREASING else "decreased"
        if not matching_analytes:
            narrative = f"None of your recorded laboratory measurements with multiple readings showed an {direction_label} trend."
        else:
            bullets = [f"• {item['analyte']}: from {item['previous_value']} ({item['previous_date']}) to {item['latest_value']} ({item['latest_date']}) [Change: {item['change']}]" for item in matching_analytes]
            nl = "\n"
            narrative = f"The following recorded lab values have {direction_label}:{nl}" + "\n".join(bullets)

        return StructuredTrendResult(
            query_type=StructuredQueryType.ALL_INCREASING if target_direction == TrendDirection.INCREASING else StructuredQueryType.ALL_DECREASING,
            analyte_name="All Laboratory Biomarkers",
            canonical_name="All Laboratory Biomarkers",
            trend_direction=target_direction if matching_analytes else TrendDirection.STABLE,
            has_sufficient_data=bool(matching_analytes),
            narrative_summary=narrative,
            multi_analyte_items=matching_analytes,
            citations=self._build_citations(cited_points)
        )

    def _build_citations(self, points: List[MeasurementPoint]) -> List[Dict[str, Any]]:
        seen_reports = set()
        citations = []
        for p in points:
            if not p.source_report_id or p.source_report_id in seen_reports:
                continue
            seen_reports.add(p.source_report_id)
            excerpt = f"{p.test_name}: {p.value} {p.unit} ({p.test_date}) - {p.facility}"
            if p.reference_range and p.reference_range.lower() != "unavailable":
                excerpt += f" [Ref: {p.reference_range}]"

            citations.append({
                "reportId": p.source_report_id,
                "reportTitle": p.source_report_title or f"Report #{p.source_report_id}",
                "date": p.test_date,
                "excerpt": excerpt,
                "confidenceScore": 0.98
            })
        return citations
