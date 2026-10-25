import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication, LabResult
from backend.app.models.allergy import Allergy


def map_gender_to_fhir(gender: str) -> str:
    g = (gender or "").lower()
    if "male" in g:
        return "male"
    elif "female" in g:
        return "female"
    elif "other" in g:
        return "other"
    return "unknown"


def generate_fhir_r4_bundle_for_patient(db: Session, patient: Patient) -> Dict[str, Any]:
    """
    Assembles a standards-compliant HL7 FHIR R4 collection Bundle from verified patient records.
    Every mapped resource maintains strict deterministic identifiers and valid cross-references.
    """
    bundle_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    entries: List[Dict[str, Any]] = []

    # 1. FHIR Patient Resource
    patient_res_id = f"patient-{patient.id}"
    patient_full_url = f"urn:uuid:{patient.id}"
    
    patient_resource: Dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient.id,
        "identifier": [
            {
                "system": "https://chronanexus.app/patients",
                "value": patient.id
            }
        ],
        "active": True,
        "gender": map_gender_to_fhir(patient.gender),
    }

    if patient.user and patient.user.name:
        parts = patient.user.name.split(" ", 1)
        given = [parts[0]]
        family = parts[1] if len(parts) > 1 else ""
        patient_resource["name"] = [
            {
                "use": "official",
                "text": patient.user.name,
                "family": family,
                "given": given
            }
        ]

    if patient.date_of_birth:
        patient_resource["birthDate"] = patient.date_of_birth

    if patient.primary_care_physician:
        patient_resource["generalPractitioner"] = [
            {
                "display": patient.primary_care_physician
            }
        ]

    entries.append({
        "fullUrl": f"urn:uuid:{patient.id}",
        "resource": patient_resource
    })

    # 2. FHIR DocumentReference Resources for Medical Reports
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).all()
    reports_by_id = {r.id: r for r in reports}

    for r in reports:
        doc_ref: Dict[str, Any] = {
            "resourceType": "DocumentReference",
            "id": r.id,
            "status": "current",
            "docStatus": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11506-3" if "blood" in r.category else "34117-2",
                        "display": r.category.replace("_", " ").title()
                    }
                ],
                "text": r.title
            },
            "subject": {
                "reference": f"Patient/{patient.id}"
            },
            "date": r.upload_date.isoformat() if r.upload_date else now_iso,
            "author": [
                {
                    "display": r.doctor_name or r.hospital_name
                }
            ],
            "custodian": {
                "display": r.hospital_name
            },
            "content": [
                {
                    "attachment": {
                        "contentType": r.file_type or "application/pdf",
                        "title": r.file_name,
                        "size": r.file_size or 0,
                        "hash": r.checksum or ""
                    }
                }
            ],
            "context": {
                "period": {
                    "start": r.report_date
                }
            }
        }
        if r.summary:
            doc_ref["description"] = r.summary

        entries.append({
            "fullUrl": f"urn:uuid:{r.id}",
            "resource": doc_ref
        })

    # 3. FHIR Observation Resources for Lab Results
    labs = db.query(LabResult).filter(LabResult.patient_id == patient.id).all()
    for lab in labs:
        obs: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": lab.id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": lab.loinc_code or "unknown",
                        "display": lab.canonical_name or lab.test_name
                    }
                ],
                "text": lab.test_name
            },
            "subject": {
                "reference": f"Patient/{patient.id}"
            },
            "effectiveDateTime": lab.test_date,
        }

        if lab.hospital_name:
            obs["performer"] = [{"display": lab.hospital_name}]

        # Value quantity vs value string
        try:
            numeric_val = float(lab.value.replace(",", "").strip())
            obs["valueQuantity"] = {
                "value": numeric_val,
                "unit": lab.unit,
                "system": "http://unitsofmeasure.org",
                "code": lab.unit
            }
        except Exception:
            obs["valueString"] = f"{lab.value} {lab.unit}".strip()

        # Interpretation
        if lab.status == "high":
            obs["interpretation"] = [{
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": "H", "display": "High"}]
            }]
        elif lab.status == "low":
            obs["interpretation"] = [{
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": "L", "display": "Low"}]
            }]
        elif lab.status == "critical":
            obs["interpretation"] = [{
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": "AA", "display": "Critical abnormal"}]
            }]
        else:
            obs["interpretation"] = [{
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": "N", "display": "Normal"}]
            }]

        if lab.reference_range:
            obs["referenceRange"] = [{"text": lab.reference_range}]

        if lab.source_report_id and lab.source_report_id in reports_by_id:
            obs["derivedFrom"] = [{"reference": f"DocumentReference/{lab.source_report_id}"}]

        entries.append({
            "fullUrl": f"urn:uuid:{lab.id}",
            "resource": obs
        })

    # 4. FHIR Condition Resources for Diseases / Diagnoses
    diseases = db.query(Disease).filter(Disease.patient_id == patient.id).all()
    for d in diseases:
        clin_status = "active" if d.status in ["active", "chronic"] else ("resolved" if d.status in ["resolved", "completed"] else "remission")
        cond: Dict[str, Any] = {
            "resourceType": "Condition",
            "id": d.id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": clin_status
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed"
                    }
                ]
            },
            "code": {
                "text": d.name
            },
            "subject": {
                "reference": f"Patient/{patient.id}"
            },
            "onsetDateTime": d.diagnosed_date,
            "recordedDate": d.diagnosed_date
        }

        if d.icd_code:
            cond["code"]["coding"] = [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": d.icd_code,
                    "display": d.name
                }
            ]

        if d.notes:
            cond["note"] = [{"text": d.notes}]

        if d.source_report_id and d.source_report_id in reports_by_id:
            cond["evidence"] = [{
                "detail": [{"reference": f"DocumentReference/{d.source_report_id}"}]
            }]

        entries.append({
            "fullUrl": f"urn:uuid:{d.id}",
            "resource": cond
        })

    # 5. FHIR AllergyIntolerance Resources
    allergies = db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
    for a in allergies:
        cat = a.category if a.category in ["food", "medication", "environment", "biologic"] else "medication"
        crit = "high" if a.severity in ["severe", "life-threatening"] else ("low" if a.severity == "mild" else "unable-to-assess")
        ai: Dict[str, Any] = {
            "resourceType": "AllergyIntolerance",
            "id": a.id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": a.status or "active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                        "code": "confirmed"
                    }
                ]
            },
            "type": "allergy",
            "category": [cat],
            "criticality": crit,
            "code": {
                "text": a.allergen
            },
            "patient": {
                "reference": f"Patient/{patient.id}"
            }
        }
        if a.reaction:
            ai["reaction"] = [{"manifestation": [{"text": a.reaction}], "severity": a.severity or "moderate"}]
        if a.notes:
            ai["note"] = [{"text": a.notes}]

        entries.append({
            "fullUrl": f"urn:uuid:{a.id}",
            "resource": ai
        })

    # 6. FHIR MedicationStatement Resources
    meds = db.query(Medication).filter(Medication.patient_id == patient.id).all()
    for m in meds:
        med_status = "active" if m.status in ["active", "as_needed"] else ("stopped" if m.status in ["discontinued", "completed"] else "unknown")
        ms: Dict[str, Any] = {
            "resourceType": "MedicationStatement",
            "id": m.id,
            "status": med_status,
            "medicationCodeableConcept": {
                "text": m.name
            },
            "subject": {
                "reference": f"Patient/{patient.id}"
            },
            "effectivePeriod": {
                "start": m.start_date
            },
            "dosage": [
                {
                    "text": f"{m.dosage} {m.frequency}".strip(),
                    "route": {
                        "text": m.route or "oral"
                    }
                }
            ]
        }

        if m.end_date:
            ms["effectivePeriod"]["end"] = m.end_date

        if m.rxnorm_code:
            ms["medicationCodeableConcept"]["coding"] = [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": m.rxnorm_code,
                    "display": m.name
                }
            ]

        if m.indication:
            ms["reasonCode"] = [{"text": m.indication}]

        if m.source_report_id and m.source_report_id in reports_by_id:
            ms["derivedFrom"] = [{"reference": f"DocumentReference/{m.source_report_id}"}]

        entries.append({
            "fullUrl": f"urn:uuid:{m.id}",
            "resource": ms
        })

    # Construct complete FHIR R4 Bundle
    bundle: Dict[str, Any] = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": now_iso,
        "meta": {
            "lastUpdated": now_iso,
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Bundle"
            ]
        },
        "total": len(entries),
        "entry": entries
    }

    return bundle


