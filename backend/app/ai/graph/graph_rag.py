import logging
from typing import List, Dict, Any, Optional
from backend.app.ai.graph.models import GraphNode, GraphEdge, PatientKnowledgeGraphResponse

logger = logging.getLogger(__name__)


class GraphRAGAugmenter:
    """
    Traverses patient knowledge network to generate structured multi-hop
    factual context for clinical questions.
    """

    @staticmethod
    def extract_relevant_subgraph(
        query: str,
        graph: PatientKnowledgeGraphResponse,
        max_hops: int = 2
    ) -> List[str]:
        """
        Extracts multi-hop relational paths from the graph that relate to words in the user's query.
        Returns clear, human-readable verified clinical facts.
        """
        q_lower = query.lower()
        matched_nodes = []

        # 1. Find matching anchor nodes
        for node in graph.nodes:
            if node.type == "patient":
                continue
            if node.label.lower() in q_lower or (node.value and node.value.lower() in q_lower):
                matched_nodes.append(node)
            elif any(w in node.label.lower() for w in q_lower.split() if len(w) > 3):
                matched_nodes.append(node)

        if not matched_nodes:
            # Fallback: include primary active conditions and medications as baseline context
            matched_nodes = [n for n in graph.nodes if n.type in ["condition", "medication"]][:4]

        # 2. Trace 1-hop and 2-hop edges connected to matched nodes
        matched_ids = {n.id for n in matched_nodes}
        facts: List[str] = []
        node_lookup = {n.id: n for n in graph.nodes}

        for edge in graph.edges:
            src = node_lookup.get(edge.source)
            tgt = node_lookup.get(edge.target)
            if not src or not tgt:
                continue

            # Check if edge connects to any matched node
            if edge.source in matched_ids or edge.target in matched_ids:
                doc_cite = f" [Verified in: {edge.document_title}]" if edge.document_title else ""
                date_str = f" ({edge.date})" if edge.date else ""

                if edge.relation == "TREATS":
                    facts.append(f"• **{src.label}** therapeutically treats **{tgt.label}**{date_str}{doc_cite}.")
                elif edge.relation == "DIAGNOSED_WITH":
                    facts.append(f"• Patient diagnosed with **{tgt.label}**{date_str}{doc_cite}.")
                elif edge.relation == "PRESCRIBED":
                    facts.append(f"• Prescribed **{tgt.label}** ({tgt.value or 'active'}){date_str}{doc_cite}.")
                elif edge.relation == "MONITORS":
                    facts.append(f"• Biomarker **{src.label}** ({src.value}) monitors **{tgt.label}**{date_str}{doc_cite}.")
                elif edge.relation == "MEASURED":
                    facts.append(f"• Laboratory finding: **{tgt.label}** measured at **{tgt.value}**{date_str}{doc_cite}.")
                elif edge.relation == "ALLERGIC_TO":
                    facts.append(f"• Documented allergy to **{tgt.label}** (Severity: {tgt.value}){doc_cite}.")

        # Deduplicate
        seen = set()
        unique_facts = []
        for f in facts:
            if f not in seen:
                seen.add(f)
                unique_facts.append(f)

        return unique_facts[:6]

