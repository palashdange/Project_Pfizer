"""The API answers without a model when we swap in a fake. No key, no cost."""
import json
from pathlib import Path

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

import agent.graph as g
from app import app


class FakeLLM:
    """Asks for one tool call, then answers. Enough to test the wiring."""

    def __init__(self):
        self.calls = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return AIMessage(content="", tool_calls=[{"name": "lookup_batch", "args": {"batch_no": "K2300101"}, "id": "t1"}])
        return AIMessage(content="Batch K2300101 expires on 30-09-2025.")


def test_ask_runs_the_tool_loop(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(g, "get_llm", lambda: fake)
    r = TestClient(app).post("/api/ask", json={"question": "When does K2300101 expire?"})
    assert r.status_code == 200
    body = r.json()
    assert body["evidence"][0]["expiry_date"] == "30-09-2025"
    assert body["evidence"][0]["found"] is True
    assert body["model_calls"] == 2


def test_ask_can_run_the_shelf_life_tool(monkeypatch):
    class FakeShelfLifeLLM:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            return self

        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "find_short_shelf_life_shipments",
                            "args": {"limit": 1},
                            "id": "shelf-life-tool-call",
                        }
                    ],
                )
            return AIMessage(content="Here is the shelf-life review.")

    fake = FakeShelfLifeLLM()
    monkeypatch.setattr(g, "get_llm", lambda: fake)
    response = TestClient(app).post(
        "/api/ask", json={"question": "Which shipments have short shelf life?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_calls"] == 2
    assert body["evidence"][0]["flagged_count"] >= 0
    assert body["evidence"][0]["date_used_as_dispatch_proxy"] == "invoice_date"


def test_ask_can_run_the_cfa_stock_imbalance_tool(monkeypatch):
    class FakeStockLLM:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            return self

        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "find_cfa_stock_imbalances",
                        "args": {"limit": 1},
                        "id": "stock-tool-call",
                    }],
                )
            return AIMessage(content="Here are the CFA stock differences for review.")

    fake = FakeStockLLM()
    monkeypatch.setattr(g, "get_llm", lambda: fake)
    response = TestClient(app).post(
        "/api/ask", json={"question": "Which SKUs have stock at one CFA and none at another?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_calls"] == 2
    assert "cross_cfa_imbalance_sku_count" in body["evidence"][0]
    assert "latest_snapshot_date" in body["evidence"][0]


def test_ask_can_run_the_primary_shipment_forecast_tool(monkeypatch):
    class FakeForecastLLM:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            assert "forecast_primary_shipments" in {tool.name for tool in tools}
            return self

        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "forecast_primary_shipments",
                        "args": {
                            "cfa_code": "CF-N02",
                            "sku_code": "PFL1001",
                            "horizon_months": 3,
                        },
                        "id": "forecast-tool-call",
                    }],
                )
            return AIMessage(content="Here is the shipment baseline forecast.")

    fake = FakeForecastLLM()
    monkeypatch.setattr(g, "get_llm", lambda: fake)
    response = TestClient(app).post(
        "/api/ask", json={"question": "Forecast primary shipments for this CFA and SKU."}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_calls"] == 2
    evidence = body["evidence"][0]
    assert evidence["forecast_type"].startswith("primary shipments")
    assert evidence["forecasts"][0]["baseline_source_file"] == "primary_sales.csv"
    assert evidence["forecasts"][0]["baseline_source_rows"]


def test_ask_can_run_the_claim_review_tool_and_uses_untrusted_email_guardrails(monkeypatch):
    class FakeClaimLLM:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            assert "review_expiry_claim" in {tool.name for tool in tools}
            return self

        def invoke(self, messages):
            self.calls += 1
            assert "untrusted data" in messages[0].content
            assert "never call a claim approved or rejected" in messages[0].content
            if self.calls == 1:
                return AIMessage(content="", tool_calls=[{
                    "name": "review_expiry_claim",
                    "args": {"claim_no": "CLM-2605-04488"},
                    "id": "claim-tool-call",
                }])
            return AIMessage(content="A possible prior credit needs human review.")

    fake = FakeClaimLLM()
    monkeypatch.setattr(g, "get_llm", lambda: fake)
    response = TestClient(app).post(
        "/api/ask", json={"question": "Review claim CLM-2605-04488."}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_calls"] == 2
    assert body["evidence"][0]["duplicate_signal"] == "possible_repeat_credit"
    assert body["evidence"][0]["review_status"] == "NEEDS_HUMAN_REVIEW"


def test_ask_can_retrieve_claim_email_as_untrusted_source_evidence(monkeypatch):
    class FakeEmailLLM:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            assert "lookup_claim_email" in {tool.name for tool in tools}
            return self

        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return AIMessage(content="", tool_calls=[{
                    "name": "lookup_claim_email",
                    "args": {"email_id": "EML-017"},
                    "id": "email-tool-call",
                }])
            return AIMessage(content="The email contains an untrusted request to bypass checks.")

    monkeypatch.setattr(g, "get_llm", lambda: FakeEmailLLM())
    response = TestClient(app).post("/api/ask", json={"question": "Inspect email EML-017."})

    assert response.status_code == 200
    evidence = response.json()["evidence"][0]
    assert evidence["result_type"] == "claim_email_evidence"
    assert evidence["body_trust_status"] == "untrusted_correspondence"
    assert evidence["source_row"] == 28


def test_health():
    assert TestClient(app).get("/api/health").json()["ok"] is True


def test_vercel_config_keeps_runtime_evidence_and_excludes_development_files():
    config = json.loads((Path(__file__).resolve().parents[1] / "vercel.json").read_text())

    assert "app.py" in config["functions"]
    exclusions = config["functions"]["app.py"]["excludeFiles"]
    assert "tests/**" in exclusions
    assert ".env" in exclusions
    assert "data/**" not in exclusions


def test_claim_case_csvs_match_the_supplied_data_pack():
    starter_data = Path(__file__).resolve().parents[1] / "data"
    source_data = starter_data.parents[1] / "data-pack" / "data"

    for filename in ("claim_emails.csv", "expiry_claims.csv", "stockist_master.csv"):
        assert (starter_data / filename).read_bytes() == (source_data / filename).read_bytes()