def validate_fhir_r4_bundle(bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the generated FHIR R4 collection bundle against required structural invariants.
    Returns (True, []) on valid bundle or (False, [errors]) if structural violations exist.
    """
    errors: List[str] = []

    if not isinstance(bundle, dict):
        return False, ["Bundle must be a JSON object"]

    if bundle.get("resourceType") != "Bundle":
        errors.append(f"Expected resourceType 'Bundle', got '{bundle.get('resourceType')}'")

    if bundle.get("type") != "collection":
        errors.append(f"Expected Bundle type 'collection', got '{bundle.get('type')}'")

    entries = bundle.get("entry")
    if not isinstance(entries, list):
        errors.append("Bundle must contain an 'entry' list")
        return False, errors

    # Track all valid internal resource references
    known_resource_targets = set()
    for idx, entry in enumerate(entries):
        res = entry.get("resource")
        if not res or not isinstance(res, dict):
            errors.append(f"Entry {idx} missing valid 'resource' object")
            continue
        res_type = res.get("resourceType")
        res_id = res.get("id")
        if not res_type or not res_id:
            errors.append(f"Entry {idx} resource missing 'resourceType' or 'id'")
            continue
        known_resource_targets.add(f"{res_type}/{res_id}")
        known_resource_targets.add(f"urn:uuid:{res_id}")

    # Validate resource references
    for idx, entry in enumerate(entries):
        res = entry.get("resource", {})
        # Check subject / patient reference
        subj = res.get("subject") or res.get("patient")
        if subj and isinstance(subj, dict):
            ref = subj.get("reference")
            if ref and not ref.startswith("http") and ref not in known_resource_targets:
                errors.append(f"Entry {idx} ({res.get('resourceType')}) references unknown target '{ref}'")

    is_valid = len(errors) == 0
    return is_valid, errors
