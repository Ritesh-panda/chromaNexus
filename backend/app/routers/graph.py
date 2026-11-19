import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.services.auth_service import get_current_patient
from backend.app.ai.graph.models import PatientKnowledgeGraphResponse, ClinicalCluster
from backend.app.ai.graph.graph_builder import build_patient_knowledge_graph
from backend.app.ai.graph.kuzu_store import kuzu_store
from backend.app.ai.graph.graph_rag import GraphRAGAugmenter
from backend.app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Knowledge Network & GraphRAG"])


@router.get("/patient", response_model=PatientKnowledgeGraphResponse)
def get_patient_graph(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns the comprehensive, grounded Patient Knowledge Network (Nodes, Edges, and Clinical Clusters)
    deterministically synthesized from verified medical documentation and laboratory records.
    """
    graph_resp = build_patient_knowledge_graph(db, current_patient)

    # Non-blocking embedded sync to local KùzuDB
    try:
        kuzu_store.sync_patient_graph(current_patient.id, graph_resp.nodes, graph_resp.edges)
    except Exception as e:
        logger.warning(f"KùzuDB non-blocking sync warning: {e}")

    log_audit_event(
        db=db,
        action="KNOWLEDGE_GRAPH_ACCESSED",
        outcome="SUCCESS",
        patient_id=current_patient.id,
        resource_type="knowledge_graph",
        details={
            "nodes_count": graph_resp.total_nodes,
            "edges_count": graph_resp.total_edges,
            "clusters_count": len(graph_resp.clusters)
        }
    )

    return graph_resp


@router.get("/clusters", response_model=List[ClinicalCluster])
def get_patient_clusters(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Returns detected clinical communities and topic clusters."""
    graph_resp = build_patient_knowledge_graph(db, current_patient)
    return graph_resp.clusters


@router.get("/facts", response_model=List[str])
def get_graph_facts(
    query: str = Query(..., description="Clinical inquiry or search phrase"),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Executes multi-hop graph traversal to extract verified relationship facts."""
    graph_resp = build_patient_knowledge_graph(db, current_patient)
    facts = GraphRAGAugmenter.extract_relevant_subgraph(query, graph_resp)
    return facts


@router.post("/sync", response_model=PatientKnowledgeGraphResponse)
def sync_patient_graph(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Forces recalculation of the patient graph and updates embedded storage."""
    graph_resp = build_patient_knowledge_graph(db, current_patient)
    kuzu_store.sync_patient_graph(current_patient.id, graph_resp.nodes, graph_resp.edges)
    return graph_resp

