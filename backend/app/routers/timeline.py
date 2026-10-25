import re
from typing import List, Optional, Dict, Any, Set
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.timeline import (
    TimelineEventResponse,
    TimelineEventCreate,
    TimelineFacilityResponse,
    TimelineFilterSummary,
)
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.timeline import TimelineEvent
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication, LabResult

router = APIRouter(prefix="/timeline", tags=["Timeline"])


def _extract_year_from_date(date_str: Optional[str]) -> int:
    if not date_str:
        return 0
    m = re.search(r"\b(19\d\d|20\d\d)\b", str(date_str))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return 0
    return 0


def _is_valid_iso_date(date_str: Optional[str]) -> bool:
    if not date_str:
        return False
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(date_str).strip()))


def format_timeline_response(event: TimelineEvent) -> TimelineEventResponse:
    date_val = str(event.date or "Unknown Date").strip()
    is_unknown = not _is_valid_iso_date(date_val)
    yr = event.year if event.year and event.year > 0 else _extract_year_from_date(date_val)

    return TimelineEventResponse(
        id=event.id,
        date=date_val,
        year=yr,
        title=event.title,
        description=event.description,
        type=event.event_type,
        severity=event.severity or "medium",
        doctorName=event.doctor_name,
        facility=event.facility,
        sourceReportId=event.source_report_id,
        sourceReportTitle=event.source_report_title,
        connectedEntities=event.connected_entities or {},
        uploadDate=None,
        isUnknownDate=is_unknown,
        hasConflict=False,
        conflictDetails=None
    )


