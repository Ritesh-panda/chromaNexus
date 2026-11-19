import re
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import dateutil.parser

def parse_clinical_date(date_str: str) -> Optional[str]:
    """Parses a potential clinical date string into standard ISO YYYY-MM-DD."""
    try:
        clean = re.sub(r'^[^\w]+|[^\w]+$', '', date_str).strip()
        # Exclude pure number years or phone numbers
        if clean.isdigit() and len(clean) != 8:
            return None
        dt = dateutil.parser.parse(clean, dayfirst=True, fuzzy=True)
        # Verify plausible year (1970 to 2035)
        if 1970 <= dt.year <= 2035:
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None

def extract_document_date(text: str, fallback_date: Optional[str] = None) -> str:
    """
    Extracts the clinical/service date mentioned inside the prescription or report text.
    Prioritizes explicit clinical date headers, then scans header text for standalone dates.
    Falls back to user provided date or current date only if no date is found in text.
    """
    if not text:
        return fallback_date or datetime.now().strftime("%Y-%m-%d")

    # Priority 1: Contextual date prefixes (e.g., "Date:", "Prescription Date:", "Collected Date:")
    context_pattern = re.compile(
        r'(?:date(?:\s*(?:of\s+)?(?:visit|service|consultation|admission|discharge|report|collection))?|dated|collected(?:\s*(?:date|on))?|reporting(?:\s*date)?|prescribed(?:\s*date)?|admission\s*date|rx\s*date)[:\s]+([A-Za-z0-9,/\-\. ]{6,25})',
        re.IGNORECASE
    )
    for match in context_pattern.finditer(text[:4000]):
        extracted = parse_clinical_date(match.group(1))
        if extracted:
            return extracted

    # Priority 2: Standalone date patterns near the document header (first 1500 chars)
    header_text = text[:1500]
    standalone_patterns = [
        # YYYY-MM-DD
        r'\b(19\d\d|20\d\d)[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b',
        # DD-MM-YYYY or DD/MM/YYYY
        r'\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](19\d\d|20\d\d)\b',
        # DD Mon YYYY or Mon DD, YYYY
        r'\b(?:0?[1-9]|[12]\d|3[01])\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+(?:19\d\d|20\d\d)\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:0?[1-9]|[12]\d|3[01])[\s,]+(?:19\d\d|20\d\d)\b'
    ]
    for pat in standalone_patterns:
        match = re.search(pat, header_text, re.IGNORECASE)
        if match:
            extracted = parse_clinical_date(match.group(0))
            if extracted:
                return extracted

    return fallback_date or datetime.now().strftime("%Y-%m-%d")

