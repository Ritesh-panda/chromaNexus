from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity, Disease, Medication, LabResult
from backend.app.models.allergy import Allergy
from backend.app.models.timeline import TimelineEvent
from backend.app.models.chat import ChatConversation, ChatMessage
from backend.app.models.summary import DoctorSummary
from backend.app.core.security import get_password_hash


def seed_initial_data(db: Session):
    """
    Seeds initial demonstration patient (Alex Vance, 38M) into database if not present.
    """
    existing_user = db.query(User).filter(User.email == "alex.vance@example.com").first()
    if existing_user:
        return existing_user

    # 1. Create Default User
    demo_user = User(
        id="usr_alex_vance_001",
        name="Alex Vance",
        email="alex.vance@example.com",
        hashed_password=get_password_hash("Password123!"),
        role="patient",
        avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        phone_number="+1 (555) 234-5678",
        preferences={
            "theme": "system",
            "language": "en",
            "notifications": {
                "email": True,
                "sms": False,
                "criticalAlerts": True,
                "aiDigest": True
            },
            "privacy": {
                "strictDataIsolation": True,
                "localAiProcessingOnly": True,
                "auditableLogsEnabled": True
            }
        }
    )
    db.add(demo_user)
    db.flush()

    # 2. Create Patient Profile
    patient = Patient(
        id="pat_alex_vance_001",
        user_id=demo_user.id,
        date_of_birth="1988-04-12",
        gender="male",
        blood_group="O+",
        height_cm=178.0,
        weight_kg=82.0,
        primary_care_physician="Dr. Sarah Jenkins, MD",
        emergency_contact={
            "name": "Elena Vance",
            "relationship": "Spouse",
            "phone": "+1 (555) 987-6543"
        },
        insurance={
            "providerName": "BlueCross Shield Pro",
            "policyNumber": "BCS-99281-X",
            "groupNumber": "GRP-8812",
            "validUntil": "2027-12-31"
        },
        known_allergies=[
            "Penicillin (Moderate Rash)",
            "Sulfa Drugs (Anaphylaxis Risk)"
        ]
    )
    db.add(patient)
    db.flush()

    # 3. Create Diseases
    diseases = [
        Disease(
            id="dis_001",
            patient_id=patient.id,
            name="Type 2 Diabetes Mellitus",
            icd_code="E11.9",
            status="chronic",
            diagnosed_date="2023-09-18",
            treating_doctor="Dr. Sarah Jenkins, MD",
            source_report_id="rep_005",
            notes="Active glycemic management with Metformin 500mg BID. HbA1c improved from 7.2% to 6.7%."
        ),
        Disease(
            id="dis_002",
            patient_id=patient.id,
            name="Essential (Primary) Hypertension",
            icd_code="I10",
            status="active",
            diagnosed_date="2023-11-04",
            treating_doctor="Dr. Sarah Jenkins, MD",
            source_report_id="rep_004",
            notes="Maintained on Lisinopril 10mg daily. BP well-controlled at 124/80."
        ),
        Disease(
            id="dis_003",
            patient_id=patient.id,
            name="Hyperlipidemia",
            icd_code="E78.5",
            status="active",
            diagnosed_date="2021-06-12",
            treating_doctor="Dr. Robert Chen, MD",
            source_report_id="rep_002",
            notes="Managed on Atorvastatin 10mg QD. Cholesterol decreased to 198 mg/dL."
        ),
        Disease(
            id="dis_004",
            patient_id=patient.id,
            name="Vitamin D Deficiency",
            icd_code="E55.9",
            status="resolved",
            diagnosed_date="2020-03-10",
            resolved_date="2020-09-15",
            treating_doctor="Dr. Robert Chen, MD",
            source_report_id="rep_001",
            notes="Resolved following 12-week high-dose Cholecalciferol supplementation."
        ),
        Disease(
            id="dis_005",
            patient_id=patient.id,
            name="Dengue Fever with Thrombocytopenia",
            icd_code="A90",
            status="resolved",
            diagnosed_date="2019-10-10",
            resolved_date="2019-10-18",
            treating_doctor="Dr. Angela Ramos, MD",
            source_report_id="rep_001",
            notes="Complete recovery after 5-day inpatient fluid resuscitation and platelet monitoring."
        ),
    ]
    for d in diseases:
        db.add(d)

    # 4. Create Medications
    medications = [
        Medication(
            id="med_001",
            patient_id=patient.id,
            name="Metformin HCl",
            dosage="500mg",
            frequency="Twice daily with meals (BID)",
            route="Oral",
            start_date="2023-09-20",
            status="active",
            prescribing_doctor="Dr. Sarah Jenkins, MD",
            indication="Type 2 Diabetes Mellitus",
            source_report_id="rep_005"
        ),
        Medication(
            id="med_002",
            patient_id=patient.id,
            name="Lisinopril",
            dosage="10mg",
            frequency="Once daily in the morning (QD)",
            route="Oral",
            start_date="2023-11-04",
            status="active",
            prescribing_doctor="Dr. Sarah Jenkins, MD",
            indication="Essential Hypertension",
            source_report_id="rep_004"
        ),
        Medication(
            id="med_003",
            patient_id=patient.id,
            name="Atorvastatin Calcium",
            dosage="10mg",
            frequency="Once daily at bedtime (QHS)",
            route="Oral",
            start_date="2021-06-15",
            status="active",
            prescribing_doctor="Dr. Robert Chen, MD",
            indication="Hyperlipidemia",
            source_report_id="rep_002"
        ),
        Medication(
            id="med_004",
            patient_id=patient.id,
            name="Cholecalciferol (Vitamin D3)",
            dosage="60,000 IU",
            frequency="Once weekly for 12 weeks",
            route="Oral",
            start_date="2020-03-12",
            end_date="2020-06-12",
            status="completed",
            prescribing_doctor="Dr. Robert Chen, MD",
            indication="Vitamin D Deficiency",
            source_report_id="rep_001"
        ),
    ]
    for m in medications:
        db.add(m)

    # 4.1 Create Structured Allergies
    allergies = [
        Allergy(
            id="all_001",
            patient_id=patient.id,
            allergen="Penicillin",
            category="medication",
            severity="severe",
            reaction="Anaphylaxis & Generalized Urticaria",
            drug_classes=["Penicillins", "Beta-lactam antibacterials"],
            cross_reactivities=["amoxicillin", "ampicillin", "augmentin", "amoxicillin-clavulanate", "piperacillin"],
            status="active",
            source_report_id="rep_001",
            source_page_number=1,
            extraction_confidence=0.99,
            notes="Documented severe anaphylactic reaction. Beta-lactam aminopenicillins strictly contraindicated."
        ),
        Allergy(
            id="all_002",
            patient_id=patient.id,
            allergen="Sulfa Drugs",
            category="medication",
            severity="moderate",
            reaction="Severe Erythematous Maculopapular Rash",
            drug_classes=["Sulfonamides"],
            cross_reactivities=["bactrim", "septra", "sulfamethoxazole"],
            status="active",
            source_report_id="rep_001",
            source_page_number=1,
            extraction_confidence=0.98,
            notes="Sulfonamide antibacterial hypersensitivity."
        ),
    ]
    for a in allergies:
        db.add(a)

    # 5. Create Lab Results
    lab_results = [
        LabResult(
            id="lab_001",
            patient_id=patient.id,
            test_name="Hemoglobin A1c (HbA1c)",
            category="metabolic",
            value="6.7",
            unit="%",
            reference_range="4.0 - 5.6",
            status="high",
            test_date="2026-06-15",
            source_report_id="rep_008",
            hospital_name="Metro General Hospital"
        ),
        LabResult(
            id="lab_002",
            patient_id=patient.id,
            test_name="Fasting Blood Glucose",
            category="metabolic",
            value="128",
            unit="mg/dL",
            reference_range="70 - 99",
            status="high",
            test_date="2026-06-15",
            source_report_id="rep_008",
            hospital_name="Metro General Hospital"
        ),
        LabResult(
            id="lab_003",
            patient_id=patient.id,
            test_name="Total Cholesterol",
            category="lipid_panel",
            value="198",
            unit="mg/dL",
            reference_range="< 200",
            status="normal",
            test_date="2026-06-15",
            source_report_id="rep_008",
            hospital_name="Metro General Hospital"
        ),
        LabResult(
            id="lab_004",
            patient_id=patient.id,
            test_name="Serum Creatinine",
            category="metabolic",
            value="0.95",
            unit="mg/dL",
            reference_range="0.74 - 1.35",
            status="normal",
            test_date="2026-06-15",
            source_report_id="rep_008",
            hospital_name="Metro General Hospital"
        ),
        LabResult(
            id="lab_005",
            patient_id=patient.id,
            test_name="25-Hydroxy Vitamin D",
            category="vitamin",
            value="42",
            unit="ng/mL",
            reference_range="30 - 100",
            status="normal",
            test_date="2024-05-10",
            source_report_id="rep_006",
            hospital_name="Quest Diagnostics"
        ),
        LabResult(
            id="lab_006",
            patient_id=patient.id,
            test_name="Platelet Count",
            category="cbc",
            value="245",
            unit="x10^3/uL",
            reference_range="150 - 450",
            status="normal",
            test_date="2024-05-10",
            source_report_id="rep_006",
            hospital_name="Quest Diagnostics"
        ),
    ]
    for lr in lab_results:
        db.add(lr)

    # 6. Create Reports
    reports_data = [
        {
            "id": "rep_008",
            "title": "Comprehensive Metabolic & Lipid Panel",
            "fileName": "2026_06_15_Metro_CMP_Lipid.pdf",
            "fileSize": 2450000,
            "fileType": "application/pdf",
            "category": "blood_report",
            "hospitalName": "Metro General Hospital",
            "doctorName": "Dr. Sarah Jenkins, MD",
            "reportDate": "2026-06-15",
            "confidenceScore": 0.99,
            "summary": "Routine metabolic surveillance. HbA1c demonstrated marked improvement to 6.7% (down from 7.2%). Lipid markers stabilized under statin therapy with Total Cholesterol at 198 mg/dL.",
            "rawText": "METRO GENERAL CENTRAL LAB - COMPREHENSIVE METABOLIC PANEL\nPatient: Alex Vance | DOB: 12-Apr-1988\nGlucose: 128 mg/dL [H] (Ref: 70-99)\nHbA1c: 6.7 % [H] (Ref: 4.0-5.6)\nTotal Cholesterol: 198 mg/dL (Ref: <200)\nTriglycerides: 155 mg/dL [H]\nCreatinine: 0.95 mg/dL (Ref: 0.74-1.35)\neGFR: >90 mL/min/1.73m2\nInterpretation: Glycemic control stable on Metformin 500mg BID. Renal function preserved.",
            "entities": [
                {"category": "lab_value", "name": "HbA1c", "value": "6.7", "unit": "%", "confidence": 0.99},
                {"category": "lab_value", "name": "Fasting Blood Glucose", "value": "128", "unit": "mg/dL", "confidence": 0.99},
                {"category": "medication", "name": "Metformin", "value": "500mg", "unit": "BID", "confidence": 0.98},
                {"category": "disease", "name": "Type 2 Diabetes Mellitus", "value": "Controlled", "confidence": 0.97}
            ]
        },
        {
            "id": "rep_007",
            "title": "Cardiovascular Risk & Echo Evaluation",
            "fileName": "2025_11_20_Cardio_Echo_Report.pdf",
            "fileSize": 4120000,
            "fileType": "application/pdf",
            "category": "discharge_summary",
            "hospitalName": "St. Jude Heart & Vascular Center",
            "doctorName": "Dr. Marcus Thorne, FACC",
            "reportDate": "2025-11-20",
            "confidenceScore": 0.97,
            "summary": "Resting 2D Transthoracic Echocardiogram. Normal left ventricular systolic function (LVEF 60-65%). No regional wall motion abnormalities. Normal valvular structure.",
            "rawText": "ST. JUDE CARDIOVASCULAR - TRANSTHORACIC ECHOCARDIOGRAM\nPatient: Alex Vance | Indication: Hypertension surveillance\nLV Ejection Fraction: 62%\nResting Blood Pressure: 124/80 mmHg\nNo left ventricular hypertrophy. Continue Lisinopril 10mg QD.",
            "entities": [
                {"category": "procedure", "name": "Echocardiogram 2D", "value": "LVEF 62%", "confidence": 0.98},
                {"category": "medication", "name": "Lisinopril", "value": "10mg", "unit": "QD", "confidence": 0.99}
            ]
        },
        {
            "id": "rep_006",
            "title": "Follow-Up Prescription & Endocrine Review",
            "fileName": "2024_05_10_Rx_Endocrine_Jenkins.pdf",
            "fileSize": 1200000,
            "fileType": "application/pdf",
            "category": "prescription",
            "hospitalName": "Metro Endocrinology Clinic",
            "doctorName": "Dr. Sarah Jenkins, MD",
            "reportDate": "2024-05-10",
            "confidenceScore": 0.98,
            "summary": "Ongoing therapy renewal for Diabetes and Hypertension. Refilled Metformin 500mg BID and Lisinopril 10mg QD for 90 days. Diet modification advised.",
            "rawText": "METRO ENDOCRINOLOGY RX ORDER\nPatient: Alex Vance\n1. Metformin 500mg PO BID #180, 2 refills\n2. Lisinopril 10mg PO QD #90, 2 refills\n3. Atorvastatin 10mg PO QD #90, 2 refills\nDietary counseling provided.",
            "entities": [
                {"category": "medication", "name": "Metformin", "value": "500mg", "unit": "BID", "confidence": 0.99},
                {"category": "medication", "name": "Lisinopril", "value": "10mg", "unit": "QD", "confidence": 0.99},
                {"category": "medication", "name": "Atorvastatin", "value": "10mg", "unit": "QD", "confidence": 0.99}
            ]
        },
        {
            "id": "rep_005",
            "title": "Comprehensive Metabolic Panel & HbA1c",
            "fileName": "2023_09_18_Quest_CMP_HbA1c.pdf",
            "fileSize": 1850000,
            "fileType": "application/pdf",
            "category": "blood_report",
            "hospitalName": "Quest Diagnostics",
            "doctorName": "Dr. Sarah Jenkins, MD",
            "reportDate": "2023-09-18",
            "confidenceScore": 0.99,
            "summary": "Diagnostic panel confirming Type 2 Diabetes onset. HbA1c elevated at 7.2%. Fasting plasma glucose at 142 mg/dL. Initiated on Metformin monotherapy.",
            "rawText": "QUEST DIAGNOSTICS LABORATORY REPORT\nPatient: Alex Vance | Date: 18-Sep-2023\nHbA1c: 7.2 % [CRITICAL HIGH] (Ref: 4.0-5.6)\nFasting Glucose: 142 mg/dL [H] (Ref: 70-99)\nDiagnosis: Type 2 Diabetes Mellitus (E11.9)\nPlan: Metformin 500mg BID with meals.",
            "entities": [
                {"category": "disease", "name": "Type 2 Diabetes Mellitus", "value": "E11.9", "confidence": 0.99},
                {"category": "lab_value", "name": "HbA1c", "value": "7.2", "unit": "%", "confidence": 0.99},
                {"category": "lab_value", "name": "Fasting Glucose", "value": "142", "unit": "mg/dL", "confidence": 0.99}
            ]
        },
        {
            "id": "rep_004",
            "title": "Clinical Encounter & Rx — Hypertension Initial",
            "fileName": "2023_11_04_Metro_Hypertension_Initial.pdf",
            "fileSize": 1150000,
            "fileType": "application/pdf",
            "category": "prescription",
            "hospitalName": "Metro General Hospital",
            "doctorName": "Dr. Sarah Jenkins, MD",
            "reportDate": "2023-11-04",
            "confidenceScore": 0.98,
            "summary": "Clinical consultation for stage 1 hypertension (office BP 145/92 mmHg). Commenced Lisinopril 10mg PO QD.",
            "rawText": "METRO GENERAL CLINICAL SUMMARY\nPatient: Alex Vance\nEncounter Date: 04-Nov-2023\nVitals: BP 145/92 mmHg, Pulse 76 bpm, BMI 25.8\nAssessment: Primary Hypertension (I10)\nPlan: Lisinopril 10mg QD, home BP monitoring.",
            "entities": [
                {"category": "disease", "name": "Essential Hypertension", "value": "I10", "confidence": 0.99},
                {"category": "medication", "name": "Lisinopril", "value": "10mg", "unit": "QD", "confidence": 0.99}
            ]
        },
        {
            "id": "rep_003",
            "title": "MRI Right Knee Joint",
            "fileName": "2022_08_10_StJude_MRI_Knee.pdf",
            "fileSize": 8500000,
            "fileType": "application/pdf",
            "category": "mri",
            "hospitalName": "St. Jude Diagnostic Imaging Center",
            "doctorName": "Dr. Emily Watson, MD",
            "reportDate": "2022-08-10",
            "confidenceScore": 0.96,
            "summary": "3.0T MRI Right Knee. Demonstrated Grade II degenerative signal in the posterior horn of the medial meniscus without displaced tear. ACL, PCL, and collateral ligaments intact.",
            "rawText": "ST. JUDE MRI IMAGING REPORT - 3.0T SCANNER\nPatient: Alex Vance\nTechnique: Sagittal, Coronal, Axial PD and T2 Fat-Suppressed Sequences\nFindings: Medial meniscus posterior horn demonstrates Grade II signal alteration without articular extension. Ligamentous structures intact.\nImpression: Non-surgical medial meniscus strain.",
            "entities": [
                {"category": "procedure", "name": "MRI Right Knee", "value": "Grade II Degenerative Signal", "confidence": 0.97},
                {"category": "disease", "name": "Medial Meniscus Strain", "value": "Non-surgical", "confidence": 0.95}
            ]
        },
        {
            "id": "rep_002",
            "title": "Lipid Profile & Glucose Screening",
            "fileName": "2021_06_12_Quest_Lipid_Profile.pdf",
            "fileSize": 1720000,
            "fileType": "application/pdf",
            "category": "blood_report",
            "hospitalName": "Quest Diagnostics",
            "doctorName": "Dr. Robert Chen, MD",
            "reportDate": "2021-06-12",
            "confidenceScore": 0.98,
            "summary": "Lipid screening showing elevated Total Cholesterol at 242 mg/dL and LDL at 158 mg/dL. Initiated on Atorvastatin 10mg QD with lifestyle modifications.",
            "rawText": "QUEST DIAGNOSTICS - LIPID & GLUCOSE PANEL\nTotal Cholesterol: 242 mg/dL [HIGH] (Ref: <200)\nLDL Cholesterol: 158 mg/dL [HIGH] (Ref: <100)\nHDL: 44 mg/dL\nFasting Glucose: 104 mg/dL [BORDERLINE]\nImpression: Hyperlipidemia. Rx: Atorvastatin 10mg daily.",
            "entities": [
                {"category": "disease", "name": "Hyperlipidemia", "value": "E78.5", "confidence": 0.98},
                {"category": "lab_value", "name": "Total Cholesterol", "value": "242", "unit": "mg/dL", "confidence": 0.99},
                {"category": "medication", "name": "Atorvastatin", "value": "10mg", "unit": "QD", "confidence": 0.99}
            ]
        },
        {
            "id": "rep_001",
            "title": "Inpatient Discharge Summary — Dengue Hemorrhagic",
            "fileName": "2019_10_14_Metro_Discharge_Dengue.pdf",
            "fileSize": 3200000,
            "fileType": "application/pdf",
            "category": "discharge_summary",
            "hospitalName": "Metro General Hospital",
            "doctorName": "Dr. Angela Ramos, MD",
            "reportDate": "2019-10-14",
            "confidenceScore": 0.97,
            "summary": "5-day hospital admission for acute Dengue Fever with thrombocytopenia (nadir platelets 48,000/uL). Successfully managed with IV hydration. Platelets rebounded to 165,000/uL on discharge.",
            "rawText": "METRO GENERAL INPATIENT SUMMARY\nPatient: Alex Vance | Admission: 10-Oct-2019 | Discharge: 14-Oct-2019\nFinal Dx: Acute Dengue Fever (A90)\nPlatelet nadir: 48 x10^3/uL. Discharge platelets: 165 x10^3/uL.\nCondition: Resolved. Discharged home with follow-up.",
            "entities": [
                {"category": "disease", "name": "Dengue Fever", "value": "A90", "confidence": 0.99},
                {"category": "procedure", "name": "Inpatient Hospitalization", "value": "5 Days", "confidence": 0.98}
            ]
        }
    ]

    for rep in reports_data:
        entities = rep.pop("entities")
        report_obj = MedicalReport(
            id=rep["id"],
            patient_id=patient.id,
            title=rep["title"],
            file_name=rep["fileName"],
            file_size=rep["fileSize"],
            file_type=rep["fileType"],
            category=rep["category"],
            hospital_name=rep["hospitalName"],
            doctor_name=rep.get("doctorName"),
            report_date=rep["reportDate"],
            confidence_score=rep["confidenceScore"],
            summary=rep.get("summary"),
            raw_text=rep.get("rawText")
        )
        db.add(report_obj)
        db.flush()

        for ent in entities:
            db.add(ExtractedEntity(
                report_id=report_obj.id,
                category=ent["category"],
                name=ent["name"],
                value=ent.get("value"),
                unit=ent.get("unit"),
                confidence=ent.get("confidence", 0.95)
            ))

    # 7. Create Timeline Events
    timeline_events = [
        TimelineEvent(
            id="ev_001",
            patient_id=patient.id,
            date="2026-06-15",
            year=2026,
            title="HbA1c Target Reached (6.7%)",
            description="Glycemic control stabilized. Marked improvement from diagnosis baseline of 7.2% in 2023 under continuous Metformin 500mg BID therapy.",
            event_type="lab_test",
            severity="low",
            doctor_name="Dr. Sarah Jenkins, MD",
            facility="Metro General Hospital",
            source_report_id="rep_008",
            source_report_title="Comprehensive Metabolic & Lipid Panel",
            connected_entities={"diseases": ["Type 2 Diabetes Mellitus"], "medications": ["Metformin HCl 500mg"], "labResults": ["HbA1c 6.7%"]}
        ),
        TimelineEvent(
            id="ev_002",
            patient_id=patient.id,
            date="2025-11-20",
            year=2025,
            title="Cardiovascular Screening Normal",
            description="2D Echocardiogram confirmed normal left ventricular ejection fraction (62%). Blood pressure controlled at 124/80 mmHg.",
            event_type="hospital_visit",
            severity="low",
            doctor_name="Dr. Marcus Thorne, MD",
            facility="St. Jude Heart & Vascular Center",
            source_report_id="rep_007",
            source_report_title="Cardiovascular Risk & Echo Evaluation",
            connected_entities={"diseases": ["Essential Hypertension"], "medications": ["Lisinopril 10mg"]}
        ),
        TimelineEvent(
            id="ev_003",
            patient_id=patient.id,
            date="2024-05-10",
            year=2024,
            title="Long-Term Prescription Refill",
            description="Endocrine follow-up confirmed stable metabolic parameters. 90-day supply of Metformin 500mg and Lisinopril 10mg renewed.",
            event_type="medication_start",
            severity="low",
            doctor_name="Dr. Sarah Jenkins, MD",
            facility="Metro Endocrinology Clinic",
            source_report_id="rep_006",
            source_report_title="Follow-Up Prescription & Endocrine Review",
            connected_entities={"medications": ["Metformin HCl", "Lisinopril", "Atorvastatin"]}
        ),
        TimelineEvent(
            id="ev_004",
            patient_id=patient.id,
            date="2023-11-04",
            year=2023,
            title="Essential Hypertension Diagnosed",
            description="Diagnosed with Primary Hypertension after consecutive elevated clinic readings (145/92 mmHg). Initiated on Lisinopril 10mg QD.",
            event_type="diagnosis",
            severity="medium",
            doctor_name="Dr. Sarah Jenkins, MD",
            facility="Metro General Hospital",
            source_report_id="rep_004",
            source_report_title="Clinical Encounter & Rx — Hypertension Initial",
            connected_entities={"diseases": ["Essential (Primary) Hypertension"], "medications": ["Lisinopril 10mg QD"]}
        ),
        TimelineEvent(
            id="ev_005",
            patient_id=patient.id,
            date="2023-09-18",
            year=2023,
            title="Type 2 Diabetes Diagnosed",
            description="Diagnostic lab results demonstrated HbA1c of 7.2% and fasting glucose of 142 mg/dL. Initiated on Metformin 500mg BID monotherapy.",
            event_type="diagnosis",
            severity="high",
            doctor_name="Dr. Sarah Jenkins, MD",
            facility="Quest Diagnostics",
            source_report_id="rep_005",
            source_report_title="Comprehensive Metabolic Panel & HbA1c",
            connected_entities={"diseases": ["Type 2 Diabetes Mellitus"], "medications": ["Metformin HCl 500mg BID"]}
        ),
        TimelineEvent(
            id="ev_006",
            patient_id=patient.id,
            date="2022-08-10",
            year=2022,
            title="Right Knee MRI — Meniscus Strain",
            description="Right knee MRI indicated Grade II posterior horn medial meniscus signal alteration without tear. Managed conservatively with physical therapy.",
            event_type="imaging",
            severity="medium",
            doctor_name="Dr. Emily Watson, MD",
            facility="St. Jude Diagnostic Imaging Center",
            source_report_id="rep_003",
            source_report_title="MRI Right Knee Joint",
            connected_entities={"diseases": ["Medial Meniscus Strain"]}
        ),
        TimelineEvent(
            id="ev_007",
            patient_id=patient.id,
            date="2021-06-12",
            year=2021,
            title="Hyperlipidemia Diagnosis & Statin Rx",
            description="Lipid panel showed elevated Total Cholesterol of 242 mg/dL. Prescribed Atorvastatin 10mg daily with dietary guidance.",
            event_type="diagnosis",
            severity="medium",
            doctor_name="Dr. Robert Chen, MD",
            facility="Quest Diagnostics",
            source_report_id="rep_002",
            source_report_title="Lipid Profile & Glucose Screening",
            connected_entities={"diseases": ["Hyperlipidemia"], "medications": ["Atorvastatin Calcium 10mg QD"]}
        ),
        TimelineEvent(
            id="ev_008",
            patient_id=patient.id,
            date="2019-10-14",
            year=2019,
            title="Dengue Fever Hospital Recovery",
            description="Discharged from Metro General Hospital following successful management of acute Dengue fever with thrombocytopenia.",
            event_type="hospital_visit",
            severity="high",
            doctor_name="Dr. Angela Ramos, MD",
            facility="Metro General Hospital",
            source_report_id="rep_001",
            source_report_title="Inpatient Discharge Summary — Dengue Hemorrhagic",
            connected_entities={"diseases": ["Dengue Fever with Thrombocytopenia"]}
        ),
    ]
    for ev in timeline_events:
        db.add(ev)

    # 8. Create Chat Conversation and Thread
    conversation = ChatConversation(
        id="th_1",
        patient_id=patient.id,
        title="Diabetes & Hypertension Medications"
    )
    db.add(conversation)
    db.flush()

    messages = [
        ChatMessage(
            id="msg_1",
            conversation_id=conversation.id,
            sender="user",
            text="What is my current dosage of Metformin, and when was it last verified?",
            timestamp="10:30 AM"
        ),
        ChatMessage(
            id="msg_2",
            conversation_id=conversation.id,
            sender="ai",
            text="Your current active prescription is Metformin 500mg taken twice daily with meals (BID). This was most recently verified on June 15, 2026 during your Comprehensive Metabolic & Lipid Panel at Metro General Hospital.",
            timestamp="10:31 AM",
            reasoning_type="fact",
            citations=[
                {
                    "reportId": "rep_008",
                    "reportTitle": "Comprehensive Metabolic & Lipid Panel",
                    "date": "2026-06-15",
                    "excerpt": "Metformin 500mg BID continued for Type 2 Diabetes management. HbA1c: 6.7%.",
                    "confidenceScore": 0.99
                }
            ]
        ),
    ]
    for m in messages:
        db.add(m)

    # 9. Create Doctor Summary
    summary = DoctorSummary(
        id="sum_001",
        patient_id=patient.id,
        patient_name="Alex Vance",
        age=38,
        gender="Male (38M)",
        summary_overview="38-year-old male with well-controlled Type 2 Diabetes (HbA1c 6.7%) and Essential Hypertension (BP 124/80 mmHg). No active cardiovascular symptoms or acute organ impairment. Compliant with pharmacotherapy (Metformin, Lisinopril, Atorvastatin). Known severe allergy to Penicillin.",
        current_diseases=[
            {"id": "dis_001", "name": "Type 2 Diabetes Mellitus", "icdCode": "E11.9", "notes": "HbA1c improved to 6.7% under Metformin 500mg BID."},
            {"id": "dis_002", "name": "Essential Hypertension", "icdCode": "I10", "notes": "BP stable at 124/80 on Lisinopril 10mg daily."},
            {"id": "dis_003", "name": "Hyperlipidemia", "icdCode": "E78.5", "notes": "Managed on Atorvastatin 10mg QD (Cholesterol: 198 mg/dL)."}
        ],
        past_diseases=[
            {"id": "dis_004", "name": "Vitamin D Deficiency", "icdCode": "E55.9", "notes": "Resolved in 2020."},
            {"id": "dis_005", "name": "Dengue Fever with Thrombocytopenia", "icdCode": "A90", "notes": "Resolved in 2019."}
        ],
        active_medications=[
            {"id": "med_001", "name": "Metformin HCl", "dosage": "500mg", "frequency": "BID with meals", "status": "active"},
            {"id": "med_002", "name": "Lisinopril", "dosage": "10mg", "frequency": "QD morning", "status": "active"},
            {"id": "med_003", "name": "Atorvastatin", "dosage": "10mg", "frequency": "QD bedtime", "status": "active"}
        ],
        known_allergies=[
            "Penicillin (Moderate Rash)",
            "Sulfa Drugs (Anaphylaxis Risk)"
        ],
        abnormal_labs=[
            {"id": "lab_001", "testName": "HbA1c", "value": "6.7", "unit": "%", "referenceRange": "4.0 - 5.6", "status": "high"},
            {"id": "lab_002", "testName": "Fasting Blood Glucose", "value": "128", "unit": "mg/dL", "referenceRange": "70 - 99", "status": "high"}
        ],
        risk_factors=[
            "Type 2 Diabetes Mellitus (E11.9)",
            "Family History of Early CAD",
            "Occasional Work-Related Sedentary Stress"
        ],
        recent_reports=[
            {"id": "rep_008", "title": "Comprehensive Metabolic & Lipid Panel", "reportDate": "2026-06-15", "hospitalName": "Metro General Hospital"},
            {"id": "rep_007", "title": "Cardiovascular Risk & Echo Evaluation", "reportDate": "2025-11-20", "hospitalName": "St. Jude Heart & Vascular Center"}
        ],
        timeline_highlights=[
            "2026-06-15: HbA1c improved to normal range (6.7%) under Metformin therapy.",
            "2025-11-20: Transthoracic Echo confirmed normal systolic function (LVEF 62%).",
            "2023-09-18: Type 2 Diabetes diagnosed (HbA1c 7.2%).",
            "2019-10-14: Inpatient recovery from acute Dengue fever."
        ],
        share_token="share_demo_98231"
    )
    db.add(summary)

    db.commit()
    db.refresh(demo_user)
    return demo_user
