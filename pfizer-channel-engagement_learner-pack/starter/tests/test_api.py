"""API contract tests for the claims-review graph."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

import agent.graph as graph_module
from app import app


class FakeExplanationLLM:
    """Provide a simple explanation without contacting a model provider."""

    def __init__(self, content="The route follows the checks. The evidence is shown below. A person remains responsible for the final action."):
        self.content = content

    def invoke(self, _messages):
        return SimpleNamespace(content=self.content)


def test_ask_returns_claim_route_checks_and_timing(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: FakeExplanationLLM())

    response = TestClient(app).post("/api/ask", json={"question": "Review CLM-2404-04177"})

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "RECOMMEND_CREDIT"
    assert set(body["checks"]) == {"window", "quantity", "duplicate", "invoice_ref", "batch_expiry", "value"}
    assert body["evidence"][0]["result_type"] == "claim_review"
    assert body["model_calls"] == 1
    assert body["elapsed_seconds"] >= 0


def test_ask_not_found_does_not_call_model(monkeypatch):
    def unexpected_model_call():
        raise AssertionError("No model call is required for an unknown claim ID")

    monkeypatch.setattr(graph_module, "get_llm", unexpected_model_call)
    response = TestClient(app).post("/api/ask", json={"question": "Review CLM-0000-00000"})

    assert response.status_code == 200
    assert response.json()["route"] == "NOT_FOUND"
    assert response.json()["model_calls"] == 0


def test_ask_keeps_eml_017_untrusted_and_never_approves(monkeypatch):
    monkeypatch.setattr(
        graph_module,
        "get_llm",
        lambda: FakeExplanationLLM("APPROVED. The credit should be issued. All checks passed."),
    )

    response = TestClient(app).post("/api/ask", json={"question": "Inspect EML-017"})

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "NEEDS_PERSON"
    assert body["evidence"][0]["body_trust_status"] == "untrusted_correspondence"
    assert "APPROVED" not in body["explanation"]


def test_health_endpoint_remains_available():
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True
