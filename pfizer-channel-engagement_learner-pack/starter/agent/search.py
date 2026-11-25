"""Claim search for the claim-review box: find a register claim by number, stockist, SKU or batch.

Read-only and code-only (no model). Pending claims are listed first because they are what the
claims team reviews each week; credited and rejected claims stay searchable for audits and demos.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

from agent.data import DATA_DIR, get_sku, get_stockist, rows_for
from agent.rules import parse_amount, parse_date

DEFAULT_LIMIT = 20
MAX_LIMIT = 50
_STATUS_ORDER = {"Pending": 0, "Rejected": 1, "Credited": 2}


def _iso(value: str) -> str:
    try:
        return parse_date(value).isoformat()
    except (ValueError, TypeError):
        return ""


def _amount(value: str) -> str:
    try:
        return format(parse_amount(value), "f")
    except (ValueError, InvalidOperation, TypeError):
        return ""


@lru_cache(maxsize=None)
def _claim_index(data_dir: Path) -> tuple[dict, ...]:
    """One display row per register claim, with a lower-case text to match against."""
    entries = []
    for claim in rows_for("claim", data_dir) or []:
        stockist = get_stockist(claim.get("stockist_code", ""), data_dir) or {}
        sku = get_sku(claim.get("sku_code", ""), data_dir) or {}
        entry = {
            "kind": "claim",
            "id": claim["claim_no"],
            "claim_date": _iso(claim.get("claim_date", "")),
            "claim_type": claim.get("claim_type", ""),
            "status": claim.get("status", ""),
            "value_inr": _amount(claim.get("claim_value_inr", "")),
            "stockist_code": claim.get("stockist_code", ""),
            "stockist_name": stockist.get("stockist_name", ""),
            "city": stockist.get("city", ""),
            "sku_code": claim.get("sku_code", ""),
            "product": sku.get("product_description", ""),
            "batch_no": claim.get("batch_no", ""),
            "cnf_code": claim.get("cnf_code", ""),
            "source": f"{claim['source_file']}:{claim['source_row']}",
        }
        entry["_text"] = " ".join(str(entry[key]) for key in (
            "id", "stockist_code", "stockist_name", "city", "sku_code", "product", "batch_no", "claim_type", "status",
        )).lower()
        entries.append(entry)
    return tuple(entries)


@lru_cache(maxsize=None)
def _email_index(data_dir: Path) -> tuple[dict, ...]:
    entries = []
    for email in rows_for("email", data_dir) or []:
        entry = {
            "kind": "email",
            "id": email["email_id"],
            "claim_date": _iso(email.get("received_date", "")),
            "from_name": email.get("from_name", ""),
            "subject": email.get("subject", ""),
            "source": f"{email['source_file']}:{email['source_row']}",
        }
        entry["_text"] = f"{entry['id']} {entry['from_name']} {entry['subject']}".lower()
        entries.append(entry)
    return tuple(entries)


def _date_key(entry: dict) -> int:
    """Newest first: a larger ordinal sorts earlier once negated."""
    try:
        return -date.fromisoformat(entry["claim_date"]).toordinal()
    except ValueError:
        return 0


def search_claims(query: str = "", pending_only: bool = False, limit: int = DEFAULT_LIMIT,
                  data_dir: Path = DATA_DIR) -> dict:
    """Return matching claims (and claim emails), pending first, then newest first.

    Every word in the query must appear somewhere in the claim's number, stockist, city, SKU,
    product, batch, type or status. A claim number that starts with the query ranks first.
    """
    limit = max(1, min(int(limit), MAX_LIMIT))
    words = [word for word in query.lower().replace(",", " ").split() if word]
    # "PFL-1303" and "CF-E01" are stored without the hyphen; claim numbers keep theirs.
    match = lambda word, text: word in text or word.replace("-", "") in text  # noqa: E731
    normalized = query.strip().upper().replace(" ", "")

    claims = [entry for entry in _claim_index(data_dir)
              if (not pending_only or entry["status"] == "Pending")
              and all(match(word, entry["_text"]) for word in words)]
    claims.sort(key=lambda entry: (
        0 if normalized and entry["id"].startswith(normalized) else 1,
        _STATUS_ORDER.get(entry["status"], 3),
        _date_key(entry),
        entry["id"],
    ))
    emails = [] if pending_only or not words else [
        entry for entry in _email_index(data_dir) if all(match(word, entry["_text"]) for word in words)
    ]

    public = lambda entry: {key: value for key, value in entry.items() if not key.startswith("_")}  # noqa: E731
    results = [public(entry) for entry in emails[:5]] + [public(entry) for entry in claims[:limit]]
    return {
        "query": query,
        "pending_only": pending_only,
        "total_claims": len(claims),
        "pending_in_register": sum(1 for entry in _claim_index(data_dir) if entry["status"] == "Pending"),
        "results": results[:limit + 5],
    }
