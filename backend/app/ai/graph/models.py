from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # 'condition' | 'medication' | 'lab_test' | 'procedure' | 'allergy' | 'document' | 'patient'
    cluster_id: int = 0
    cluster_name: str = "General Clinical"
    code: Optional[str] = None  # ICD-10, LOINC, or RxNorm code
    value: Optional[str] = None  # e.g., "7.2%", "138 mg/dL", "500 mg"
    status: Optional[str] = "active"  # 'active' | 'resolved' | 'abnormal' | 'normal'
    date: Optional[str] = None
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    page_number: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str  # 'DIAGNOSED_WITH' | 'PRESCRIBED' | 'TREATS' | 'MONITORS' | 'ALLERGIC_TO' | 'EVIDENCED_IN' | 'PERFORMED_AT'
    label: str
    date: Optional[str] = None
    confidence: float = 0.95
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    page_number: Optional[int] = None


class ClinicalCluster(BaseModel):
    id: int
    name: str
    category: str  # 'metabolic' | 'cardiovascular' | 'respiratory' | 'pharmacotherapy' | 'general'
    color: str
    node_count: int
    hub_entity: str
    summary: str
    node_ids: List[str] = Field(default_factory=list)


class PatientKnowledgeGraphResponse(BaseModel):
    patient_id: str
    patient_name: str
    total_nodes: int
    total_edges: int
    clusters: List[ClinicalCluster]
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    updated_at: str

