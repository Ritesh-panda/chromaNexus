import pytest
from backend.app.ai.embeddings import (
    EmbeddingProvider,
    LocalLightweightEmbeddingProvider,
    get_embedding_provider
)


def test_embedding_provider_interface():
    provider = get_embedding_provider("local")
    assert isinstance(provider, EmbeddingProvider)
    assert provider.dimension() == 384


def test_embed_text_single_and_batch():
    provider = LocalLightweightEmbeddingProvider(dim=128)
    assert provider.dimension() == 128

    vec = provider.embed_text("Total cholesterol was 242 mg/dL on June 12, 2021.")
    assert len(vec) == 128
    assert all(isinstance(x, float) for x in vec)

    # Empty string check
    empty_vec = provider.embed_text("")
    assert len(empty_vec) == 128
    assert all(x == 0.0 for x in empty_vec)

    # Batch embedding check
    texts = [
        "Metformin 500mg BID",
        "Lisinopril 10mg QD",
        "Atorvastatin 10mg QD"
    ]
    batch_vecs = provider.embed_texts(texts)
    assert len(batch_vecs) == 3
    for v in batch_vecs:
        assert len(v) == 128


def test_embedding_similarity_consistency():
    provider = LocalLightweightEmbeddingProvider(dim=384)
    vec1 = provider.embed_text("Type 2 diabetes mellitus fasting glucose")
    vec2 = provider.embed_text("Type 2 diabetes blood sugar glucose")
    vec3 = provider.embed_text("Right knee MRI meniscus joint ligament")

    # Cosine dot product (normalized vectors)
    sim12 = sum(a * b for a, b in zip(vec1, vec2))
    sim13 = sum(a * b for a, b in zip(vec1, vec3))

    # Diabetes query should have higher semantic similarity to diabetes text than knee MRI
    assert sim12 > sim13
