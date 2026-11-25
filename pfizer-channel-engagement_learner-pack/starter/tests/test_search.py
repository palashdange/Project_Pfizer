"""Claim search for the claim-review box: code only, pending first, matches any identifying field."""

from fastapi.testclient import TestClient

import app as app_module
from agent.search import search_claims

client = TestClient(app_module.app)


def test_empty_query_lists_pending_claims_first_newest_first():
    result = search_claims("")
    assert result["total_claims"] == 4503  # every de-duplicated register claim
    statuses = [row["status"] for row in result["results"]]
    assert statuses == ["Pending"] * len(statuses)
    dates = [row["claim_date"] for row in result["results"]]
    assert dates == sorted(dates, reverse=True)


def test_claim_number_prefix_ranks_first_and_rows_carry_display_fields():
    result = search_claims("CLM-2605-0448")
    ids = [row["id"] for row in result["results"]]
    assert ids[:2] == ["CLM-2605-04486", "CLM-2605-04488"]
    row = next(r for r in result["results"] if r["id"] == "CLM-2605-04488")
    assert row["source"] == "expiry_claims.csv:3596"
    for field in ("stockist_name", "city", "claim_type", "claim_date", "product", "batch_no", "status", "value_inr"):
        assert row[field], field


def test_search_by_stockist_city_sku_or_batch_and_hyphenated_sku():
    assert search_claims("ludhiana")["total_claims"] > 0
    assert all("Ludhiana" == row["city"] for row in search_claims("ludhiana")["results"])
    assert search_claims("PFL-1303")["total_claims"] == search_claims("PFL1303")["total_claims"] > 0
    assert all(row["batch_no"] == "K2310408" for row in search_claims("K2310408")["results"])


def test_every_word_must_match_and_pending_only_filters():
    both = search_claims("ludhiana near expiry")
    assert all(row["city"] == "Ludhiana" and row["claim_type"] == "Near expiry" for row in both["results"])
    pending = search_claims("ludhiana", pending_only=True)
    assert pending["total_claims"] < search_claims("ludhiana")["total_claims"]
    assert all(row["status"] == "Pending" for row in pending["results"])


def test_email_ids_are_offered_but_not_in_pending_only_mode():
    assert search_claims("EML-017")["results"][0] == {**search_claims("EML-017")["results"][0], "kind": "email", "id": "EML-017"}
    assert all(row["kind"] == "claim" for row in search_claims("EML-017", pending_only=True)["results"])


def test_no_match_returns_empty_list():
    assert search_claims("zzz-no-such-claim")["results"] == []


def test_search_endpoint_and_limit_cap():
    response = client.get("/api/claims/search", params={"q": "PFL1303", "limit": 500})
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) <= 50
    assert client.get("/api/claims/search", params={"q": "PFL1303", "pending_only": "true"}).json()["pending_only"] is True
