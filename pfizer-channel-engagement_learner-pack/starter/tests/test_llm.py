"""The model client gives up on a stuck provider: 20 s timeout, one retry, then the graph's failure path."""

import json

import httpx
import pytest

import agent.graph as graph_module
from agent import llm as llm_module
from config import MODEL_MAX_RETRIES, MODEL_TIMEOUT_SECONDS


def _reply(text):
    body = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "test",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    return httpx.Response(200, json=body)


class TimeoutThenReply:
    """Fake provider: time out on the first `timeouts` requests, then answer."""

    def __init__(self, timeouts):
        self.timeouts = timeouts
        self.requests = 0

    def __call__(self, request):
        self.requests += 1
        if self.requests <= self.timeouts:
            raise httpx.ReadTimeout("provider stuck", request=request)
        return _reply("The route is ready. A person remains responsible for any final action.")


@pytest.fixture
def fake_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


def test_model_client_has_20_second_timeout_and_one_retry(fake_key):
    client = llm_module.get_llm()
    assert MODEL_TIMEOUT_SECONDS == 20 and MODEL_MAX_RETRIES == 1
    assert client.request_timeout == 20
    assert client.max_retries == 1


def test_one_timeout_is_retried_once_and_then_succeeds(fake_key):
    provider = TimeoutThenReply(timeouts=1)
    client = llm_module.get_llm(http_client=httpx.Client(transport=httpx.MockTransport(provider)))

    reply = client.invoke("hello")

    assert provider.requests == 2
    assert "person remains responsible" in reply.content


def test_two_timeouts_stop_after_one_retry_and_the_graph_keeps_the_code_route(fake_key, monkeypatch):
    provider = TimeoutThenReply(timeouts=99)
    monkeypatch.setattr(
        graph_module, "get_llm",
        lambda: llm_module.get_llm(http_client=httpx.Client(transport=httpx.MockTransport(provider))),
    )

    result = graph_module.run_question("Review CLM-2605-04488")

    assert provider.requests == 2  # first try + one retry, then give up
    assert result["route"] == "REJECT"  # decided by code, unaffected by the stuck model
    assert result["explanation"].startswith("Route: REJECT.")  # code fallback text


def test_stuck_provider_during_free_text_parse_goes_to_a_person(fake_key, monkeypatch):
    provider = TimeoutThenReply(timeouts=99)
    monkeypatch.setattr(
        graph_module, "get_llm",
        lambda: llm_module.get_llm(http_client=httpx.Client(transport=httpx.MockTransport(provider))),
    )

    result = graph_module.run_question("Please check the note from our stockist.")

    assert result["route"] == "NEEDS_PERSON"
    assert "Timeout" in result["checks"]["input_parse"]["reason"]
