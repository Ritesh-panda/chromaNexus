import re
import logging
from typing import List, Dict, Any, Optional, Set
from rank_bm25 import BM25Okapi
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import SearchResult

logger = logging.getLogger(__name__)


def clinical_bm25_tokenize(text: str) -> List[str]:
    """
    Clinical text tokenizer for BM25 keyword matching.
    Extracts alphanumeric tokens, medical abbreviations, dates, and dosages.
    """
    if not text:
        return []
    # Tokenize words, numbers, and hyphenated terms
    tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())
    # Filter pure single punctuation or empty tokens
    return [t for t in tokens if len(t) > 1 or t.isdigit()]


class BM25KeywordRetriever:
    """
    Production BM25 Okapi lexical retriever for ChronaNexus Phase 4.
    Matches exact keywords, clinical test names, drug dosages, and numbers.
    Enforces strict patient isolation via metadata filtering.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._chunks: List[DocumentChunk] = []
        self._corpus_tokens: List[List[str]] = []
        self._bm25: Optional[BM25Okapi] = None
        self._chunk_ids: Set[str] = set()

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Indexes a list of DocumentChunks into the BM25 lexical corpus.
        Prevents duplicate chunk entries by chunk_id.
        """
        if not chunks:
            return

        added = False
        for chunk in chunks:
            c_id = chunk.chunk_id or f"chk_{chunk.document_id}_{chunk.chunk_index}"
            if c_id not in self._chunk_ids:
                tokens = clinical_bm25_tokenize(chunk.text)
                self._chunks.append(chunk)
                self._corpus_tokens.append(tokens)
                self._chunk_ids.add(c_id)
                added = True

        if added and self._corpus_tokens:
            self._bm25 = BM25Okapi(self._corpus_tokens, k1=self.k1, b=self.b)

    def search(
        self,
        query: str,
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Executes BM25 keyword search for query against indexed corpus.
        Filters candidate matches by metadata (e.g. patient_id).
        Returns SearchResult objects with normalized scores.
        """
        if not query or not query.strip() or not self._bm25 or not self._chunks:
            return []

        query_tokens = clinical_bm25_tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Sort candidate indices by BM25 score descending
        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)
        results: List[SearchResult] = []

        # Find maximum positive score for min-max normalization
        pos_scores = [s for s in scores if s > 0]
        max_score = max(pos_scores) if pos_scores else 1.0

        for idx in ranked_indices:
            raw_score = float(scores[idx])
            if raw_score <= 0.0:
                # Small-corpus fallback: when corpus has few docs, BM25Okapi IDF can be <= 0 even on exact matches
                if any(t in self._corpus_tokens[idx] for t in query_tokens):
                    raw_score = 0.5
                else:
                    continue

            chunk = self._chunks[idx]

            # Enforce metadata filtering (e.g., patient isolation)
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if v is not None:
                        meta_val = chunk.metadata.get(k) if chunk.metadata else None
                        if meta_val != v:
                            match = False
                            break
                if not match:
                    continue

            norm_score = max(0.0, min(1.0, raw_score / max_score)) if max_score > 0 else 0.5
            results.append(SearchResult(chunk=chunk, score=round(norm_score, 4)))

            if len(results) >= top_k:
                break

        return results

    def clear(self) -> None:
        self._chunks.clear()
        self._corpus_tokens.clear()
        self._bm25 = None
        self._chunk_ids.clear()