def _aggregate_patient_events(
    patient_id: str,
    db: Session,
    include_records: bool = True
) -> List[TimelineEventResponse]:
    """
    Synthesizes timeline events across TimelineEvent, MedicalReport, Disease,
    Medication, and significant LabResults while avoiding N+1 queries and deduplicating.
    """
    # 1. Fetch explicit timeline events
    explicit_events = db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient_id).all()
    results: List[TimelineEventResponse] = [format_timeline_response(e) for e in explicit_events]

    if not include_records:
        return results

    # Track reports already referenced to avoid redundant report cards
    referenced_report_ids: Set[str] = {e.sourceReportId for e in results if e.sourceReportId}
    referenced_diagnoses: Set[str] = set()
    referenced_meds: Set[str] = set()

    for e in results:
        if e.connectedEntities:
            for d in e.connectedEntities.get("diseases", []):
                referenced_diagnoses.add(str(d).lower().strip())
            for m in e.connectedEntities.get("medications", []):
                referenced_meds.add(str(m).lower().strip())

    # 2. Medical reports (encounter date vs upload date)
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient_id).all()
    report_dict: Dict[str, MedicalReport] = {r.id: r for r in reports}

    for rep in reports:
        if rep.id in referenced_report_ids:
            # Update existing event's uploadDate if missing
            for ev in results:
                if ev.sourceReportId == rep.id and not ev.uploadDate and rep.upload_date:
                    ev.uploadDate = rep.upload_date.isoformat()
            continue

        raw_date = rep.report_date or "Unknown Date"
        is_unknown = not _is_valid_iso_date(raw_date)
        yr = _extract_year_from_date(raw_date)

        # Categorize report type
        t_lower = (rep.title or "").lower()
        if any(w in t_lower for w in ["mri", "ct", "x-ray", "ultrasound", "scan", "echo"]):
            e_type = "imaging"
        elif any(w in t_lower for w in ["panel", "cbc", "metabolic", "lipid", "lab"]):
            e_type = "lab_test"
        elif any(w in t_lower for w in ["cardiology", "consultation", "evaluation", "visit"]):
            e_type = "hospital_visit"
        else:
            e_type = "medical_report"

        desc = rep.summary or f"Medical record from {rep.hospital_name or 'verified facility'} (File: {rep.file_name})."
        up_date = rep.upload_date.isoformat() if rep.upload_date else None

        results.append(
            TimelineEventResponse(
                id=f"syn_rep_{rep.id}",
                date=raw_date,
                year=yr,
                title=rep.title or f"Clinical Report: {rep.file_name}",
                description=desc,
                type=e_type,
                severity="medium",
                doctorName=rep.doctor_name,
                facility=rep.hospital_name,
                sourceReportId=rep.id,
                sourceReportTitle=rep.title,
                connectedEntities={"diseases": [], "medications": [], "labResults": []},
                uploadDate=up_date,
                isUnknownDate=is_unknown,
                hasConflict=False,
                conflictDetails=None
            )
        )

    # 3. Diagnoses (Disease records)
    diseases = db.query(Disease).filter(Disease.patient_id == patient_id).all()
    for dis in diseases:
        d_name = (dis.name or "").strip()
        if d_name.lower() in referenced_diagnoses:
            continue

        raw_date = dis.diagnosed_date or "Unknown Date"
        is_unknown = not _is_valid_iso_date(raw_date)
        yr = _extract_year_from_date(raw_date)

        rep = report_dict.get(dis.source_report_id) if dis.source_report_id else None
        fac = rep.hospital_name if rep else None
        up_date = rep.upload_date.isoformat() if rep and rep.upload_date else None

        desc = f"Condition: {d_name}"
        if dis.icd_code:
            desc += f" (ICD: {dis.icd_code})"
        desc += f" • Status: {dis.status or 'active'}"
        if dis.treating_doctor:
            desc += f" • Treating: {dis.treating_doctor}"

        results.append(
            TimelineEventResponse(
                id=f"syn_dis_{dis.id}",
                date=raw_date,
                year=yr,
                title=f"Diagnosed: {d_name}",
                description=desc,
                type="diagnosis",
                severity="high" if dis.status == "active" else "medium",
                doctorName=dis.treating_doctor or (rep.doctor_name if rep else None),
                facility=fac,
                sourceReportId=dis.source_report_id,
                sourceReportTitle=rep.title if rep else None,
                connectedEntities={"diseases": [d_name], "medications": [], "labResults": []},
                uploadDate=up_date,
                isUnknownDate=is_unknown,
                hasConflict=False,
                conflictDetails=None
            )
        )

    # 4. Medications
    meds = db.query(Medication).filter(Medication.patient_id == patient_id).all()
    for med in meds:
        m_name = (med.name or "").strip()
        if m_name.lower() in referenced_meds:
            continue

        raw_date = med.start_date or "Unknown Date"
        is_unknown = not _is_valid_iso_date(raw_date)
        yr = _extract_year_from_date(raw_date)

        rep = report_dict.get(med.source_report_id) if med.source_report_id else None
        fac = rep.hospital_name if rep else None
        up_date = rep.upload_date.isoformat() if rep and rep.upload_date else None

        desc = f"Prescribed {m_name} {med.dosage or ''}"
        if med.frequency:
            desc += f" ({med.frequency})"
        if med.indication:
            desc += f" for {med.indication}"
        desc += f" • Status: {med.status or 'active'}"

        results.append(
            TimelineEventResponse(
                id=f"syn_med_{med.id}",
                date=raw_date,
                year=yr,
                title=f"Rx: {m_name} {med.dosage or ''}".strip(),
                description=desc,
                type="medication_start",
                severity="low",
                doctorName=med.prescribing_doctor or (rep.doctor_name if rep else None),
                facility=fac,
                sourceReportId=med.source_report_id,
                sourceReportTitle=rep.title if rep else None,
                connectedEntities={"diseases": [], "medications": [m_name], "labResults": []},
                uploadDate=up_date,
                isUnknownDate=is_unknown,
                hasConflict=False,
                conflictDetails=None
            )
        )

    # 5. Check for same-day multi-facility conflicts
    events_by_date: Dict[str, List[TimelineEventResponse]] = {}
    for ev in results:
        if ev.date and not ev.isUnknownDate:
            events_by_date.setdefault(ev.date, []).append(ev)

    for d_val, d_events in events_by_date.items():
        if len(d_events) > 1:
            facilities = {e.facility for e in d_events if e.facility}
            if len(facilities) > 1:
                # Flag multi-facility presence on same date
                fac_list_str = ", ".join(sorted(facilities))
                for e in d_events:
                    e.hasConflict = True
                    e.conflictDetails = f"Multiple healthcare encounters recorded across different facilities on this date ({fac_list_str})."

    return results


