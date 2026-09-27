from memory import hindsight_memory


def test_memory_is_customer_scoped_without_api_key(monkeypatch):
    monkeypatch.delenv("HINDSIGHT_API_KEY", raising=False)
    result = hindsight_memory.retain_interaction("C01", "Customer promised payment tomorrow")
    assert result["status"] == "local_only"
    assert result["customer_id"] == "C01"
    assert hindsight_memory.recall_customer_memory("C01", "payment") == []