def classify_document_category(text: str, file_name: str = "", fallback_category: Optional[str] = None) -> str:
    """
    Analyzes medical text and file name to automatically categorize the document into:
    - 'prescription'
    - 'blood_report'
    - 'mri' (imaging)
    - 'discharge_summary'
    - 'doctor_notes'
    """
    text_lower = (text or "").lower()
    fname_lower = (file_name or "").lower()
    combined = f"{fname_lower} {text_lower[:5000]}"

    scores: Dict[str, float] = {
        "prescription": 0.0,
        "blood_report": 0.0,
        "mri": 0.0,
        "discharge_summary": 0.0,
        "doctor_notes": 0.0
    }

    # Prescription signals
    rx_keywords = [
        "rx", "prescription", "take 1 tablet", "take 2 tablet", "refill", "dosage",
        "tab.", "cap.", "syp.", "mg daily", "once daily", "twice daily", "after meals",
        "before meals", "p.o.", "b.i.d.", "t.i.d.", "q.d.", "h.s.", "prn", "dispense",
        "sig:", "prescribed by", "tablets", "capsules", "syrup", "ointment"
    ]
    for kw in rx_keywords:
        if kw in combined:
            scores["prescription"] += 2.0 if kw in ("rx", "prescription", "refill", "sig:") else 1.0

    # Lab / Blood Report signals
    lab_keywords = [
        "complete blood count", "cbc", "lipid profile", "lipid panel", "liver function",
        "lft", "kidney function", "kft", "hba1c", "blood sugar", "fasting glucose",
        "hemoglobin", "platelet count", "serum", "specimen", "pathology report",
        "reference range", "normal range", "biochemistry", "hematology", "urine routine",
        "lab report", "test name", "observed value", "units", "biological reference"
    ]
    for kw in lab_keywords:
        if kw in combined:
            scores["blood_report"] += 2.0 if kw in ("complete blood count", "cbc", "lipid profile", "pathology report", "reference range") else 1.0

    # Imaging signals
    img_keywords = [
        "mri", "magnetic resonance", "ct scan", "computed tomography", "x-ray", "radiograph",
        "ultrasound", "sonography", "radiology", "axial", "sagittal", "coronal", "t1-weighted",
        "t2-weighted", "flair", "contrast", "radiologist", "imaging report"
    ]
    for kw in img_keywords:
        if kw in combined:
            scores["mri"] += 2.5 if kw in ("mri", "magnetic resonance", "ct scan", "x-ray", "radiology") else 1.0

    # Discharge Summary signals
    discharge_keywords = [
        "discharge summary", "date of admission", "date of discharge", "hospital course",
        "condition on discharge", "discharge diagnosis", "admitting diagnosis", "inpatient stay",
        "discharge advice", "follow up advice"
    ]
    for kw in discharge_keywords:
        if kw in combined:
            scores["discharge_summary"] += 2.5 if kw in ("discharge summary", "date of discharge", "hospital course") else 1.0

    # Doctor Notes signals
    notes_keywords = [
        "clinical note", "consultation note", "progress note", "soap note", "chief complaint",
        "history of present illness", "assessment and plan", "general physical examination"
    ]
    for kw in notes_keywords:
        if kw in combined:
            scores["doctor_notes"] += 1.5

    best_category, best_score = max(scores.items(), key=lambda x: x[1])

    # If significant evidence is found, use detected category
    if best_score >= 2.0:
        return best_category

    # Fallback to user-supplied category if valid and not default 'blood_report' / 'auto'
    if fallback_category and fallback_category not in ("auto", "all"):
        return fallback_category

    if best_score > 0.0:
        return best_category

    return "blood_report"

def extract_doctor_and_facility(text: str, fallback_doctor: Optional[str] = None, fallback_facility: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Extracts doctor and healthcare facility names from medical document text."""
    doc_name = fallback_doctor
    fac_name = fallback_facility

    # Find doctor name
    doc_match = re.search(r'(?:Dr\.|Doctor|Consultant|Physician)[:\s]+([A-Z][a-zA-Z\.\s]{2,35}(?:MD|MBBS|MS|DNB|FACS)?)', text[:2000])
    if doc_match:
        extracted_doc = doc_match.group(1).strip()
        if len(extracted_doc) > 3:
            doc_name = f"Dr. {extracted_doc}" if not extracted_doc.startswith("Dr.") else extracted_doc

    # Find facility name in top lines
    lines = text[:2000].splitlines()
    for line in lines[:15]:
        line_clean = line.strip()
        if any(w in line_clean.lower() for w in ["hospital", "clinic", "medical center", "healthcare", "diagnostics", "pathology lab", "imaging center"]):
            if len(line_clean) < 60:
                fac_name = line_clean
                break

    return doc_name, fac_name

def generate_smart_title(category: str, doctor: Optional[str], facility: Optional[str], clinical_date: str, file_name: str) -> str:
    """Generates a clean, professional clinical document title."""
    cat_label = {
        "prescription": "Prescription",
        "blood_report": "Laboratory Report",
        "mri": "Diagnostic Imaging (MRI/Scan)",
        "discharge_summary": "Discharge Summary",
        "doctor_notes": "Clinical Consultation Note"
    }.get(category, "Medical Record")

    source = doctor or facility
    if source:
        return f"{cat_label} - {source} ({clinical_date})"
    
    # Clean up filename if no source
    base_name = re.sub(r'[\-_]', ' ', file_name.rsplit('.', 1)[0]).title()
    if cat_label.lower() in base_name.lower():
        return f"{base_name} ({clinical_date})"
    return f"{cat_label} - {base_name} ({clinical_date})"

