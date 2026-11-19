import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication, LabResult, ExtractedEntity
from backend.app.models.allergy import Allergy
from backend.app.ai.graph.models import GraphNode, GraphEdge, PatientKnowledgeGraphResponse
from backend.app.ai.graph.clustering import compute_clinical_clusters

logger = logging.getLogger(__name__)

DISALLOWED_DISEASES = {"unknown", "none", "n/a", "na", "unspecified", "nil", "no", "not applicable"}
DISALLOWED_ALLERGENS = {"unknown", "none", "n/a", "na", "nil", "no", "not applicable", "nkda", "no known drug allergies", "no known allergies"}

# Clinical Treatment & Monitoring Rules
TREATMENT_MAPPINGS = {
    "metformin": ["diabetes", "type 2 diabetes", "glycemic", "glucose"],
    "insulin": ["diabetes", "type 1 diabetes", "type 2 diabetes"],
    "glimepiride": ["diabetes", "type 2 diabetes"],
    "amlodipine": ["hypertension", "high blood pressure", "blood pressure"],
    "lisinopril": ["hypertension", "heart failure"],
    "atorvastatin": ["hyperlipidemia", "cholesterol", "dyslipidemia"],
    "levothyroxine": ["hypothyroidism", "thyroid"],
    "omeprazole": ["gerd", "acid reflux", "gastritis"],
    "amoxicillin": ["infection", "bronchitis", "pneumonia"],
    "paracetamol": ["pain", "fever"],
}

MONITORING_MAPPINGS = {
    "hba1c": ["diabetes", "type 2 diabetes"],
    "glucose": ["diabetes", "type 2 diabetes"],
    "blood sugar": ["diabetes", "type 2 diabetes"],
    "cholesterol": ["hyperlipidemia", "cardiovascular"],
    "creatinine": ["kidney", "renal", "hypertension"],
    "blood pressure": ["hypertension"],
}


def make_node_id(prefix: str, identifier: str) -> str:
    clean = identifier.strip().lower()
    h = hashlib.sha256(clean.encode()).hexdigest()[:10]
    return f"{prefix}_{h}"


