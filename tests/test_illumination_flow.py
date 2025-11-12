from oracle_illuminating.workflows import illumination_cycle


def test_illumination_cycle_produces_recursive_question() -> None:
    result = illumination_cycle({"summary": "test cycle"})

    assert "insights" in result and len(result["insights"]) > 0
    assert "guardrails" in result and len(result["guardrails"]) > 0

    recursive = result.get("recursive")
    assert recursive is not None
    assert recursive["status"] in {"pass", "review"}
    assert recursive["question"]

