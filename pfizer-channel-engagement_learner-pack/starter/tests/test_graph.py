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


def test_provider_failure_during_parse_routes_to_a_person(monkeypatch):
    def broken_llm():
        raise RuntimeError("provider down")

    monkeypatch.setattr(graph_module, "get_llm", broken_llm)

    result = graph_module.run_question("Please check the note from our stockist.")

    assert result["route"] == "NEEDS_PERSON"
    assert "RuntimeError" in result["checks"]["input_parse"]["reason"]


def test_provider_failure_during_explain_keeps_code_route_and_uses_fallback(monkeypatch):
    def broken_llm():
        raise RuntimeError("provider down")

    monkeypatch.setattr(graph_module, "get_llm", broken_llm)

    result = graph_module.run_question("Review CLM-2605-04488")

    assert result["route"] == "REJECT"
    assert result["explanation"].startswith("Route: REJECT.")
    assert "duplicate" in result["explanation"]


def test_explanation_cannot_present_the_route_as_an_action_already_taken(monkeypatch):
    monkeypatch.setattr(
        graph_module, "get_llm",
        lambda: ExplainOnlyLLM("The claim has been rejected. A duplicate was found. A person remains responsible for any final action."),
    )

    result = graph_module.run_question("Review CLM-2605-04488")

    assert result["route"] == "REJECT"
    assert "has been rejected" not in result["explanation"]
    assert result["explanation"].startswith("Route: REJECT.")


def test_repeat_of_pending_claim_is_sent_to_a_person(monkeypatch):
    # CLM-2609-04449 repeats pending CLM-2608-02222: same stockist, batch and 547 packs (held-out case).
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Review CLM-2609-04449")

    assert result["route"] == "NEEDS_PERSON"
    assert result["checks"]["duplicate"]["status"] == "review"
    assert result["checks"]["duplicate"]["matched_claims"] == ["CLM-2608-02222"]


def test_near_equal_repeat_of_credited_claim_is_sent_to_a_person(monkeypatch):
    # CLM-2507-04457 (370 packs) follows credited CLM-2505-00789 (371 packs) on the same stockist and batch.
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Review CLM-2507-04457")

    assert result["route"] == "NEEDS_PERSON"
    assert result["checks"]["duplicate"]["status"] == "review"
    assert "CLM-2505-00789" in result["checks"]["duplicate"]["matched_claims"]


def test_exact_repeat_of_credited_claim_is_still_rejected(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Review CLM-2605-04488")

    assert result["route"] == "REJECT"
    assert result["checks"]["duplicate"]["status"] == "fail"


class PastedFieldsLLM(ExplainOnlyLLM):
    """Return fixed extracted fields, as the structured-output model would."""

    def __init__(self, **fields):
        super().__init__()
        self.fields = fields

    def with_structured_output(self, schema):
        return SimpleNamespace(invoke=lambda _messages: schema(**self.fields))


def test_bare_claim_id_makes_no_extraction_call(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Review expiry claim CLM-2404-04177 and show its source evidence.")

    assert result["model_calls"] == 1  # explanation only
    assert "pasted_fields" not in result["checks"]


def test_pasted_value_that_differs_from_register_goes_to_a_person(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: PastedFieldsLLM(claim_value="Rs 64,400", qty="805"))

    result = graph_module.run_question(
        "From STK0024: claim CLM-2604-01611 for 805 packs, claim value Rs 64,400.")

    assert result["route"] == "NEEDS_PERSON"
    check = result["checks"]["pasted_fields"]
    assert check["status"] == "review"
    assert "claim_value: pasted Rs 64,400 vs register 57477.0" in check["reason"]
    assert result["model_calls"] == 2


def test_pasted_details_that_match_keep_the_code_route(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: PastedFieldsLLM(qty="38", expiry_claimed="30-09-2025"))

    result = graph_module.run_question("Claim CLM-2404-04177: 38 packs, expiry 30-09-2025.")

    assert result["route"] == "RECOMMEND_CREDIT"
    assert result["checks"]["pasted_fields"]["status"] == "pass"


def test_model_value_not_present_in_the_text_is_ignored(monkeypatch):
    # The model "finds" a value the user never typed; code drops it instead of acting on it.
    monkeypatch.setattr(graph_module, "get_llm", lambda: PastedFieldsLLM(claim_value="99999"))

    result = graph_module.run_question("Claim CLM-2404-04177, 38 packs.")

    assert "pasted_fields" not in result["checks"]
    assert result["route"] == "RECOMMEND_CREDIT"


def test_extraction_failure_on_pasted_details_goes_to_a_person(monkeypatch):
    class BrokenExtractor(ExplainOnlyLLM):
        def with_structured_output(self, schema):
            def fail(_messages):
                raise RuntimeError("provider down")
            return SimpleNamespace(invoke=fail)

    monkeypatch.setattr(graph_module, "get_llm", lambda: BrokenExtractor())

    result = graph_module.run_question("Claim CLM-2404-04177, 38 packs, value Rs 3,936.80.")

    assert result["route"] == "NEEDS_PERSON"
    assert result["checks"]["pasted_fields"]["status"] == "missing"
