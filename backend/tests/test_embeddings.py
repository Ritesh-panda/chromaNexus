import pytest
from backend.app.ai.embeddings import (
    EmbeddingProvider,
    LocalLightweightEmbeddingProvider,
    OllamaEmbeddingProvider,
    get_embedding_provider
)


def test_embedding_provider_interface():
    provider = get_embedding_provider("local")
    assert isinstance(provider, EmbeddingProvider)
    assert provider.dimension() == 384


def test_ollama_embedding_provider_factory():
    provider = get_embedding_provider("ollama")
    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.dimension() == 384


def test_ollama_embedding_single_and_batch():
    provider = OllamaEmbeddingProvider(model_name="all-minilm")
    assert provider.dimension() == 384

    # Single text embedding test
    vec = provider.embed_text("Total cholesterol was 242 mg/dL on June 12, 2021.")
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)

    # Empty string check
    empty_vec = provider.embed_text("")
    assert len(empty_vec) == 384
    assert all(x == 0.0 for x in empty_vec)

    # Batch embedding check
    texts = [
        "Metformin 500mg BID for type 2 diabetes",
        "Lisinopril 10mg QD for hypertension",
        "Atorvastatin 10mg QD for hyperlipidemia"
    ]
    batch_vecs = provider.embed_texts(texts)
    assert len(batch_vecs) == 3
    for v in batch_vecs:
        assert len(v) == 384
        assert all(isinstance(x, float) for x in v)


def test_ollama_embedding_fallback_on_invalid_url():
    # Test graceful fallback when service is unreachable
    unreachable_provider = OllamaEmbeddingProvider(
        model_name="all-minilm",
        base_url="http://invalid-host-9999:11434",
        timeout=0.5
    )
    vec = unreachable_provider.embed_text("Clinical test sentence")
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)


def test_embed_text_single_and_batch_local():
    provider = LocalLightweightEmbeddingProvider(dim=128)
    assert provider.dimension() == 128

    vec = provider.embed_text("Total cholesterol was 242 mg/dL on June 12, 2021.")
    assert len(vec) == 128
    assert all(isinstance(x, float) for x in vec)

    empty_vec = provider.embed_text("")
    assert len(empty_vec) == 128
    assert all(x == 0.0 for x in empty_vec)

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

    sim12 = sum(a * b for a, b in zip(vec1, vec2))
    sim13 = sum(a * b for a, b in zip(vec1, vec3))

    assert sim12 > sim13
