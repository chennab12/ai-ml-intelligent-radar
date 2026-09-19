from radar.engine import classify, score_item, load_demo, trends, ideas


def test_classify():
    assert classify("vLLM inference latency benchmark") == "Inference"
    assert classify("agentic tool use and MCP") == "Agentic AI"


def test_score_bounds():
    assert 0 <= score_item("Model release", "inference benchmark GPU", 2, 1) <= 100


def test_demo_pipeline():
    df = load_demo()
    assert not df.empty
    assert {"title", "topic", "score", "tpm_takeaway"}.issubset(df.columns)
    assert not trends(df).empty
    assert len(ideas(df)) >= 6

