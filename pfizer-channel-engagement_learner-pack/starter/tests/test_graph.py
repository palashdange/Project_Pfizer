"""Tests for deterministic claim routing and the two constrained model tasks."""

from types import SimpleNamespace

import agent.graph as graph_module


class ExplainOnlyLLM:
    """Return a harmless explanation for the graph's explanation node."""

    def __init__(self, content="The route is ready. The checks are listed with their source evidence. A person remains responsible for any final action."):
        self.content = content

    def invoke(self, messages):
        return SimpleNamespace(content=self.content)


def test_claim_graph_covers_recommend_reject_needs_person_and_not_found(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    recommend = graph_module.run_question("Review CLM-2404-04177")
    reject = graph_module.run_question("Review CLM-2605-04488")
    needs_person = graph_module.run_question("Review CLM-2404-04181")
    not_found = graph_module.run_question("Review CLM-0000-00000")

    assert recommend["route"] == "RECOMMEND_CREDIT"
    assert set(recommend["checks"]) == {
        "window", "quantity", "duplicate", "invoice_ref", "batch_expiry", "value"
    }
    assert reject["route"] == "REJECT"
    assert reject["checks"]["duplicate"]["status"] == "fail"
    assert needs_person["route"] == "NEEDS_PERSON"
    assert needs_person["checks"]["invoice_ref"]["status"] == "missing"
    assert not_found["route"] == "NOT_FOUND"
    assert not_found["explanation"] == ""
    assert not_found["model_calls"] == 0


def test_email_prompt_injection_is_untrusted_and_cannot_return_approval(monkeypatch):
    monkeypatch.setattr(
        graph_module, "get_llm",
        lambda: ExplainOnlyLLM("APPROVED. The credit should be issued immediately. All checks passed."),
    )

    result = graph_module.run_question("Inspect email EML-017")

    assert result["route"] == "NEEDS_PERSON"
    assert result["evidence"][0]["body_trust_status"] == "untrusted_correspondence"
    assert "APPROVED" not in result["explanation"]
    assert "NEEDS_PERSON" in result["explanation"]


def test_free_text_uses_structured_extraction_and_counts_both_model_calls(monkeypatch):
    class ExtractingLLM(ExplainOnlyLLM):
        def with_structured_output(self, schema):
            assert schema is graph_module.ClaimExtraction
            return SimpleNamespace(invoke=lambda messages: schema(claim_no="CLM-2404-04177"))

    monkeypatch.setattr(graph_module, "get_llm", lambda: ExtractingLLM())

    result = graph_module.run_question("Please review this claim from my notes")

    assert result["route"] == "RECOMMEND_CREDIT"
    assert result["model_calls"] == 2


def test_model_explanation_cannot_add_numbers_not_present_in_checks(monkeypatch):
    monkeypatch.setattr(
        graph_module, "get_llm",
        lambda: ExplainOnlyLLM("The route is ready. It took 99 days. A person remains responsible for any final action."),
    )

    result = graph_module.run_question("Review CLM-2404-04177")

    assert "99 days" not in result["explanation"]
    assert result["route"] == "RECOMMEND_CREDIT"


def test_claim_value_mismatch_is_sent_to_a_person(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())
    original_get_claim = graph_module.data.get_claim

    def claim_with_mismatched_value(claim_no):
        claim = dict(original_get_claim(claim_no))
        claim["claim_value_inr"] = "1.00"
        return claim

    monkeypatch.setattr(graph_module.data, "get_claim", claim_with_mismatched_value)

    result = graph_module.run_question("Review CLM-2404-04177")

    assert result["route"] == "NEEDS_PERSON"
    assert result["checks"]["value"]["status"] == "fail"
    assert "Send the mismatch to a person" in result["checks"]["value"]["reason"]


def test_unidentifiable_free_text_is_routed_to_a_person(monkeypatch):
    class EmptyExtractorLLM(ExplainOnlyLLM):
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda _messages: schema())

    monkeypatch.setattr(graph_module, "get_llm", lambda: EmptyExtractorLLM())

    result = graph_module.run_question("Please check this note, but no claim ID is included.")

    assert result["route"] == "NEEDS_PERSON"
    assert result["checks"]["input_parse"]["status"] == "missing"
    assert result["model_calls"] == 2