@router.get("", response_model=List[TimelineEventResponse])
def get_timeline(
    year: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    facility: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    order: Optional[str] = Query("desc"),
    include_all_records: bool = Query(True),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns patient-scoped clinical timeline events sorted chronologically by clinical encounter date.
    Distingushes event date from upload date and surfaces multi-facility conflicts.
    """
    events = _aggregate_patient_events(
        patient_id=current_patient.id,
        db=db,
        include_records=include_all_records
    )

    # Apply filters
    if year:
        events = [e for e in events if e.year == year]

    if event_type and event_type != "all":
        if event_type == "medication_start":
            events = [e for e in events if e.type in ["medication_start", "medication_stop"]]
        else:
            events = [e for e in events if e.type == event_type]

    if facility and facility != "all":
        f_lower = facility.lower().strip()
        events = [e for e in events if e.facility and f_lower in e.facility.lower()]

    if start_date:
        events = [e for e in events if not e.isUnknownDate and e.date >= start_date]

    if end_date:
        events = [e for e in events if not e.isUnknownDate and e.date <= end_date]

    # Sort: Valid dates first (descending or ascending), Unknown dates at the bottom
    valid_events = [e for e in events if not e.isUnknownDate]
    unknown_events = [e for e in events if e.isUnknownDate]

    is_desc = (order or "desc").lower() == "desc"
    valid_events.sort(key=lambda x: (x.date, x.title), reverse=is_desc)

    return valid_events + unknown_events


@router.get("/facilities", response_model=TimelineFacilityResponse)
def get_timeline_facilities(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns distinct medical facilities across all verified records for the patient.
    """
    events = _aggregate_patient_events(patient_id=current_patient.id, db=db, include_records=True)
    facilities_set: Set[str] = set()
    for e in events:
        if e.facility and e.facility.strip():
            facilities_set.add(e.facility.strip())

    return TimelineFacilityResponse(facilities=sorted(list(facilities_set)))


@router.get("/summary", response_model=TimelineFilterSummary)
def get_timeline_summary(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns summary metadata for timeline filtering (counts, available types, facilities, years).
    """
    events = _aggregate_patient_events(patient_id=current_patient.id, db=db, include_records=True)
    types_set = {e.type for e in events if e.type}
    fac_set = {e.facility.strip() for e in events if e.facility and e.facility.strip()}
    yrs_set = {e.year for e in events if e.year and e.year > 0}

    dates = [e.date for e in events if not e.isUnknownDate and _is_valid_iso_date(e.date)]
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None

    return TimelineFilterSummary(
        totalEvents=len(events),
        eventTypes=sorted(list(types_set)),
        facilities=sorted(list(fac_set)),
        years=sorted(list(yrs_set), reverse=True),
        dateRange={"earliest": earliest, "latest": latest}
    )


@router.get("/{event_id}", response_model=TimelineEventResponse)
def get_timeline_event(
    event_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    events = _aggregate_patient_events(patient_id=current_patient.id, db=db, include_records=True)
    for e in events:
        if e.id == event_id:
            return e
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline event not found")


@router.post("", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
def create_timeline_event(
    event_in: TimelineEventCreate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    event = TimelineEvent(
        patient_id=current_patient.id,
        date=event_in.date,
        year=event_in.year,
        title=event_in.title,
        description=event_in.description,
        event_type=event_in.type,
        severity=event_in.severity or "medium",
        doctor_name=event_in.doctorName,
        facility=event_in.facility,
        source_report_id=event_in.sourceReportId,
        source_report_title=event_in.sourceReportTitle,
        connected_entities=event_in.connectedEntities or {}
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return format_timeline_response(event)
