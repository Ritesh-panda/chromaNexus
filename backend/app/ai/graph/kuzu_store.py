import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

GRAPH_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "kuzu_graph"))


class KuzuGraphStore:
    """
    Embedded Local KùzuDB Graph Store for ChronaNexus.
    Runs 100% locally with zero server daemon, storing patient knowledge graph on disk.
    Supports OpenCypher querying for multi-hop graph retrieval with lazy initialization.
    """

    def __init__(self, db_path: str = GRAPH_DATA_DIR):
        self.db_path = db_path
        self._db = None
        self._conn = None
        self._initialized = False

    def _ensure_connected(self):
        if self._initialized:
            return self._conn
        
        try:
            import kuzu
            os.makedirs(self.db_path, exist_ok=True)
            self._db = kuzu.Database(self.db_path)
            self._conn = kuzu.Connection(self._db)
            self._init_schema()
            self._initialized = True
            logger.info(f"KùzuDB embedded graph engine connected at {self.db_path}")
        except Exception as e:
            logger.warning(f"KùzuDB lazy connection note: {e}")
            self._conn = None
            self._initialized = True
        return self._conn

    def _init_schema(self):
        """Initializes vertex and edge node tables if not existing."""
        if not self._conn:
            return
        
        try:
            self._conn.execute("CREATE NODE TABLE IF NOT EXISTS EntityNode(id STRING, label STRING, type STRING, cluster_id INT64, value STRING, PRIMARY KEY (id))")
            self._conn.execute("CREATE REL TABLE IF NOT EXISTS ClinicalRelation(FROM EntityNode TO EntityNode, relation STRING, label STRING, date STRING)")
        except Exception as e:
            logger.debug(f"KùzuDB schema init: {e}")

    def sync_patient_graph(self, patient_id: str, nodes: list, edges: list):
        """Persists the patient's updated knowledge graph into KùzuDB."""
        conn = self._ensure_connected()
        if not conn:
            return

        try:
            # Upsert nodes
            for n in nodes:
                safe_val = (getattr(n, "value", "") or "").replace("'", "''")
                safe_label = (getattr(n, "label", "") or "").replace("'", "''")
                query = f"""
                MERGE (e:EntityNode {{id: '{n.id}'}})
                ON MATCH SET e.label = '{safe_label}', e.type = '{n.type}', e.cluster_id = {n.cluster_id}, e.value = '{safe_val}'
                ON CREATE SET e.label = '{safe_label}', e.type = '{n.type}', e.cluster_id = {n.cluster_id}, e.value = '{safe_val}'
                """
                conn.execute(query)

            # Insert edges
            for e in edges:
                safe_rel = e.relation.replace("'", "''")
                safe_lbl = (getattr(e, "label", "") or "").replace("'", "''")
                safe_dt = (getattr(e, "date", "") or "").replace("'", "''")
                edge_q = f"""
                MATCH (s:EntityNode {{id: '{e.source}'}}), (t:EntityNode {{id: '{e.target}'}})
                CREATE (s)-[:ClinicalRelation {{relation: '{safe_rel}', label: '{safe_lbl}', date: '{safe_dt}'}}]->(t)
                """
                try:
                    conn.execute(edge_q)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"KùzuDB sync error: {e}")

    def query_subgraph(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Executes custom OpenCypher query against the embedded local graph."""
        conn = self._ensure_connected()
        if not conn:
            return []
        try:
            result = conn.execute(cypher_query)
            rows = []
            while result.has_next():
                rows.append(result.get_next())
            return rows
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return []


# Global singleton
kuzu_store = KuzuGraphStore()