def build_patient_knowledge_graph(db: Session, patient: Patient) -> PatientKnowledgeGraphResponse:
    """
    Constructs a rich, grounded Knowledge Graph for the authenticated patient directly
    from their verified primary medical records and clinical extractions.
    """
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []

    patient_name = patient.user.name if (patient.user and patient.user.name) else "Patient"
    patient_node_id = f"patient_{patient.id[:8]}"

    # 1. Patient Central Node
    nodes[patient_node_id] = GraphNode(
        id=patient_node_id,
        label=patient_name,
        type="patient",
        code=None,
        value=f"DOB: {patient.date_of_birth or 'N/A'}",
        status="active",
        details={
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "primaryCarePhysician": patient.primary_care_physician
        }
    )

    # 2. Medical Reports (Document Vault Nodes)
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).order_by(MedicalReport.report_date.desc()).all()
    reports_map = {r.id: r for r in reports}

    for r in reports:
        doc_node_id = f"doc_{r.id[:8]}"
        nodes[doc_node_id] = GraphNode(
            id=doc_node_id,
            label=r.title,
            type="document",
            date=r.report_date,
            document_id=r.id,
            document_title=r.title,
            value=r.category,
            details={"hospital": r.hospital_name, "category": r.category, "file_name": r.file_name}
        )
        # Edge: Patient owns Document
        edges.append(GraphEdge(
            id=f"e_{patient_node_id}_{doc_node_id}",
            source=patient_node_id,
            target=doc_node_id,
            relation="DOCUMENT_VAULT",
            label="filed in vault",
            date=r.report_date,
            document_id=r.id,
            document_title=r.title
        ))

    # 3. Diagnoses / Conditions
    diseases = db.query(Disease).filter(Disease.patient_id == patient.id).all()
    condition_nodes_map: Dict[str, str] = {}  # clean_name -> node_id

    for d in diseases:
        name_clean = (d.name or "").strip()
        if not name_clean or name_clean.lower() in DISALLOWED_DISEASES:
            continue

        cond_node_id = make_node_id("cond", name_clean)
        rep = reports_map.get(d.source_report_id)

        if cond_node_id not in nodes:
            nodes[cond_node_id] = GraphNode(
                id=cond_node_id,
                label=name_clean,
                type="condition",
                code=d.icd_code,
                status=d.status or "active",
                date=d.diagnosed_date,
                document_id=d.source_report_id,
                document_title=rep.title if rep else None,
                page_number=d.source_page_number,
                details={"notes": d.notes, "hospital": rep.hospital_name if rep else None}
            )
            condition_nodes_map[name_clean.lower()] = cond_node_id

            # Edge: Patient -> DIAGNOSED_WITH -> Condition
            edges.append(GraphEdge(
                id=f"e_{patient_node_id}_{cond_node_id}",
                source=patient_node_id,
                target=cond_node_id,
                relation="DIAGNOSED_WITH",
                label="diagnosed with",
                date=d.diagnosed_date,
                document_id=d.source_report_id,
                document_title=rep.title if rep else None,
                page_number=d.source_page_number
            ))

        # Edge: Condition -> EVIDENCED_IN -> Document
        if rep:
            doc_node_id = f"doc_{rep.id[:8]}"
            if doc_node_id in nodes:
                edges.append(GraphEdge(
                    id=f"e_{cond_node_id}_{doc_node_id}",
                    source=cond_node_id,
                    target=doc_node_id,
                    relation="EVIDENCED_IN",
                    label=f"evidenced in p.{d.source_page_number or 1}",
                    date=d.diagnosed_date or rep.report_date,
                    document_id=rep.id,
                    document_title=rep.title,
                    page_number=d.source_page_number
                ))

    # 4. Medications & Pharmacotherapy
    meds = db.query(Medication).filter(Medication.patient_id == patient.id).all()
    for m in meds:
        m_name = (m.name or "").strip()
        if not m_name:
            continue

        med_node_id = make_node_id("med", m_name)
        rep = reports_map.get(m.source_report_id)

        if med_node_id not in nodes:
            nodes[med_node_id] = GraphNode(
                id=med_node_id,
                label=m_name,
                type="medication",
                value=m.dosage,
                status=m.status or "active",
                date=m.start_date,
                document_id=m.source_report_id,
                document_title=rep.title if rep else None,
                page_number=m.source_page_number,
                details={
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "route": m.route,
                    "prescriber": m.prescribing_doctor
                }
            )

            # Edge: Patient -> PRESCRIBED -> Medication
            edges.append(GraphEdge(
                id=f"e_{patient_node_id}_{med_node_id}",
                source=patient_node_id,
                target=med_node_id,
                relation="PRESCRIBED",
                label=f"prescribed ({m.dosage or 'active'})",
                date=m.start_date,
                document_id=m.source_report_id,
                document_title=rep.title if rep else None,
                page_number=m.source_page_number
            ))

        # Check if Medication TREATS any Condition in graph
        m_lower = m_name.lower()
        for drug_key, targets in TREATMENT_MAPPINGS.items():
            if drug_key in m_lower:
                for cond_name, c_node_id in condition_nodes_map.items():
                    if any(t in cond_name for t in targets):
                        edges.append(GraphEdge(
                            id=f"e_{med_node_id}_{c_node_id}",
                            source=med_node_id,
                            target=c_node_id,
                            relation="TREATS",
                            label="therapeutically treats",
                            date=m.start_date,
                            document_id=m.source_report_id,
                            document_title=rep.title if rep else None
                        ))

        # Edge: Medication -> EVIDENCED_IN -> Document
        if rep:
            doc_node_id = f"doc_{rep.id[:8]}"
            if doc_node_id in nodes:
                edges.append(GraphEdge(
                    id=f"e_{med_node_id}_{doc_node_id}",
                    source=med_node_id,
                    target=doc_node_id,
                    relation="EVIDENCED_IN",
                    label=f"documented on p.{m.source_page_number or 1}",
                    date=m.start_date or rep.report_date,
                    document_id=rep.id,
                    document_title=rep.title,
                    page_number=m.source_page_number
                ))

    # 5. Lab Results & Biomarkers
    labs = db.query(LabResult).filter(LabResult.patient_id == patient.id).order_by(LabResult.test_date.desc()).all()
    for lab in labs:
        test_name = (lab.test_name or "").strip()
        if not test_name:
            continue

        lab_node_id = make_node_id("lab", f"{test_name}_{lab.test_date or ''}")
        rep = reports_map.get(lab.source_report_id)

        val_str = str(lab.value or "").strip()
        unit_str = str(lab.unit or "").strip()
        if unit_str and val_str.lower().endswith(unit_str.lower()):
            clean_val = val_str[:-len(unit_str)].strip()
            display_val = f"{clean_val} {unit_str}".strip()
        elif unit_str:
            display_val = f"{val_str} {unit_str}".strip()
        else:
            display_val = val_str
        nodes[lab_node_id] = GraphNode(
            id=lab_node_id,
            label=test_name,
            type="lab_test",
            value=display_val,
            code=lab.loinc_code,
            status=lab.status or "normal",
            date=lab.test_date,
            document_id=lab.source_report_id,
            document_title=rep.title if rep else None,
            page_number=lab.source_page_number,
            details={
                "value": lab.value,
                "unit": lab.unit,
                "reference_range": lab.reference_range,
                "status": lab.status
            }
        )

        # Edge: Patient -> TESTED -> LabTest
        edges.append(GraphEdge(
            id=f"e_{patient_node_id}_{lab_node_id}",
            source=patient_node_id,
            target=lab_node_id,
            relation="MEASURED",
            label=f"measured {display_val}",
            date=lab.test_date,
            document_id=lab.source_report_id,
            document_title=rep.title if rep else None,
            page_number=lab.source_page_number
        ))

        # Check if Lab MONITORS any Condition in graph
        l_lower = test_name.lower()
        for lab_key, targets in MONITORING_MAPPINGS.items():
            if lab_key in l_lower:
                for cond_name, c_node_id in condition_nodes_map.items():
                    if any(t in cond_name for t in targets):
                        edges.append(GraphEdge(
                            id=f"e_{lab_node_id}_{c_node_id}",
                            source=lab_node_id,
                            target=c_node_id,
                            relation="MONITORS",
                            label=f"monitors ({display_val})",
                            date=lab.test_date,
                            document_id=lab.source_report_id,
                            document_title=rep.title if rep else None
                        ))

        # Edge: Lab -> EVIDENCED_IN -> Document
        if rep:
            doc_node_id = f"doc_{rep.id[:8]}"
            if doc_node_id in nodes:
                edges.append(GraphEdge(
                    id=f"e_{lab_node_id}_{doc_node_id}",
                    source=lab_node_id,
                    target=doc_node_id,
                    relation="EVIDENCED_IN",
                    label=f"lab panel p.{lab.source_page_number or 1}",
                    date=lab.test_date or rep.report_date,
                    document_id=rep.id,
                    document_title=rep.title,
                    page_number=lab.source_page_number
                ))

    # 6. Allergies & Adverse Reactions
    allergies = db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
    for a in allergies:
        alg_name = (a.allergen or "").strip()
        if not alg_name or alg_name.lower() in DISALLOWED_ALLERGENS:
            continue

        alg_node_id = make_node_id("alg", alg_name)
        rep = reports_map.get(a.source_report_id)

        if alg_node_id not in nodes:
            nodes[alg_node_id] = GraphNode(
                id=alg_node_id,
                label=alg_name,
                type="allergy",
                value=a.severity or "moderate",
                status="active",
                document_id=a.source_report_id,
                document_title=rep.title if rep else None,
                page_number=a.source_page_number,
                details={"reaction": a.reaction, "severity": a.severity}
            )

            # Edge: Patient -> ALLERGIC_TO -> Allergy
            edges.append(GraphEdge(
                id=f"e_{patient_node_id}_{alg_node_id}",
                source=patient_node_id,
                target=alg_node_id,
                relation="ALLERGIC_TO",
                label=f"allergic reaction ({a.severity or 'moderate'})",
                date=None,
                document_id=a.source_report_id,
                document_title=rep.title if rep else None
            ))

    # 7. Cluster communities using NetworkX Louvain / Greedy Modularity
    nodes_list = list(nodes.values())
    clustered_nodes, clusters = compute_clinical_clusters(nodes_list, edges)

    # 8. Deduplicate edges by unique ID
    seen_edge_ids = set()
    deduped_edges: List[GraphEdge] = []
    for e in edges:
        if e.id not in seen_edge_ids:
            seen_edge_ids.add(e.id)
            deduped_edges.append(e)

    return PatientKnowledgeGraphResponse(
        patient_id=patient.id,
        patient_name=patient_name,
        total_nodes=len(clustered_nodes),
        total_edges=len(deduped_edges),
        clusters=clusters,
        nodes=clustered_nodes,
        edges=deduped_edges,
        updated_at=datetime.now(timezone.utc).isoformat()
    )
