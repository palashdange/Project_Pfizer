"""Claims-review LangGraph: models extract/explain; Python owns every decision."""

import json
import re
import time
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from agent import data
from agent.llm import get_llm
from agent.prompts import EXPLAIN_SYSTEM_PROMPT, PARSE_INPUT_SYSTEM_PROMPT
from agent.schemes import available_quarters, review_scheme
from agent.rules import (
    assess_expiry_claim_window,
    assess_transit_claim_window,
    classify_prior_claim,
    compare_pasted_fields,
    compare_claim_value_at_pts,
    compare_claim_quantity,
    parse_date,
    parse_pack_quantity,
)
from config import (
    BATCH_EXPIRY_POLICY_CLAUSE,
    CLAIM_QUANTITY_POLICY_CLAUSE,
    CLAIM_VALUE_POLICY_CLAUSE,
    DUPLICATE_CLAIM_POLICY_CLAUSE,
    EXPIRY_CLAIM_POLICY_CLAUSE,
    INVOICE_REFERENCE_POLICY_CLAUSE,
    PASTED_FIELDS_POLICY_CLAUSE,
    TRANSIT_CLAIM_POLICY_CLAUSE,
)

CLAIM_PATTERN = re.compile(r"\bCLM-\d{4}-\d{5}\b", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\bEML-\d{3}\b", re.IGNORECASE)
SCHEME_PATTERN = re.compile(r"\bQS-FY\d{2}Q[1-4]-[AB]\b|\bFY\s?\d{2}\s*Q[1-4]\b", re.IGNORECASE)


class ClaimExtraction(BaseModel):
    """Fields a model may extract from free-form claim text; it has no decision field."""

    model_config = ConfigDict(extra="forbid")
    claim_no: Optional[str] = None
    stockist_code: Optional[str] = None
    sku_code: Optional[str] = None
    batch_no: Optional[str] = None
    qty: Optional[str] = None
    claim_type: Optional[str] = None
    invoice_ref: Optional[str] = None
    expiry_claimed: Optional[str] = None
    claim_value: Optional[str] = None


class State(TypedDict):
    """Per-request state; parallel checks merge by their unique check keys."""

    input_text: str
    claim_no: str
    email_id: str
    records: dict[str, Any]
    checks: Annotated[dict[str, dict], lambda old, new: {**old, **new}]
    route: str
    explanation: str
    evidence: list[dict]
    model_calls: int
    elapsed_seconds: float
    scheme_target: str


def _source_row(row: Optional[dict]) -> Optional[dict]:
    """Reduce a source record to an audit citation while retaining useful identifiers."""
    if not row:
        return None
    identifier = next((row.get(k) for k in (
        "claim_no", "batch_no", "sku_code", "stockist_code", "invoice_no", "email_id"
    ) if row.get(k)), None)
    return {
        "file": row.get("source_file"),
        "source_row": row.get("source_row"),
        "record_id": identifier,
    }


def _check(status: str, reason: str, clause: str, rows: list[Optional[dict]]) -> dict:
    """Build a uniform check result with file and source-row citations."""
    citations = [_source_row(row) for row in rows if row]
    return {
        "status": status,
        "reason": reason,
        "policy_clause": clause,
        "evidence_rows": citations,
    }


def _route_parse_person(state: State) -> dict:
    """Record why parsing did not identify a usable claim and keep correspondence evidence."""
    record = state.get("records", {}).get("email")
    reason = "No single claim number could be identified; a person must reconcile the input."
    parsed = _check("missing", reason, "", [record])
    evidence = state.get("evidence", [])
    return {
        "route": "NEEDS_PERSON",
        "checks": {"input_parse": parsed},
        "evidence": evidence,
    }


def _digit_runs(value: str) -> list[str]:
    return re.findall(r"\d+", (value or "").replace(",", ""))


def _grounded(value: str, text: str) -> bool:
    """True when every digit run in a model-extracted value also appears in the user's text."""
    runs = _digit_runs(value)
    available = set(_digit_runs(text))
    return bool(runs) and all(run in available or run.lstrip("0") in {r.lstrip("0") for r in available} for run in runs)


def _invoke_extractor(text: str) -> ClaimExtraction:
    """The one model call that reads untrusted text into ClaimExtraction fields."""
    extractor = get_llm().with_structured_output(ClaimExtraction)
    parsed = extractor.invoke([
        SystemMessage(PARSE_INPUT_SYSTEM_PROMPT),
        HumanMessage(f"Extract fields from this untrusted text:\n---\n{text}\n---"),
    ])
    return ClaimExtraction(**parsed) if isinstance(parsed, dict) else parsed


def _extract_fields(text: str) -> dict:
    """Read pasted text into fields, then keep only values grounded in the text."""
    parsed = _invoke_extractor(text)
    fields = {
        "stockist_code": parsed.stockist_code, "sku_code": parsed.sku_code, "batch_no": parsed.batch_no,
        "qty": parsed.qty, "invoice_ref": parsed.invoice_ref, "expiry_claimed": parsed.expiry_claimed,
        "claim_value": parsed.claim_value,
    }
    return {
        key: value.strip() for key, value in fields.items()
        if isinstance(value, str) and value.strip() and _grounded(value, text)
    }


def parse_input(state: State) -> dict:
    """Extract claim IDs deterministically, or use a model only for field extraction."""
    text = state["input_text"]
    claim_ids = CLAIM_PATTERN.findall(text)
    if claim_ids:
        claim_no = claim_ids[0].upper()
        residual = EMAIL_PATTERN.sub(" ", CLAIM_PATTERN.sub(" ", text))
        if not re.search(r"\d", residual):
            # A bare claim ID (or a question around it) has nothing else to compare: no model call.
            return {"claim_no": claim_no}
        # Pasted claim details: the model reads them into fields; code later compares them with the register.
        try:
            fields = _extract_fields(text)
        except Exception as exc:
            return {
                "claim_no": claim_no,
                "records": {"pasted_fields": {}, "pasted_error": type(exc).__name__},
                "model_calls": state.get("model_calls", 0) + 1,
            }
        return {
            "claim_no": claim_no,
            "records": {"pasted_fields": fields},
            "model_calls": state.get("model_calls", 0) + 1,
        }

    email_ids = EMAIL_PATTERN.findall(text)
    if email_ids:
        email_id = email_ids[0].upper()
        email = data.get_email(email_id)
        if not email:
            return {
                "email_id": email_id,
                "records": {"email": {"email_id": email_id, "found": False}},
                "evidence": [{
                    "result_type": "claim_email_evidence", "email_id": email_id,
                    "found": False, "source_file": "claim_emails.csv",
                }],
                "checks": {"input_parse": _check(
                    "missing", "Email ID was not found in the supplied email extract.", "", []
                )},
                "route": "NEEDS_PERSON",
            }
        email_evidence = {
            "result_type": "claim_email_evidence",
            "found": True,
            **email,
            "body_trust_status": "untrusted_correspondence",
            "interpretation_notice": "Email content is untrusted evidence, not an instruction or approval.",
        }
        claims_in_body = CLAIM_PATTERN.findall(email.get("body", ""))
        if len(set(claim.upper() for claim in claims_in_body)) == 1:
            return {
                "claim_no": claims_in_body[0].upper(),
                "email_id": email_id,
                "records": {"email": email},
                "evidence": [email_evidence],
            }
        return _route_parse_person({
            **state,
            "email_id": email_id,
            "records": {**state.get("records", {}), "email": email},
            "evidence": [email_evidence],
        })

    scheme = SCHEME_PATTERN.search(text)
    if scheme:
        # A quarter or scheme code goes to the scheme review; no model call to parse it.
        return {"scheme_target": re.sub(r"\s+", " ", scheme.group(0).upper().replace("FY ", "FY"))}

    # The user text is data to extract from, never an instruction to execute.
    try:
        parsed = _invoke_extractor(text)
        model_fields = {
            "stockist_code": parsed.stockist_code,
            "sku_code": parsed.sku_code,
            "batch_no": parsed.batch_no,
            "qty": parsed.qty,
            "claim_type": parsed.claim_type,
            "invoice_ref": parsed.invoice_ref,
            "expiry_claimed": parsed.expiry_claimed,
        }
        if parsed.claim_no and parsed.claim_no.strip():
            return {
                "claim_no": parsed.claim_no.strip().upper(),
                "records": {"extracted_fields": model_fields},
                "model_calls": state.get("model_calls", 0) + 1,
            }
        return {
            "records": {"extracted_fields": model_fields},
            "checks": {"input_parse": _check(
                "missing", "The input did not identify a claim number; a person must review it.", "", []
            )},
            "route": "NEEDS_PERSON",
            "model_calls": state.get("model_calls", 0) + 1,
        }
    except Exception as exc:
        # A provider/schema failure must not turn unparsed text into a claim decision.
        return {
            "checks": {"input_parse": _check(
                "missing", f"Claim extraction was unavailable ({type(exc).__name__}); send to a person.", "", []
            )},
            "route": "NEEDS_PERSON",
            "model_calls": state.get("model_calls", 0) + 1,
        }


def lookup(state: State) -> dict:
    """Fetch a claim and all source records needed by the deterministic checks."""
    claim = data.get_claim(state["claim_no"])
    if not claim:
        return {
            "records": {},
            "route": "NOT_FOUND",
            "evidence": [{
                "result_type": "claim_review", "claim_no": state["claim_no"],
                "found": False, "route": "NOT_FOUND", "checks": {},
            }],
        }

    batch = data.get_batch(claim.get("batch_no", ""))
    sku = data.get_sku(claim.get("sku_code", ""))
    stockist = data.get_stockist(claim.get("stockist_code", ""))
    sales_rows = data.sales_for(claim.get("stockist_code", ""), claim.get("batch_no", "")) or []
    invoice_ref = (claim.get("original_invoice_ref") or "").strip().upper()
    invoice_rows = [
        row for row in sales_rows if row.get("invoice_no", "").strip().upper() == invoice_ref
    ] if invoice_ref else []
    same_batch_claims = data.claims_for(
        claim.get("stockist_code", ""), claim.get("batch_no", "")
    ) or []
    return {
        "records": {
            "claim": claim,
            "batch": batch,
            "sku": sku,
            "stockist": stockist,
            "sales_rows": sales_rows,
            "invoice_rows": invoice_rows,
            "same_batch_claims": same_batch_claims,
            "email": state.get("records", {}).get("email"),
            "pasted_fields": state.get("records", {}).get("pasted_fields"),
            "pasted_error": state.get("records", {}).get("pasted_error"),
        },
        "route": "",
    }


def check_window(state: State) -> dict:
    """Apply the expiry or transit filing window from CO-POL-014 §5.2."""
    records = state["records"]
    claim = records["claim"]
    claim_type = (claim.get("claim_type") or "").strip().casefold()
    if claim_type in {"breakage in transit", "short supply"}:
        invoices = records["invoice_rows"]
        if not invoices:
            result = _check("missing", "Original invoice and its date could not be matched.", TRANSIT_CLAIM_POLICY_CLAUSE, [claim])
        else:
            try:
                assessed = assess_transit_claim_window(claim.get("claim_date", ""), invoices[0].get("invoice_date", ""))
                status = "pass" if assessed["status"] == "within_window" else "fail"
                result = _check(status, f"{assessed['elapsed_days']} days after invoice; {assessed['reason']}.", TRANSIT_CLAIM_POLICY_CLAUSE, [claim, invoices[0]])
            except ValueError as exc:
                result = _check("missing", str(exc), TRANSIT_CLAIM_POLICY_CLAUSE, [claim, invoices[0]])
    elif claim_type in {"near expiry", "expired", "near_expiry"}:
        batch = records["batch"]
        if not batch:
            result = _check("missing", "Batch master expiry date is unavailable.", EXPIRY_CLAIM_POLICY_CLAUSE, [claim])
        else:
            try:
                assessed = assess_expiry_claim_window(claim_type, claim.get("claim_date", ""), batch.get("expiry_date", ""))
                status = "pass" if assessed["status"] == "within_window" else "fail"
                result = _check(status, f"{assessed['elapsed_days']} days from batch expiry; {assessed['reason']}.", EXPIRY_CLAIM_POLICY_CLAUSE, [claim, batch])
            except ValueError as exc:
                result = _check("missing", str(exc), EXPIRY_CLAIM_POLICY_CLAUSE, [claim, batch])
    else:
        result = _check("missing", f"Unsupported claim type: {claim_type or 'blank'}.", EXPIRY_CLAIM_POLICY_CLAUSE, [claim])
    return {"checks": {"window": result}}


def check_quantity(state: State) -> dict:
    """Compare claimed packs with all invoiced plus free packs for the same stockist/batch."""
    records = state["records"]
    claim = records["claim"]
    sales = records["sales_rows"]
    if not sales:
        result = _check("missing", "No sales rows were found for this stockist and batch.", CLAIM_QUANTITY_POLICY_CLAUSE, [claim])
    else:
        try:
            recorded = sum((
                parse_pack_quantity(row.get("invoiced_qty", "")) +
                parse_pack_quantity(row.get("free_qty", "0")) for row in sales
            ), Decimal("0"))
            comparison = compare_claim_quantity(claim.get("qty_claimed", ""), str(recorded))
            status = "pass" if comparison["status"] == "within_recorded_quantity" else "fail"
            result = _check(status, f"Claimed {comparison['claimed_quantity']} packs; recorded invoiced plus free quantity is {comparison['recorded_quantity']} packs.", CLAIM_QUANTITY_POLICY_CLAUSE, [claim, *sales])
            result["claimed_quantity"] = comparison["claimed_quantity"]
            result["recorded_quantity"] = comparison["recorded_quantity"]
        except ValueError as exc:
            result = _check("missing", str(exc), CLAIM_QUANTITY_POLICY_CLAUSE, [claim, *sales])
    return {"checks": {"quantity": result}}


def check_duplicate(state: State) -> dict:
    """Check earlier claims on the same stockist and batch (§5.6).

    An exact repeat of a credited claim fails (REJECT). A repeat of a pending claim, or a quantity
    within the configured near-repeat tolerance, needs a person ("review").
    """
    records = state["records"]
    claim = records["claim"]
    try:
        current_date = parse_date(claim.get("claim_date", ""))
        current_qty = parse_pack_quantity(claim.get("qty_claimed", ""))
        current_row = claim.get("source_row") or 0
        found: dict[str, list[dict]] = {"repeat_of_credited": [], "repeat_of_pending": [], "near_repeat": []}
        for item in records["same_batch_claims"]:
            if item.get("claim_no") == claim.get("claim_no"):
                continue
            try:
                item_date = parse_date(item.get("claim_date", ""))
                item_qty = parse_pack_quantity(item.get("qty_claimed", ""))
            except ValueError:
                continue
            # Only claims filed before this one; same-day claims count if they appear earlier in the register.
            if item_date > current_date or (item_date == current_date and (item.get("source_row") or 0) >= current_row):
                continue
            kind = classify_prior_claim(
                current_qty, item_qty, item.get("status", ""), bool((item.get("credit_note_no") or "").strip())
            )
            if kind:
                found[kind].append(item)
        labels = {
            "repeat_of_credited": "earlier credited claim with the same quantity",
            "repeat_of_pending": "earlier unsettled claim with the same quantity",
            "near_repeat": "earlier claim with a near-equal quantity",
        }
        parts = [
            f"{labels[kind]}: " + ", ".join(f"{i.get('claim_no')} ({i.get('qty_claimed')} packs, {i.get('status')})" for i in items)
            for kind, items in found.items() if items
        ]
        if found["repeat_of_credited"]:
            status = "fail"
        elif found["repeat_of_pending"] or found["near_repeat"]:
            status = "review"
        else:
            status = "pass"
        reason = ("Same stockist and batch — " + "; ".join(parts) + "." + (" A person must check whether this is the same stock." if status == "review" else "")
                  if parts else "No earlier claim on this stockist and batch repeats this quantity.")
        prior = [i for items in found.values() for i in items]
        result = _check(status, reason, DUPLICATE_CLAIM_POLICY_CLAUSE, [claim, *prior])
        result["matched_claims"] = [item.get("claim_no") for item in prior]
    except ValueError as exc:
        result = _check("missing", str(exc), DUPLICATE_CLAIM_POLICY_CLAUSE, [claim])
    return {"checks": {"duplicate": result}}


def check_invoice_ref(state: State) -> dict:
    """Require a nonblank original invoice reference that matches sales evidence."""
    records = state["records"]
    claim = records["claim"]
    invoice_ref = (claim.get("original_invoice_ref") or "").strip()
    if not invoice_ref:
        result = _check("missing", "Original invoice reference is blank; route for written approval/ledger review.", INVOICE_REFERENCE_POLICY_CLAUSE, [claim])
    elif not records["invoice_rows"]:
        result = _check("missing", f"Invoice reference {invoice_ref} did not match a sales row for this stockist and batch.", INVOICE_REFERENCE_POLICY_CLAUSE, [claim])
    else:
        result = _check("pass", f"Invoice reference {invoice_ref} matched the sales ledger.", INVOICE_REFERENCE_POLICY_CLAUSE, [claim, *records["invoice_rows"]])
    return {"checks": {"invoice_ref": result}}


def check_batch_expiry(state: State) -> dict:
    """Compare claimed expiry to the official batch-master date."""
    records = state["records"]
    claim, batch = records["claim"], records["batch"]
    claimed_expiry = claim.get("expiry_date_as_claimed", "")
    if not batch:
        result = _check("missing", "Batch was not found in the batch master.", BATCH_EXPIRY_POLICY_CLAUSE, [claim])
    elif not claimed_expiry:
        result = _check("missing", "Claimed expiry date is blank.", BATCH_EXPIRY_POLICY_CLAUSE, [claim, batch])
    else:
        try:
            matches = parse_date(claimed_expiry) == parse_date(batch.get("expiry_date", ""))
            result = _check("pass" if matches else "fail", "Claimed expiry matches batch master." if matches else "Claimed expiry differs from batch master; a person must verify it.", BATCH_EXPIRY_POLICY_CLAUSE, [claim, batch])
        except ValueError as exc:
            result = _check("missing", str(exc), BATCH_EXPIRY_POLICY_CLAUSE, [claim, batch])
    return {"checks": {"batch_expiry": result}}


def check_value(state: State) -> dict:
    """Compare the claim amount with quantity × product-master PTS."""
    records = state["records"]
    claim, sku = records["claim"], records["sku"]
    if not sku:
        result = _check("missing", "SKU master PTS is unavailable.", CLAIM_VALUE_POLICY_CLAUSE, [claim])
    else:
        try:
            assessed = compare_claim_value_at_pts(
                claim.get("qty_claimed", ""), sku.get("pts_inr", ""), claim.get("claim_value_inr", "")
            )
            mismatch = assessed["status"] != "match"
            result = _check(
                "fail" if mismatch else "pass",
                f"Claim value is {assessed['claim_value_inr']}; quantity × PTS is {assessed['calculated_value_inr']}." + (" Send the mismatch to a person." if mismatch else ""),
                CLAIM_VALUE_POLICY_CLAUSE,
                [claim, sku],
            )
            result["calculated_value_inr"] = format(assessed["calculated_value_inr"], "f")
            result["claim_value_inr"] = format(assessed["claim_value_inr"], "f")
        except (ValueError, InvalidOperation, AttributeError) as exc:
            result = _check("missing", str(exc), CLAIM_VALUE_POLICY_CLAUSE, [claim, sku])
    return {"checks": {"value": result}}


def check_pasted_fields(state: State) -> dict:
    """Compare claim details pasted with the claim ID against the register; any conflict needs a person."""
    records = state["records"]
    claim, batch = records["claim"], records.get("batch")
    if records.get("pasted_error"):
        result = _check("missing", f"Pasted details could not be read ({records['pasted_error']}); a person must compare them.",
                        PASTED_FIELDS_POLICY_CLAUSE, [claim])
        return {"checks": {"pasted_fields": result}}
    pasted = records.get("pasted_fields") or {}
    if not pasted:
        return {}
    register = {
        "stockist_code": claim.get("stockist_code"), "sku_code": claim.get("sku_code"),
        "batch_no": claim.get("batch_no"), "qty": claim.get("qty_claimed"),
        "claim_value_inr": claim.get("claim_value_inr"), "invoice_ref": claim.get("original_invoice_ref"),
        "expiry": (batch or {}).get("expiry_date") or claim.get("expiry_date_as_claimed"),
    }
    rows = compare_pasted_fields(pasted, register)
    if not rows:
        return {}
    conflicts = [r for r in rows if r["match"] is not True]
    if conflicts:
        detail = "; ".join(f"{r['field']}: pasted {r['pasted']} vs register {r['register']}" for r in conflicts)
        result = _check("review", f"Pasted details differ from the register — {detail}. A person must check which is right.",
                        PASTED_FIELDS_POLICY_CLAUSE, [claim, batch])
    else:
        result = _check("pass", "Pasted details match the register: " + ", ".join(r["field"] for r in rows) + ".",
                        PASTED_FIELDS_POLICY_CLAUSE, [claim, batch])
    result["compared_fields"] = rows
    return {"checks": {"pasted_fields": result}}


def at_stake_inr(claim: dict, sku: Optional[dict]) -> Optional[Decimal]:
    """Rupees at stake: the register claim value, or quantity x PTS when it is blank (§5.7)."""
    raw = str(claim.get("claim_value_inr") or "").replace(",", "").strip()
    if raw:
        try:
            return Decimal(raw)
        except InvalidOperation:
            pass
    try:
        qty = parse_pack_quantity(claim.get("qty_claimed", ""))
        pts = Decimal(str((sku or {}).get("pts_inr") or "").replace(",", ""))
    except (ValueError, InvalidOperation):
        return None
    return (qty * pts).quantize(Decimal("0.01"))


def decide(state: State) -> dict:
    """Apply the deterministic route priority; never ask the model for a decision."""
    checks = state["checks"]
    if any(checks.get(key, {}).get("status") == "fail" for key in ("window", "duplicate", "quantity")):
        route = "REJECT"
    elif state.get("email_id"):
        route = "NEEDS_PERSON"
    elif any(checks.get(key, {}).get("status") in {"missing", "fail", "review"} for key in checks):
        route = "NEEDS_PERSON"
    else:
        route = "RECOMMEND_CREDIT"

    claim = state["records"]["claim"]
    evidence = [{
        "result_type": "claim_review",
        "found": True,
        "claim_no": claim.get("claim_no"),
        "route": route,
        "at_stake_inr": (lambda v: format(v, "f") if v is not None else None)(at_stake_inr(claim, state["records"].get("sku"))),
        "checks": checks,
        "records": {
            "claim": _source_row(claim),
            "batch": _source_row(state["records"].get("batch")),
            "sku": _source_row(state["records"].get("sku")),
            "stockist": _source_row(state["records"].get("stockist")),
        },
    }]
    return {"route": route, "evidence": evidence}


def _fallback_explanation(route: str, checks: dict) -> str:
    """Summarize only values already present in checks when model explanation fails."""
    failed = [f"{name}: {item.get('reason', 'review needed')} ({item.get('policy_clause', 'no clause')})"
              for name, item in checks.items() if item.get("status") in {"fail", "missing", "review"}]
    passed = [name for name, item in checks.items() if item.get("status") == "pass"]
    first = f"Route: {route}."
    second = "Checks needing attention: " + ("; ".join(failed) if failed else "none") + "."
    third = "Checks passed: " + (", ".join(passed) if passed else "none") + ". A person remains responsible for the final action."
    return f"{first} {second} {third}"


def explain(state: State) -> dict:
    """Generate a constrained explanation; code fallback preserves the route."""
    route = state["route"]
    checks = state.get("checks", {})
    calls = state.get("model_calls", 0) + 1
    try:
        reply = get_llm().invoke([
            SystemMessage(EXPLAIN_SYSTEM_PROMPT),
            HumanMessage(json.dumps({"route": route, "checks": checks}, ensure_ascii=False, default=str)),
        ])
        explanation = str(reply.content).strip()
        allowed_numbers = set(re.findall(r"\d+(?:[.,]\d+)*", json.dumps(checks, ensure_ascii=False, default=str)))
        used_numbers = set(re.findall(r"\d+(?:[.,]\d+)*", explanation))
        # Keep the model from presenting a recommendation as an executed approval or action.
        unsafe_decision_text = bool(
            re.search(
                r"\b(approve|approved|recommend(?:ed)? credit|credit this claim)\b"
                r"|\b(?:has|have) been (?:rejected|credited|approved|paid|settled)\b"
                r"|\bwas (?:rejected|credited|approved|paid|settled)\b",
                explanation, re.IGNORECASE,
            )
        )
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", explanation) if part]
        if not 3 <= len(sentences) <= 5 or not used_numbers.issubset(allowed_numbers) or unsafe_decision_text:
            explanation = _fallback_explanation(route, checks)
    except Exception:
        explanation = _fallback_explanation(route, checks)
    return {"explanation": explanation, "model_calls": calls}


def scheme_review(state: State) -> dict:
    """Review a quarter-end scheme or quarter against §4.4, Annexure B and §4.5, in code."""
    result = review_scheme(state["scheme_target"])
    if result is None:
        return {
            "route": "NOT_FOUND",
            "evidence": [{"result_type": "scheme_review", "target": state["scheme_target"], "found": False,
                          "route": "NOT_FOUND", "checks": {},
                          "available_quarters": available_quarters()}],
        }
    return {
        "route": result["route"],
        "checks": result["checks"],
        "evidence": [{"result_type": "scheme_review", "found": True, **result}],
    }


def _after_scheme(state: State) -> str:
    return END if state.get("route") == "NOT_FOUND" else "explain"


def _after_parse(state: State) -> str:
    if state.get("scheme_target"):
        return "scheme_review"
    if state.get("route") == "NEEDS_PERSON" and not state.get("claim_no"):
        return "explain"
    return "lookup"


def _after_lookup(state: State) -> str:
    return END if state.get("route") == "NOT_FOUND" else "dispatch_checks"


def dispatch_checks(state: State) -> dict:
    """Fan out to independent checks only after a claim record was found."""
    return {}


builder = StateGraph(State)
builder.add_node("parse_input", parse_input)
builder.add_node("lookup", lookup)
builder.add_node("dispatch_checks", dispatch_checks)
builder.add_node("check_window", check_window)
builder.add_node("check_quantity", check_quantity)
builder.add_node("check_duplicate", check_duplicate)
builder.add_node("check_invoice_ref", check_invoice_ref)
builder.add_node("check_batch_expiry", check_batch_expiry)
builder.add_node("check_value", check_value)
builder.add_node("check_pasted_fields", check_pasted_fields)
builder.add_node("decide", decide)
builder.add_node("explain", explain)
builder.add_edge(START, "parse_input")
builder.add_node("scheme_review", scheme_review)
builder.add_conditional_edges("parse_input", _after_parse, {"lookup": "lookup", "explain": "explain", "scheme_review": "scheme_review"})
builder.add_conditional_edges("scheme_review", _after_scheme, {"explain": "explain", END: END})
builder.add_conditional_edges("lookup", _after_lookup, {"dispatch_checks": "dispatch_checks", END: END})
# Fan out checks in one superstep, then wait for every independent check to finish.
CHECK_NODES = (
    "check_window", "check_quantity", "check_duplicate", "check_invoice_ref",
    "check_batch_expiry", "check_value", "check_pasted_fields",
)
for node in CHECK_NODES:
    builder.add_edge("dispatch_checks", node)
builder.add_edge(list(CHECK_NODES), "decide")
builder.add_edge("decide", "explain")
builder.add_edge("explain", END)
graph = builder.compile()

# Code-only review graph for batch mode: the same lookup, checks and decide nodes, with no
# parse or explain step, so a month of claims runs without any model call.
review_builder = StateGraph(State)
review_builder.add_node("lookup", lookup)
review_builder.add_node("dispatch_checks", dispatch_checks)
for node in CHECK_NODES:
    review_builder.add_node(node, globals()[node])
    review_builder.add_edge("dispatch_checks", node)
review_builder.add_node("decide", decide)
review_builder.add_edge(START, "lookup")
review_builder.add_conditional_edges("lookup", _after_lookup, {"dispatch_checks": "dispatch_checks", END: END})
review_builder.add_edge(list(CHECK_NODES), "decide")
review_builder.add_edge("decide", END)
review_graph = review_builder.compile()


def review_claim(claim_no: str) -> dict:
    """Route one register claim in code only (no model call); used by batch mode."""
    final = review_graph.invoke({
        "input_text": claim_no, "claim_no": claim_no, "email_id": "", "records": {}, "checks": {},
        "route": "", "explanation": "", "evidence": [], "model_calls": 0, "elapsed_seconds": 0.0,
        "scheme_target": "",
    })
    return {"route": final.get("route", "NEEDS_PERSON"), "checks": final.get("checks", {})}


def run_question(question: str) -> dict:
    """Run one input and return the structured route, checks, evidence, and timings."""
    started = time.perf_counter()
    final = graph.invoke({
        "input_text": question,
        "claim_no": "",
        "email_id": "",
        "records": {},
        "checks": {},
        "route": "",
        "explanation": "",
        "evidence": [],
        "model_calls": 0,
        "elapsed_seconds": 0.0,
        "scheme_target": "",
    })
    elapsed = time.perf_counter() - started
    return {
        "route": final.get("route", "NEEDS_PERSON"),
        "checks": final.get("checks", {}),
        "evidence": final.get("evidence", []),
        "explanation": final.get("explanation", ""),
        "answer": final.get("explanation", ""),
        "model_calls": final.get("model_calls", 0),
        "elapsed_seconds": round(elapsed, 3),
    }
