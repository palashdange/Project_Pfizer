"""Stock and expiry-risk review for the Head of Supply Chain, all in code.

One run covers one month-end snapshot (default: the latest) across every C&F:
- Expiry risk (CO-POL-014 §7.1-7.2): with first-expiry-first-out picking at the current rolling
  outward rate, packs that cannot leave before 60 days to expiry (blocked, written off) and packs
  that will be below 60% of shelf life when they ship (stockist may refuse). Valued at PTS.
- Cover (C&F agreement §2.2): out-of-stock lines, and lines above the 2-month top-up norm.
- FEFO signal (clause 6.3): share of dispatch lines in the 3 months to the snapshot that shipped a
  later-expiry batch while an earlier one was on hand at the previous month-end. Needs monthly
  snapshots (from Mar 2026); a signal for a person to check, not proof.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from statistics import median
from typing import Optional

from agent import data
from agent.rules import dispatch_deadlines, fefo_packs_at_risk, months_of_cover, parse_date
from config import (
    DAYS_PER_MONTH, FEFO_SIGNAL_MULTIPLE, STOCK_COVER_POLICY_CLAUSE, STOCK_EXPIRY_POLICY_CLAUSE,
    STOCK_FEFO_POLICY_CLAUSE,
)

EXAMPLES = 8


def _d(value) -> Decimal:
    try:
        return Decimal(str(value or "0").replace(",", "").strip() or "0")
    except InvalidOperation:
        return Decimal("0")


def _cfa_label(code: str) -> str:
    return f"{code[:2]}-{code[2:]}" if code and "-" not in code else code


def _money(value: Decimal) -> str:
    return format(Decimal(value).quantize(Decimal("0.01")), "f")


@lru_cache(maxsize=1)
def _snapshots() -> dict:
    """Snapshot rows grouped by date, then by (C&F, SKU)."""
    grouped: dict[date, dict] = defaultdict(lambda: defaultdict(list))
    for row in data.rows_for("snapshot") or []:
        try:
            day = parse_date(row.get("snapshot_date", ""))
        except ValueError:
            continue
        grouped[day][(row.get("cnf_code"), row.get("sku_code"))].append(row)
    return {day: dict(groups) for day, groups in grouped.items()}


def available_snapshots() -> list[str]:
    return [day.strftime("%d-%m-%Y") for day in sorted(_snapshots())]


def _shelf_life_days(batch_no: str, sku: dict) -> int:
    batch = data.get_batch(batch_no) or {}
    try:
        return (parse_date(batch.get("expiry_date", "")) - parse_date(batch.get("mfg_date", ""))).days
    except ValueError:
        return round(int(_d(sku.get("shelf_life_months"))) * DAYS_PER_MONTH)


@lru_cache(maxsize=1)
def _oldest_on_hand() -> dict:
    """Earliest expiry on hand per (month, C&F, SKU) from each month-end snapshot."""
    oldest = {}
    for day, groups in _snapshots().items():
        for key, rows in groups.items():
            expiries = []
            for row in rows:
                if (row.get("batch_no") or "").strip() and _d(row.get("qty_on_hand_packs")) > 0:
                    try:
                        expiries.append(parse_date(row.get("expiry_date", "")))
                    except ValueError:
                        pass
            if expiries:
                oldest[(day.year, day.month) + key] = min(expiries)
    return oldest


def _fefo_shares(as_of: date) -> Optional[dict]:
    """Per C&F: dispatch lines in the 3 months to `as_of` that skipped an older on-hand batch."""
    months = []
    year, month = as_of.year, as_of.month
    for _ in range(3):
        months.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    oldest = _oldest_on_hand()
    previous = {m: ((m[0], m[1] - 1) if m[1] > 1 else (m[0] - 1, 12)) for m in months}
    if not all(any(k[:2] == previous[m] for k in oldest) for m in months):
        return None  # a previous month-end snapshot is missing (quarterly snapshots before Mar 2026)
    counts: dict[str, list] = defaultdict(lambda: [0, 0, None])
    for row in data.rows_for("sales") or []:
        if not (row.get("batch_no") or "").strip():
            continue
        try:
            day = parse_date(row.get("invoice_date", ""))
        except ValueError:
            continue
        if (day.year, day.month) not in months:
            continue
        prior = oldest.get(previous[(day.year, day.month)] + (row.get("cnf_code"), row.get("sku_code")))
        batch = data.get_batch(row.get("batch_no", ""))
        if prior is None or not batch:
            continue
        try:
            shipped = parse_date(batch.get("expiry_date", ""))
        except ValueError:
            continue
        item = counts[row.get("cnf_code")]
        item[0] += 1
        if shipped > prior:
            item[1] += 1
            if item[2] is None:
                item[2] = row.get("source_row")
    return {cfa: {"lines": n, "skipped": k, "share": Decimal(k) / n if n else Decimal("0"), "example_row": ex}
            for cfa, (n, k, ex) in counts.items()}


def review_stock(snapshot: Optional[str] = None) -> Optional[dict]:
    """Review one month-end snapshot across all C&Fs; None if the date is not in the extract."""
    snapshots = _snapshots()
    if snapshot:
        try:
            as_of = parse_date(snapshot)
        except ValueError:
            return None
        if as_of not in snapshots:
            return None
    else:
        as_of = max(snapshots)
    skus = {row["sku_code"]: row for row in data.rows_for("sku") or []}
    by_cfa: dict[str, dict] = defaultdict(lambda: {
        "city": "", "short_shelf_life_inr": Decimal("0"), "block_inr": Decimal("0"),
        "out_of_stock": 0, "above_norm": 0, "lines": 0})
    batches_at_risk = []
    for (cfa, sku_code), rows in snapshots[as_of].items():
        sku = skus.get(sku_code, {})
        pts = _d(sku.get("pts_inr"))
        rate = _d(rows[0].get("avg_monthly_outward_packs"))
        summary = by_cfa[cfa]
        summary["city"] = rows[0].get("cnf_city", "")
        summary["lines"] += 1
        stock = []
        for row in rows:
            if (row.get("batch_no") or "").strip() and _d(row.get("qty_on_hand_packs")) > 0:
                try:
                    stock.append((parse_date(row.get("expiry_date", "")), _d(row.get("qty_on_hand_packs")), row))
                except ValueError:
                    continue
        cover = months_of_cover(sum((q for _, q, _ in stock), Decimal("0")), rate)
        if cover["status"] == "out_of_stock":
            summary["out_of_stock"] += 1
            continue
        if cover["status"] == "above_norm":
            summary["above_norm"] += 1
        stock.sort(key=lambda item: item[0])
        deadlines = [dispatch_deadlines(expiry, _shelf_life_days(row.get("batch_no", ""), sku)) for expiry, _, row in stock]
        pairs = [(expiry, packs) for expiry, packs, _ in stock]
        short = fefo_packs_at_risk(pairs, rate, as_of, "short_shelf_life", deadlines)
        block = fefo_packs_at_risk(pairs, rate, as_of, "block", deadlines)
        for (expiry, packs, row), short_packs, block_packs in zip(stock, short, block):
            summary["short_shelf_life_inr"] += short_packs * pts
            summary["block_inr"] += block_packs * pts
            if short_packs > 0:
                batches_at_risk.append({
                    "cfa": _cfa_label(cfa), "sku_code": sku_code, "product": sku.get("product_description", ""),
                    "batch_no": row.get("batch_no"), "expiry_date": row.get("expiry_date"),
                    "on_hand_packs": format(packs, "f"), "monthly_outward_packs": format(rate, "f"),
                    "packs_at_risk": format(short_packs, "f"), "blocked_packs": format(block_packs, "f"),
                    "value_at_risk_inr": _money(short_packs * pts),
                    "source": f"cnf_stock_snapshot.csv:{row.get('source_row')}",
                    "_value": short_packs * pts, "_row": row,
                })
    batches_at_risk.sort(key=lambda item: -item["_value"])
    short_total = sum((v["short_shelf_life_inr"] for v in by_cfa.values()), Decimal("0"))
    block_total = sum((v["block_inr"] for v in by_cfa.values()), Decimal("0"))
    out_total = sum(v["out_of_stock"] for v in by_cfa.values())
    above_total = sum(v["above_norm"] for v in by_cfa.values())
    lines_total = sum(v["lines"] for v in by_cfa.values())
    worst_short = max(by_cfa, key=lambda c: by_cfa[c]["short_shelf_life_inr"])
    worst_out = max(by_cfa, key=lambda c: by_cfa[c]["out_of_stock"])
    cite = lambda items: [{"file": "cnf_stock_snapshot.csv", "source_row": i["_row"].get("source_row"),
                           "record_id": i["batch_no"]} for i in items[:5]]

    checks = {
        "short_shelf_life": {
            "status": "fail" if short_total > 0 else "pass",
            "reason": (f"{_money(short_total)} at PTS across {len(batches_at_risk)} batch(es) will ship below the 60% "
                       f"shelf-life norm at the current outward rate, so stockists may refuse them (not a write-off); "
                       f"largest at {_cfa_label(worst_short)} ({_money(by_cfa[worst_short]['short_shelf_life_inr'])})."),
            "policy_clause": STOCK_EXPIRY_POLICY_CLAUSE, "evidence_rows": cite(batches_at_risk),
            "value_inr": _money(short_total),
        },
        "expiry_block": {
            "status": "fail" if block_total > 0 else "pass",
            "reason": f"{_money(block_total)} at PTS will reach 60 days to expiry before it can ship, then be blocked and written off.",
            "policy_clause": STOCK_EXPIRY_POLICY_CLAUSE,
            "evidence_rows": cite([b for b in batches_at_risk if _d(b["blocked_packs"]) > 0]),
            "value_inr": _money(block_total),
        },
        "out_of_stock": {
            "status": "fail" if out_total else "pass",
            "reason": (f"{out_total} of {lines_total} C&F-SKU lines are out of stock; most at {_cfa_label(worst_out)} "
                       f"({by_cfa[worst_out]['out_of_stock']} of {by_cfa[worst_out]['lines']})."),
            "policy_clause": STOCK_COVER_POLICY_CLAUSE, "evidence_rows": [], "lines": out_total,
        },
        "above_norm": {
            "status": "fail" if above_total else "pass",
            "reason": f"{above_total} of {lines_total} C&F-SKU lines hold more than 2 months of cover at the current outward rate.",
            "policy_clause": STOCK_COVER_POLICY_CLAUSE, "evidence_rows": [], "lines": above_total,
        },
    }
    fefo = _fefo_shares(as_of)
    if fefo is None:
        checks["fefo_signal"] = {
            "status": "missing", "policy_clause": STOCK_FEFO_POLICY_CLAUSE, "evidence_rows": [],
            "reason": "Not available: snapshots before Mar 2026 are quarterly, so the previous month-end stock is unknown.",
        }
    else:
        flagged = []
        for cfa, item in fefo.items():
            others = [v["share"] for c, v in fefo.items() if c != cfa]
            if others and item["share"] >= Decimal(str(FEFO_SIGNAL_MULTIPLE)) * Decimal(str(median(others))):
                flagged.append(cfa)
        shares = "; ".join(f"{_cfa_label(c)} {v['share'] * 100:.1f}% of {v['lines']}" for c, v in sorted(fefo.items()))
        checks["fefo_signal"] = {
            "status": "fail" if flagged else "pass",
            "reason": (f"Dispatch lines in the 3 months to {as_of:%d-%m-%Y} that shipped a later-expiry batch while an earlier "
                       f"one was on hand: {shares}. " + (f"Flagged: {', '.join(_cfa_label(c) for c in flagged)} "
                       "(at least twice the other C&Fs' median). A signal to check the WMS picking rules, not proof."
                       if flagged else "No C&F stands out.")),
            "policy_clause": STOCK_FEFO_POLICY_CLAUSE,
            "evidence_rows": [{"file": "primary_sales.csv", "source_row": fefo[c]["example_row"], "record_id": _cfa_label(c)}
                              for c in flagged if fefo[c]["example_row"]],
            "flagged": [_cfa_label(c) for c in flagged],
        }
    route = "STOCK_NEEDS_ACTION" if any(c["status"] == "fail" for c in checks.values()) else "STOCK_OK"
    cfa_rows = [{
        "cfa": _cfa_label(c), "city": v["city"], "short_shelf_life_inr": _money(v["short_shelf_life_inr"]),
        "block_inr": _money(v["block_inr"]), "out_of_stock": v["out_of_stock"], "above_norm": v["above_norm"],
        "lines": v["lines"],
        "fefo_skip_pct": f"{fefo[c]['share'] * 100:.1f}" if fefo and c in fefo else None,
    } for c, v in sorted(by_cfa.items())]
    top = [{k: v for k, v in b.items() if not k.startswith("_")} for b in batches_at_risk[:EXAMPLES]]
    return {"snapshot": as_of.strftime("%d-%m-%Y"), "route": route, "checks": checks,
            "by_cfa": cfa_rows, "top_batches": top}
