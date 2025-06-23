import pytest
from app.services.chromadb_service import ChromaDBService

def test_add_and_query_embedding(monkeypatch):
    service = ChromaDBService(collection_name="test_collection")
    # Patch the collection to avoid real DB calls
    class FakeCollection:
        def add(self, ids, embeddings, metadatas): return None
        def query(self, query_embeddings, n_results): return {"ids": [["id"]], "distances": [[0.1]], "metadatas": [[{"foo": "bar"}]]}
    service.collection = FakeCollection()
    service.add_embedding("id", [0.1]*512, {"foo": "bar"})
    result = service.query_embedding([0.1]*512)
    assert "ids" in result

def test_add_embedding_error():
    service = ChromaDBService(collection_name="test_collection")
    class FakeCollection:
        def add(self, *a, **k): raise Exception("fail")
    service.collection = FakeCollection()
    with pytest.raises(Exception):
        service.add_embedding("id", [0.1]*512, {"foo": "bar"})

def test_query_embedding_error():
    service = ChromaDBService(collection_name="test_collection")
    class FakeCollection:
        def query(self, *a, **k): raise Exception("fail")
    service.collection = FakeCollection()
    with pytest.raises(Exception):
        service.query_embedding([0.1]*512)
