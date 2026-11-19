export interface GraphNode {
  id: string;
  label: string;
  type: 'condition' | 'medication' | 'lab_test' | 'procedure' | 'allergy' | 'document' | 'patient' | string;
  cluster_id: number;
  cluster_name: string;
  code?: string | null;
  value?: string | null;
  status?: string | null;
  date?: string | null;
  document_id?: string | null;
  document_title?: string | null;
  page_number?: number | null;
  details?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  label: string;
  date?: string | null;
  confidence?: number;
  document_id?: string | null;
  document_title?: string | null;
  page_number?: number | null;
}

export interface ClinicalCluster {
  id: number;
  name: string;
  category: string;
  color: string;
  node_count: number;
  hub_entity: string;
  summary: string;
  node_ids: string[];
}

export interface PatientKnowledgeGraphResponse {
  patient_id: string;
  patient_name: string;
  total_nodes: number;
  total_edges: number;
  clusters: ClinicalCluster[];
  nodes: GraphNode[];
  edges: GraphEdge[];
  updated_at: string;
}
