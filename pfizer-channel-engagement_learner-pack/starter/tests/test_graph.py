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


def test_scheme_code_routes_to_scheme_review_and_cap_matches_sizing(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Review scheme QS-FY25Q3-A")

    assert result["route"] == "SCHEME_NEEDS_REVIEW"
    assert set(result["checks"]) == {"cap", "eligibility", "validity_window", "sku_list", "free_ratio", "stock_norm"}
    # Same figure as discovery/sizing.py's quarter table (FY25 Q3 FOC 4.95% of primary sales).
    assert result["checks"]["cap"]["foc_pct"] == "4.95"
    assert result["checks"]["cap"]["status"] == "fail"
    assert result["checks"]["stock_norm"]["status"] == "missing"
    assert result["model_calls"] == 1  # explanation only


def test_quarter_within_cap_still_reports_eligibility(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("How did FY25 Q1 schemes do?")

    assert result["checks"]["cap"]["status"] == "pass"
    assert result["checks"]["cap"]["foc_pct"] == "1.18"
    assert int(result["checks"]["eligibility"]["lines_checked"]) > 0


def test_unknown_scheme_or_quarter_is_not_found_without_a_model_call(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    for text in ("QS-FY23Q1-A", "QS-FY25Q1-B", "FY29 Q1"):
        result = graph_module.run_question(text)
        assert result["route"] == "NOT_FOUND", text
        assert result["model_calls"] == 0
        assert "FY27 Q2" in result["evidence"][0]["available_quarters"]


def test_claim_id_takes_priority_over_a_quarter_mention(monkeypatch):
    # The extra digits make the input "pasted details"; an extractor that finds no fields keeps the claim route.
    monkeypatch.setattr(graph_module, "get_llm", lambda: PastedFieldsLLM())

    result = graph_module.run_question("Review CLM-2404-04177 from FY25 Q1")

    assert result["route"] == "RECOMMEND_CREDIT"
    assert "cap" not in result["checks"] and "window" in result["checks"]


def test_stock_review_latest_snapshot_flags_kolkata_and_lucknow(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Stock review")

    assert result["route"] == "STOCK_NEEDS_ACTION"
    evidence = result["evidence"][0]
    assert evidence["snapshot"] == "30-09-2026"
    by_cfa = {row["cfa"]: row for row in evidence["by_cfa"]}
    assert by_cfa["CF-N02"]["out_of_stock"] == 23  # Lucknow: 23 of 36 SKUs empty
    assert result["checks"]["fefo_signal"]["flagged"] == ["CF-E01"]
    assert result["checks"]["expiry_block"]["status"] == "pass"  # no write-off risk at this snapshot
    nearest = result["checks"]["expiry_block"]["nearest"]
    assert nearest["days_to_block"] > 0 and nearest["source"].startswith("cnf_stock_snapshot.csv:")


def test_stock_batch_past_its_60_percent_point_is_counted_in_full():
    # G2550105 (PFL1501, CF-E01): made 15-07-2025, expires 30-06-2028 = 1,081 days of life.
    # 60% must remain at dispatch, so it had to ship by 20-09-2026, before the 30-09-2026 snapshot.
    from agent.stock import review_stock

    result = review_stock("30-09-2026")
    rows = [b for b in result["top_batches"] if b["batch_no"] == "G2550105" and b["on_hand_packs"] == "13987"]
    assert rows and rows[0]["packs_at_risk"] == "13987" and rows[0]["blocked_packs"] == "0"
    assert rows[0]["source"] == "cnf_stock_snapshot.csv:4783"


def test_stock_review_before_monthly_snapshots_marks_fefo_unavailable(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("stock risk 31-12-2025")

    assert result["checks"]["fefo_signal"]["status"] == "missing"
    assert result["checks"]["expiry_block"]["status"] == "fail"


def test_unknown_stock_snapshot_is_not_found_without_a_model_call(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    result = graph_module.run_question("Expiry check 15-09-2026")

    assert result["route"] == "NOT_FOUND" and result["model_calls"] == 0
    assert "30-09-2026" in result["evidence"][0]["available_snapshots"]


def test_trace_records_the_route_through_the_graph(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: ExplainOnlyLLM())

    claim = graph_module.run_question("Review CLM-2404-04177")
    missing = graph_module.run_question("Review CLM-0000-00000")
    scheme = graph_module.run_question("FY25 Q3")
    stock = graph_module.run_question("Stock review")

    assert claim["trace"][:3] == ["parse_input", "lookup", "dispatch_checks"]
    assert claim["trace"][-2:] == ["decide", "explain"]
    assert {n for n in claim["trace"] if n.startswith("check_")} == {
        "check_window", "check_quantity", "check_duplicate", "check_invoice_ref",
        "check_batch_expiry", "check_value", "check_pasted_fields"}
    assert missing["trace"] == ["parse_input", "lookup"]
    assert scheme["trace"] == ["parse_input", "scheme_review", "explain"]
    assert stock["trace"] == ["parse_input", "stock_review", "explain"]
