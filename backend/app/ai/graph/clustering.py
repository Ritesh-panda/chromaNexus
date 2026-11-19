import logging
from typing import List, Dict, Any, Tuple
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from backend.app.ai.graph.models import GraphNode, GraphEdge, ClinicalCluster

logger = logging.getLogger(__name__)

# Colors for clinical clusters
CLUSTER_COLORS = [
    "#10B981",  # Emerald (Metabolic / Glycemic)
    "#3B82F6",  # Blue (Pharmacotherapy / Treatment)
    "#F43F5E",  # Rose (Cardiovascular / Conditions)
    "#8B5CF6",  # Violet (Diagnostic Imaging & Procedures)
    "#F59E0B",  # Amber (Laboratory & Pathology)
    "#06B6D4",  # Cyan (Preventive / General)
]

CLUSTER_CATEGORY_KEYWORDS = {
    "metabolic": ["diabetes", "glucose", "hba1c", "metformin", "sugar", "insulin", "glycemic", "lipid", "cholesterol"],
    "cardiovascular": ["hypertension", "blood pressure", "systolic", "diastolic", "cardio", "amlodipine", "heart", "artery"],
    "respiratory": ["x-ray", "chest", "lung", "cough", "infiltrate", "pleural", "pulmonary", "respiratory"],
    "pharmacotherapy": ["prescribed", "tablet", "capsule", "dosage", "mg", "rx", "daily", "medication"],
}


def detect_cluster_theme(nodes: List[GraphNode]) -> Tuple[str, str]:
    """Detects clinical theme and human-friendly name for a group of connected nodes."""
    all_text = " ".join([f"{n.label} {n.code or ''} {n.type}" for n in nodes]).lower()
    
    scores = {"metabolic": 0, "cardiovascular": 0, "respiratory": 0, "pharmacotherapy": 0}
    for category, keywords in CLUSTER_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                scores[category] += 1
                
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return "general", "General Health & Preventive Care"
        
    names = {
        "metabolic": "Metabolic & Glycemic Health",
        "cardiovascular": "Cardiovascular & Hemodynamics",
        "respiratory": "Pulmonary & Diagnostic Imaging",
        "pharmacotherapy": "Active Pharmacotherapy & Regimen"
    }
    return best_cat, names[best_cat]


def compute_clinical_clusters(nodes: List[GraphNode], edges: List[GraphEdge]) -> Tuple[List[GraphNode], List[ClinicalCluster]]:
    """
    Partitions the patient's knowledge graph into clinical communities using networkx.
    Assigns cluster_id and cluster_name to each node and returns the cluster list.
    """
    if not nodes:
        return [], []

    # Build undirected NetworkX graph
    G = nx.Graph()
    for n in nodes:
        G.add_node(n.id, node_obj=n)

    for e in edges:
        # Don't create clustering edges to generic document or patient nodes so clinical entities cluster cleanly
        src = next((n for n in nodes if n.id == e.source), None)
        tgt = next((n for n in nodes if n.id == e.target), None)
        if src and tgt:
            # Documents & Patient have lower clustering weight
            weight = 0.5 if (src.type in ["document", "patient"] or tgt.type in ["document", "patient"]) else 1.5
            G.add_edge(e.source, e.target, weight=weight)

    # Detect communities
    try:
        communities = list(greedy_modularity_communities(G, weight="weight"))
    except Exception as exc:
        logger.warning(f"Community detection fallback to connected components: {exc}")
        communities = list(nx.connected_components(G))

    # Calculate degree centrality for hub discovery
    centrality = nx.degree_centrality(G)

    clusters: List[ClinicalCluster] = []
    node_id_to_cluster: Dict[str, Tuple[int, str]] = {}

    for cluster_idx, comm in enumerate(communities):
        comm_nodes = [G.nodes[n_id]["node_obj"] for n_id in comm if "node_obj" in G.nodes[n_id]]
        if not comm_nodes:
            continue

        # Find hub entity (node with highest degree centrality in this cluster)
        hub_node_id = max(comm, key=lambda nid: centrality.get(nid, 0))
        hub_node = G.nodes[hub_node_id].get("node_obj")
        hub_name = hub_node.label if hub_node else "Clinical Anchor"

        cat_key, cluster_name = detect_cluster_theme(comm_nodes)
        color = CLUSTER_COLORS[cluster_idx % len(CLUSTER_COLORS)]

        # Human summary of cluster
        conditions = [n.label for n in comm_nodes if n.type == "condition"]
        meds = [n.label for n in comm_nodes if n.type == "medication"]
        labs = [n.label for n in comm_nodes if n.type == "lab_test"]

        summary_parts = []
        if conditions:
            summary_parts.append(f"Grounded around {', '.join(conditions[:2])}")
        if meds:
            summary_parts.append(f"managed via {', '.join(meds[:2])}")
        if labs:
            summary_parts.append(f"monitored with {', '.join(labs[:2])}")

        cluster_summary = ". ".join(summary_parts) + "." if summary_parts else f"Coordinated cluster of {len(comm_nodes)} clinical observations."

        cluster_obj = ClinicalCluster(
            id=cluster_idx + 1,
            name=cluster_name,
            category=cat_key,
            color=color,
            node_count=len(comm_nodes),
            hub_entity=hub_name,
            summary=cluster_summary,
            node_ids=[n.id for n in comm_nodes]
        )
        clusters.append(cluster_obj)

        for n in comm_nodes:
            node_id_to_cluster[n.id] = (cluster_obj.id, cluster_obj.name)

    # Assign cluster metadata to nodes
    updated_nodes: List[GraphNode] = []
    for n in nodes:
        c_info = node_id_to_cluster.get(n.id)
        if c_info:
            n.cluster_id = c_info[0]
            n.cluster_name = c_info[1]
        updated_nodes.append(n)

    return updated_nodes, clusters

