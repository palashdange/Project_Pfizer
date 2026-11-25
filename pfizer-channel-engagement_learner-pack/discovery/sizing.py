"""Reproducible sizing of the fictional Pfizer channel case.

Run from the learner-pack root with a Python environment that has pandas:
    python discovery/sizing.py

All rupee figures are historical exposure indicators or scenario run rates,
not confirmed savings. The CSV row references are one-based and include the
header, so the first data record is row 2.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "starter" / "data"
DEFAULT_OUTPUT = Path(__file__).resolve().with_name("sizing_results.csv")

FILE_NAMES = (
    "primary_sales.csv",
    "expiry_claims.csv",
    "batch_master.csv",
    "sku_master.csv",
    "cnf_stock_snapshot.csv",
    "stockist_master.csv",
    "claim_emails.csv",
)

RESULT_COLUMNS = [
    "problem",
    "inr_value",
    "period",
    "method",
    "source_rows_example",
    "policy_clause",
    "forecast_fixes",
]

EXPIRY_CLAIM_TYPES = {"NEAR EXPIRY", "EXPIRED"}


def normalize_code(value: Any, *, cfa: bool = False) -> str:
    """Normalize identifier whitespace/case; CFA identifiers also lose hyphens."""
    normalized = "" if value is None else str(value).strip().upper()
    return normalized.replace("-", "") if cfa else normalized


def parse_mixed_dates(values: pd.Series) -> pd.Series:
    """Parse the three date styles used in the case pack without guessing."""
    source = values.astype("string").str.strip()
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d-%b-%Y"):
        remaining = parsed.isna() & source.notna() & source.ne("")
        if remaining.any():
            parsed.loc[remaining] = pd.to_datetime(
                source.loc[remaining], format=fmt, errors="coerce"
            )
    return parsed


def _clean_file(path: Path) -> tuple[pd.DataFrame, int, int]:
    """Read text first so IDs and source row numbers remain exact and auditable."""
    raw = pd.read_csv(path, dtype="string", keep_default_na=False)
    raw_count = len(raw)
    duplicate_mask = raw.duplicated(keep="first")
    clean = raw.loc[~duplicate_mask].copy()
    # Preserve physical CSV row numbers before any filtering or sorting.
    clean["_source_row"] = clean.index + 2

    for column in clean.columns:
        if column.endswith("_code") or column in {
            "batch_no", "claim_no", "invoice_no", "credit_note_no",
            "original_invoice_ref",
        }:
            clean[column] = clean[column].map(normalize_code)
        if column == "cnf_code":
            clean[column] = clean[column].map(lambda value: normalize_code(value, cfa=True))
        if "date" in column.lower():
            clean[column] = parse_mixed_dates(clean[column])
    return clean.reset_index(drop=True), raw_count, int(duplicate_mask.sum())


def load_data(data_dir: Path, *, print_profile: bool = True) -> dict[str, pd.DataFrame]:
    """Load, exact-deduplicate, normalize, and profile every supplied CSV."""
    frames: dict[str, pd.DataFrame] = {}
    for filename in FILE_NAMES:
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required data file not found: {path}")
        frame, raw_count, duplicates = _clean_file(path)
        frames[filename] = frame
        if print_profile:
            print(f"{filename}: raw={raw_count:,}, exact_duplicates={duplicates:,}, clean={len(frame):,}")
            date_columns = [c for c in frame if "date" in c.lower()]
            if date_columns:
                for column in date_columns:
                    dates = frame[column].dropna()
                    if not dates.empty:
                        print(f"  {column}: {dates.min().date()} to {dates.max().date()}")
            else:
                print("  date range: no date column")
    return frames


def fiscal_quarter(dates: pd.Series) -> pd.Series:
    """Return fiscal quarter labels where Q1 is April through June."""
    month = dates.dt.month
    fiscal_year = (dates.dt.year + (month >= 4).astype("Int64")) % 100
    quarter = ((month - 4) % 12 // 3) + 1
    return "FY" + fiscal_year.astype("string").str.zfill(2) + " Q" + quarter.astype("string")


def _number(series: pd.Series) -> pd.Series:
    """Convert numeric columns that may contain display commas or currency marks."""
    cleaned = series.astype("string").str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace("₹", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


def _examples(rows: pd.DataFrame, filename: str, *, extra: str | None = None) -> str:
    """Return up to three source examples, retaining claim numbers where useful."""
    if rows.empty:
        return ""
    parts = []
    for _, row in rows.head(3).iterrows():
        item = f"{filename}:row {int(row['_source_row'])}"
        if extra and extra in row and str(row[extra]).strip():
            item += f" ({row[extra]})"
        parts.append(item)
    return "; ".join(parts)


def _months(frame: pd.DataFrame, date_column: str) -> int:
    dates = frame[date_column].dropna()
    return int(dates.dt.to_period("M").nunique())


def _period_rows(
    result_rows: list[dict[str, Any]],
    *,
    problem: str,
    grouped: dict[str, tuple[float, str]],
    total_months: int,
    policy: str,
    forecast: str,
    method_note: str,
) -> None:
    """Add quarterly observed values and one separate annualized run-rate row."""
    if total_months == 0:
        return
    for period, (amount, examples) in sorted(grouped.items()):
        result_rows.append({
            "problem": problem,
            "inr_value": round(float(amount), 2),
            "period": period,
            "method": f"Observed quarter; {method_note}",
            "source_rows_example": examples,
            "policy_clause": policy,
            "forecast_fixes": forecast,
        })
    full_period = sum(float(value[0]) for value in grouped.values())
    result_rows.append({
        "problem": problem,
        "inr_value": round(full_period * 12 / total_months, 2),
        "period": f"Annualized run-rate ({total_months} observed months)",
        "method": f"Observed total ₹{full_period:,.2f} ÷ {total_months} months × 12; {method_note}",
        "source_rows_example": "; ".join(
            [v[1] for v in grouped.values() if v[1]][:3]
        ),
        "policy_clause": policy,
        "forecast_fixes": forecast,
    })


def _fiscal_year_label(dates: pd.Series) -> pd.Series:
    """Return fiscal-year labels for April-March years."""
    month = dates.dt.month
    year = dates.dt.year + (month >= 4).astype("Int64")
    return "FY" + (year % 100).astype("string").str.zfill(2)


def calculate_driver_tables(
    sales: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize quarter-end concentration and CFA share/fill-rate drivers.

    Invoice date is the available transaction-date field. This does not prove
    physical dispatch timing or that all recorded orders remained valid demand.
    """
    dated_sales = sales.loc[sales["invoice_date"].notna()].copy()
    dated_sales["_quarter"] = fiscal_quarter(dated_sales["invoice_date"])
    dated_sales["_quarter_end"] = dated_sales["invoice_date"] + pd.offsets.QuarterEnd(0)
    dated_sales["_in_last_10_days"] = (
        dated_sales["invoice_date"] >= dated_sales["_quarter_end"] - pd.Timedelta(days=9)
    )
    dated_sales["_primary_packs"] = dated_sales["invoiced_qty"] + dated_sales["free_qty"]
    dated_sales["_free_value"] = dated_sales["free_qty"] * dated_sales["pts_inr"]

    quarter_rows = []
    for quarter, group in dated_sales.groupby("_quarter", sort=True):
        total_packs = float(group["_primary_packs"].sum())
        late_packs = float(group.loc[group["_in_last_10_days"], "_primary_packs"].sum())
        net_sales = float(group["net_value_inr"].sum())
        free_value = float(group["_free_value"].sum())
        quarter_rows.append({
            "period": str(quarter),
            "primary_packs": int(total_packs),
            "last_10_day_packs": int(late_packs),
            "last_10_day_share_pct": round(100 * late_packs / total_packs, 2) if total_packs else 0.0,
            "free_goods_value_inr": round(free_value, 2),
            "primary_net_value_inr": round(net_sales, 2),
            "foc_pct_of_primary_net_value": round(100 * free_value / net_sales, 2) if net_sales else 0.0,
        })
    quarter_end = pd.DataFrame(quarter_rows)

    # Use the same order grain as the existing fill-rate reconciliation.
    order_key = ["invoice_no", "invoice_date", "cnf_code", "stockist_code", "sku_code"]
    orders = dated_sales.groupby(order_key, dropna=False).agg(
        ordered_qty=("ordered_qty", "max"),
        invoiced_qty=("invoiced_qty", "sum"),
        free_qty=("free_qty", "sum"),
    ).reset_index()
    orders["fiscal_year"] = _fiscal_year_label(orders["invoice_date"])
    cfa_rows = []
    for fiscal_year, fy_orders in orders.groupby("fiscal_year", sort=True):
        fy_ordered_total = float(fy_orders["ordered_qty"].sum())
        for cfa, group in fy_orders.groupby("cnf_code", sort=True):
            ordered = float(group["ordered_qty"].sum())
            invoiced = float(group["invoiced_qty"].sum())
            free = float(group["free_qty"].sum())
            cfa_rows.append({
                "fiscal_year": str(fiscal_year),
                "cfa_code": str(cfa),
                "ordered_qty": int(ordered),
                "share_of_fy_ordered_qty_pct": round(100 * ordered / fy_ordered_total, 2) if fy_ordered_total else 0.0,
                "fill_rate_invoiced_only_pct": round(100 * invoiced / ordered, 2) if ordered else 0.0,
                "fill_rate_including_free_pct": round(100 * (invoiced + free) / ordered, 2) if ordered else 0.0,
            })
    return quarter_end, pd.DataFrame(cfa_rows)


def _quarterly_sum(
    frame: pd.DataFrame,
    date_column: str,
    amount_column: str,
    filename: str,
    *,
    mask: pd.Series | None = None,
    extra: str | None = None,
) -> dict[str, tuple[float, str]]:
    view = frame.loc[mask].copy() if mask is not None else frame.copy()
    view = view.loc[view[date_column].notna()].copy()
    if view.empty:
        return {}
    view["_quarter"] = fiscal_quarter(view[date_column])
    output: dict[str, tuple[float, str]] = {}
    for period, group in view.groupby("_quarter", sort=True):
        examples = _examples(group, filename, extra=extra)
        if extra and extra in group:
            examples = "; ".join(
                f"{filename}:row {int(row['_source_row'])} ({row[extra]})"
                for _, row in group.head(3).iterrows()
            )
        output[str(period)] = (float(group[amount_column].sum()), examples)
    return output


def _prepare(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    data = {key: value.copy() for key, value in frames.items()}
    for key, columns in {
        "primary_sales.csv": ["ordered_qty", "invoiced_qty", "free_qty", "pts_inr", "net_value_inr"],
        "expiry_claims.csv": ["qty_claimed", "claim_value_inr", "credit_value_inr"],
        "sku_master.csv": ["pts_inr"],
    }.items():
        for column in columns:
            data[key][column] = _number(data[key][column])
    return data


def calculate_sizing(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Calculate the requested risk views with explicit overlap treatment."""
    data = _prepare(frames)
    sales = data["primary_sales.csv"]
    claims = data["expiry_claims.csv"]
    batches = data["batch_master.csv"]
    skus = data["sku_master.csv"]

    sales["_quarter"] = fiscal_quarter(sales["invoice_date"])
    sales["_month"] = sales["invoice_date"].dt.to_period("M")
    claims["_quarter"] = fiscal_quarter(claims["claim_date"])
    claims["_month"] = claims["claim_date"].dt.to_period("M")
    sales_months = _months(sales, "invoice_date")
    claim_months = _months(claims, "claim_date")
    result_rows: list[dict[str, Any]] = []

    # The CFO's interview states a goal of bringing expiry returns back toward
    # 1% of sales. This is a target-gap screen, not a proven recoverable loss.
    expiry_claims = claims[
        claims["claim_type"].str.strip().str.upper().isin(EXPIRY_CLAIM_TYPES)
    ].copy()
    expiry_claims["_fiscal_year"] = _fiscal_year_label(expiry_claims["claim_date"])
    sales["_fiscal_year"] = _fiscal_year_label(sales["invoice_date"])
    fy_sales = sales.groupby("_fiscal_year")["net_value_inr"].sum()
    expiry_target_rows = []
    expiry_target_total = 0.0
    fy_keys = sorted(set(expiry_claims["_fiscal_year"].dropna().astype(str)) | set(fy_sales.index.astype(str)))
    for fy in fy_keys:
        claim_group = expiry_claims[expiry_claims["_fiscal_year"].astype("string").eq(fy)]
        claim_value = float(claim_group["claim_value_inr"].sum())
        primary_net = float(fy_sales.get(fy, 0.0))
        gap = max(0.0, claim_value - 0.01 * primary_net)
        expiry_target_total += gap
        examples = _examples(claim_group.sort_values("claim_value_inr", ascending=False), "expiry_claims.csv", extra="claim_no")
        sales_fy_rows = sales[sales["_fiscal_year"].astype("string").eq(fy)]
        if not sales_fy_rows.empty:
            sales_examples = _examples(sales_fy_rows.sort_values("net_value_inr", ascending=False), "primary_sales.csv")
            examples = "; ".join(part for part in [examples, sales_examples] if part)
        expiry_target_rows.append({
            "problem": "Expiry claims above 1% target (screen; not proven recoverable)",
            "inr_value": round(gap, 2),
            "period": fy,
            "method": (
                f"max(0, expiry claim_value_inr ₹{claim_value:,.2f} − 1% × primary net value ₹{primary_net:,.2f}); "
                "claims grouped by claim-date FY and compared with same-FY sales; not a matched shipment cohort"
            ),
            "source_rows_example": examples,
            "policy_clause": "CFO target stated in Doc 04 interview; not a CO-POL-014 threshold",
            "forecast_fixes": "partly, in principle — planning may influence future expiry, but no causal or recoverability amount is established.",
        })
    result_rows.extend(expiry_target_rows)
    # Use the complete claims-data coverage, including months with zero expiry
    # claims, so the run-rate does not inflate by dropping zero months.
    results_expiry_months = claim_months
    result_rows.append({
        "problem": "Expiry claims above 1% target (screen; not proven recoverable)",
        "inr_value": round(expiry_target_total * 12 / results_expiry_months, 2) if results_expiry_months else 0.0,
        "period": f"Annualized run-rate ({results_expiry_months} observed months)",
        "method": (
            f"Sum FY-specific positive gaps ₹{expiry_target_total:,.2f} ÷ {results_expiry_months} claim months × 12; "
            "claims are grouped by claim-date FY and compared with same-FY primary net value"
        ),
        "source_rows_example": "; ".join(row["source_rows_example"] for row in expiry_target_rows if row["source_rows_example"]),
        "policy_clause": "CFO target stated in Doc 04 interview; not a CO-POL-014 threshold",
        "forecast_fixes": "partly, in principle — planning may influence future expiry, but no causal or recoverability amount is established.",
    })

    # 1. FOC above quarterly policy cap, using source-line PTS and net sales.
    sales["_free_value"] = sales["free_qty"] * sales["pts_inr"]
    q1 = sales.groupby("_quarter").agg(
        free_value=("_free_value", "sum"), invoiced_value=("net_value_inr", "sum")
    )
    sales_examples: dict[str, str] = {}
    for period, group in sales[sales["free_qty"] > 0].groupby("_quarter"):
        sales_examples[str(period)] = _examples(group.sort_values("_free_value", ascending=False), "primary_sales.csv")
    free_goods: dict[str, tuple[float, str]] = {}
    for period, values in q1.iterrows():
        free_goods[str(period)] = (
            max(0.0, float(values.free_value - 0.03 * values.invoiced_value)),
            sales_examples.get(str(period), ""),
        )
    _period_rows(result_rows, problem="Free goods above 3% cap", grouped=free_goods,
                 total_months=sales_months, policy="CO-POL-014 §4.4", forecast="no — forecast does not enforce the scheme-spend cap.",
                 method_note="max(0, free_qty × PTS − 3% × net invoiced value)")

    # Prepare master joins and stable keys for the claims screens.
    batch_expiry = batches.set_index("batch_no")["expiry_date"].to_dict()
    batch_source_row = batches.set_index("batch_no")["_source_row"].to_dict()
    sku_pts = skus.set_index("sku_code")["pts_inr"].to_dict()
    sku_source_row = skus.set_index("sku_code")["_source_row"].to_dict()
    invoiced = sales.groupby(["stockist_code", "batch_no"], dropna=False).agg(
        billed_packs=("invoiced_qty", "sum"), free_packs=("free_qty", "sum")
    )
    invoice_dates: dict[str, pd.Timestamp] = {}
    if "invoice_no" in sales:
        invoice_groups = sales.dropna(subset=["invoice_date"]).groupby("invoice_no")
        invoice_dates = invoice_groups["invoice_date"].min().to_dict()
        invoice_rows = {key: group for key, group in invoice_groups}
    else:
        invoice_rows = {}

    credited = claims[claims["status"].str.strip().str.upper().isin({"CREDITED", "SETTLED", "APPROVED"})].copy()
    credited["_credit_value"] = credited["credit_value_inr"]
    credited["_credit_date_sort"] = credited["credit_note_date"].fillna(credited["claim_date"])
    # Identify each later credited event once, even when a key has 3+ credits.
    duplicate_mask = pd.Series(False, index=credited.index)
    duplicate_prior: dict[int, int] = {}
    duplicate_keyed = credited[
        credited["stockist_code"].astype("string").str.strip().ne("")
        & credited["batch_no"].astype("string").str.strip().ne("")
        & credited["qty_claimed"].gt(0)
    ]
    for _, group in duplicate_keyed.groupby(["stockist_code", "batch_no", "qty_claimed"], dropna=False):
        ordered = group.sort_values(["_credit_date_sort", "_source_row"])
        if len(ordered) > 1:
            first_index = ordered.index[0]
            for current_index in ordered.index[1:]:
                duplicate_mask.loc[current_index] = True
                duplicate_prior[current_index] = first_index
    duplicates = credited.loc[duplicate_mask].copy()
    duplicates["_priority_2_duplicate"] = True
    for period, group in duplicates.groupby("_quarter"):
        examples = []
        for idx, row in group.head(3).iterrows():
            prior = claims.loc[duplicate_prior[idx]]
            examples.append(
                f"expiry_claims.csv:row {int(prior['_source_row'])} {prior['claim_no']} ↔ "
                f"row {int(row['_source_row'])} {row['claim_no']}"
            )
        result_rows.append({
            "problem": "Potential duplicate credits (match candidates)",
            "inr_value": round(float(group["_credit_value"].sum()), 2),
            "period": str(period),
            "method": "Later credited value for repeated stockist + batch + claimed quantity; each later credit counted once.",
            "source_rows_example": "; ".join(examples),
            "policy_clause": "CO-POL-014 §5.6",
            "forecast_fixes": "no — forecast does not detect or prevent duplicate credit notes.",
        })
    duplicate_periods = set(str(x) for x in claims["_quarter"].dropna().unique())
    for period in sorted(duplicate_periods):
        if not any(r["problem"] == "Potential duplicate credits (match candidates)" and r["period"] == period for r in result_rows):
            result_rows.append({"problem": "Potential duplicate credits (match candidates)", "inr_value": 0.0, "period": period,
                                "method": "No later credited duplicate found under stockist + batch + quantity.",
                                "source_rows_example": "", "policy_clause": "CO-POL-014 §5.6",
                                "forecast_fixes": "no — forecast does not detect or prevent duplicate credit notes."})
    duplicate_total = float(duplicates["_credit_value"].sum())
    result_rows.append({
        "problem": "Potential duplicate credits (match candidates)",
        "inr_value": round(duplicate_total * 12 / claim_months, 2) if claim_months else 0,
        "period": f"Annualized run-rate ({claim_months} observed months)",
        "method": f"Observed later-credit total ₹{duplicate_total:,.2f} ÷ {claim_months} claim months × 12; one identified pattern is evidence of an event, not a stable future loss rate.",
        "source_rows_example": "; ".join([r["source_rows_example"] for r in result_rows if r["problem"] == "Potential duplicate credits (match candidates)" and r["source_rows_example"]][:3]),
        "policy_clause": "CO-POL-014 §5.6",
        "forecast_fixes": "no — forecast does not detect or prevent duplicate credit notes.",
    })

    # Priority 3: policy-window breaches. Claim-type-specific windows follow §5.2.
    expiry_claim_types = {"NEAR EXPIRY", "EXPIRED"}
    claim_expiry = claims["batch_no"].map(batch_expiry)
    claims["_master_expiry"] = claim_expiry
    claims["_invoice_date"] = claims["original_invoice_ref"].map(invoice_dates)
    claims["_outside_window"] = False
    near = claims["claim_type"].str.strip().str.upper().eq("NEAR EXPIRY")
    expired = claims["claim_type"].str.strip().str.upper().eq("EXPIRED")
    near_valid = near & claims["_master_expiry"].notna()
    expired_valid = expired & claims["_master_expiry"].notna()
    claims.loc[near_valid, "_outside_window"] = (
        (claims.loc[near_valid, "claim_date"] < claims.loc[near_valid, "_master_expiry"] - pd.Timedelta(days=90)) |
        (claims.loc[near_valid, "claim_date"] > claims.loc[near_valid, "_master_expiry"])
    ).to_numpy()
    claims.loc[expired_valid, "_outside_window"] = (
        (claims.loc[expired_valid, "claim_date"] < claims.loc[expired_valid, "_master_expiry"]) |
        (claims.loc[expired_valid, "claim_date"] > claims.loc[expired_valid, "_master_expiry"] + pd.Timedelta(days=90))
    ).to_numpy()
    short_types = claims["claim_type"].str.strip().str.upper().isin({"BREAKAGE IN TRANSIT", "SHORT SUPPLY"})
    short_valid = short_types & claims["_invoice_date"].notna()
    claims.loc[short_valid, "_outside_window"] = (
        claims.loc[short_valid, "claim_date"] > claims.loc[short_valid, "_invoice_date"] + pd.Timedelta(days=7)
    ).to_numpy()
    claims["_window_credited_candidate"] = claims["_outside_window"] & claims["status"].str.strip().str.upper().isin({"CREDITED", "SETTLED", "APPROVED"})
    claims["_priority_3_window"] = claims["_window_credited_candidate"] & ~claims.index.isin(duplicates.index)
    window_candidates = claims[claims["_window_credited_candidate"]].copy()
    window_rows = claims[claims["_priority_3_window"]].copy()
    window_groups = _quarterly_sum(window_rows, "claim_date", "credit_value_inr", "expiry_claims.csv", extra="claim_no")
    for period, group in window_rows.groupby("_quarter"):
        example_rows = []
        for _, claim in group.head(3).iterrows():
            evidence = f"expiry_claims.csv:row {int(claim['_source_row'])} ({claim['claim_no']})"
            claim_type = str(claim["claim_type"]).strip().upper()
            if claim_type in expiry_claim_types:
                if claim["batch_no"] in batch_source_row:
                    evidence += f"; batch_master.csv:row {int(batch_source_row[claim['batch_no']])} ({claim['batch_no']})"
            else:
                matched_lines = invoice_rows.get(claim["original_invoice_ref"])
                if matched_lines is not None and not matched_lines.empty:
                    line = matched_lines.iloc[0]
                    evidence += f"; primary_sales.csv:row {int(line['_source_row'])} ({line['invoice_no']})"
            example_rows.append(evidence)
        window_groups[str(period)] = (window_groups[str(period)][0], "; ".join(example_rows))
    for period in claims["_quarter"].dropna().astype(str).unique():
        window_groups.setdefault(period, (0.0, ""))
    _period_rows(result_rows, problem="Credited claims outside policy window", grouped=window_groups,
                 total_months=claim_months, policy="CO-POL-014 §5.2", forecast="no — a forecast does not enforce claim eligibility windows.",
                 method_note="credited claims only; expiry from batch master; type-specific §5.2 date windows")

    # Priority 4: over-quantity claims, net of prior higher-priority screens.
    over_records = []
    for idx, row in claims.iterrows():
        key = (row["stockist_code"], row["batch_no"])
        if not row["stockist_code"] or not row["batch_no"] or key not in invoiced.index:
            continue
        billed = float(invoiced.loc[key, "billed_packs"] + invoiced.loc[key, "free_packs"])
        excess = max(0.0, float(row["qty_claimed"]) - billed)
        if excess <= 0:
            continue
        amount = excess * float(sku_pts.get(row["sku_code"], 0))
        if amount <= 0:
            continue
        record = row.copy()
        record["_over_qty_value"] = amount
        record["_excess_packs"] = excess
        record["_claim_index"] = idx
        over_records.append(record)
    over_candidates = pd.DataFrame(over_records)
    if not over_candidates.empty:
        over_candidates.index = pd.Index(over_candidates["_claim_index"].astype(int))
    over_candidate_indices = set(over_candidates.index) if not over_candidates.empty else set()
    over = over_candidates.loc[
        ~over_candidates.index.isin(duplicates.index)
        & ~over_candidates.index.isin(window_candidates.index)
    ].copy() if not over_candidates.empty else over_candidates
    over_groups = _quarterly_sum(over, "claim_date", "_over_qty_value", "expiry_claims.csv", extra="claim_no") if not over.empty else {}
    if not over.empty:
        for period, group in over.groupby("_quarter"):
            example_rows = []
            for _, claim in group.head(3).iterrows():
                evidence = f"expiry_claims.csv:row {int(claim['_source_row'])} ({claim['claim_no']})"
                matched_sales = sales[
                    sales["stockist_code"].eq(claim["stockist_code"])
                    & sales["batch_no"].eq(claim["batch_no"])
                ]
                evidence += "; " + ", ".join(
                    f"primary_sales.csv:row {int(line['_source_row'])} ({line['invoice_no']})"
                    for _, line in matched_sales.head(3).iterrows()
                )
                if claim["sku_code"] in sku_source_row:
                    evidence += f"; sku_master.csv:row {int(sku_source_row[claim['sku_code']])} ({claim['sku_code']} PTS)"
                example_rows.append(evidence)
            over_groups[str(period)] = (over_groups[str(period)][0], "; ".join(example_rows))
    for period in claims["_quarter"].dropna().astype(str).unique():
        over_groups.setdefault(period, (0.0, ""))
    _period_rows(result_rows, problem="Over-quantity claims (excess packs × PTS)", grouped=over_groups,
                 total_months=claim_months, policy="CO-POL-014 §5.5", forecast="no — forecast does not reconcile claimed packs to invoiced packs.",
                 method_note="all statuses; excess = claimed packs − total invoiced and free packs for stockist + batch, valued at SKU PTS")

    # Priority 5: blank-reference credits after checks 2-4.
    credited_indices = set(credited.index)
    excluded = set(duplicates.index) | set(window_rows.index) | set(over.index if not over.empty else [])
    no_invoice = claims.loc[
        claims.index.isin(credited_indices)
        & claims["original_invoice_ref"].astype("string").str.strip().eq("")
        & ~claims.index.isin(excluded)
    ].copy()
    missing_groups = _quarterly_sum(no_invoice, "claim_date", "credit_value_inr", "expiry_claims.csv", extra="claim_no")
    for period in claims["_quarter"].dropna().astype(str).unique():
        missing_groups.setdefault(period, (0.0, ""))
    _period_rows(result_rows, problem="Credited claims without invoice reference — value at risk", grouped=missing_groups,
                 total_months=claim_months, policy="CO-POL-014 §5.4", forecast="no — invoice-reference validation is a claims-control task.",
                 method_note="credited value; mutually exclusive residual after duplicate, window, and over-quantity priorities; blank reference is not proof of invalidity")

    # 6. Cross-cut diagnostic, deliberately not added to the financial total.
    short_pairs = set()
    short_pair_details: dict[tuple[str, str], pd.Series] = {}
    bm = batches.set_index("batch_no")
    invoice_with_batch = sales[sales["batch_no"].astype("string").str.strip().ne("")].copy()
    invoice_with_batch["_mfg"] = invoice_with_batch["batch_no"].map(bm["mfg_date"])
    invoice_with_batch["_expiry"] = invoice_with_batch["batch_no"].map(bm["expiry_date"])
    total_days = (invoice_with_batch["_expiry"] - invoice_with_batch["_mfg"]).dt.days
    remaining_days = (invoice_with_batch["_expiry"] - invoice_with_batch["invoice_date"]).dt.days
    invoice_with_batch["_rsl_pct"] = remaining_days.div(total_days.where(total_days > 0)) * 100
    for _, row in invoice_with_batch.loc[invoice_with_batch["_rsl_pct"] < 60].iterrows():
        key = (row["stockist_code"], row["batch_no"])
        short_pairs.add(key)
        short_pair_details.setdefault(key, row)
    expiry_claims = claims[
        claims["claim_type"].str.strip().str.upper().isin(expiry_claim_types)
        & claims["status"].str.strip().str.upper().isin({"CREDITED", "SETTLED", "APPROVED"})
        & claims.apply(lambda row: (row["stockist_code"], row["batch_no"]) in short_pairs, axis=1)
    ].copy()
    short_rsl_groups = _quarterly_sum(expiry_claims, "claim_date", "credit_value_inr", "expiry_claims.csv", extra="claim_no")
    for period, group in expiry_claims.groupby("_quarter"):
        example_rows = []
        for _, claim in group.head(3).iterrows():
            evidence = f"expiry_claims.csv:row {int(claim['_source_row'])} ({claim['claim_no']})"
            source_line = short_pair_details.get((claim["stockist_code"], claim["batch_no"]))
            if source_line is not None:
                evidence += f"; primary_sales.csv:row {int(source_line['_source_row'])} ({source_line['invoice_no']}, RSL {source_line['_rsl_pct']:.2f}%)"
            if claim["batch_no"] in batch_source_row:
                evidence += f"; batch_master.csv:row {int(batch_source_row[claim['batch_no']])} ({claim['batch_no']})"
            example_rows.append(evidence)
        short_rsl_groups[str(period)] = (short_rsl_groups[str(period)][0], "; ".join(example_rows))
    for period in claims["_quarter"].dropna().astype(str).unique():
        short_rsl_groups.setdefault(period, (0.0, ""))
    _period_rows(result_rows, problem="Expiry claims on stockist-batches with a <60% RSL invoice", grouped=short_rsl_groups,
                 total_months=claim_months, policy="CO-POL-014 §5.2 and §7.1", forecast="no — forecasting does not stop short-RSL dispatch; this overlaps claim categories and is non-additive.",
                 method_note="cross-cut diagnostic; credited Near expiry/Expired claims with same stockist + batch as any <60% RSL invoice")

    # 7. Shipment availability signals. Free packs count as shipped units in the
    # QBR fill-rate reconciliation, so the primary shortfall subtracts them too.
    # Keep the invoiced-only gap as a separate, overlapping billing diagnostic.
    sales_order = sales[sales["invoice_date"].notna()].copy()
    order_key = ["invoice_no", "invoice_date", "cnf_code", "stockist_code", "sku_code"]
    orders = sales_order.groupby(order_key, dropna=False).agg(
        ordered_qty=("ordered_qty", "max"), invoiced_qty=("invoiced_qty", "sum"),
        free_qty=("free_qty", "sum"),
        pts_inr=("pts_inr", "first"), source_rows=("_source_row", list)
    ).reset_index()
    orders["_uncovered_qty"] = (
        orders["ordered_qty"] - orders["invoiced_qty"] - orders["free_qty"]
    ).clip(lower=0)
    orders["_uncovered_value"] = orders["_uncovered_qty"] * orders["pts_inr"]
    orders["_invoice_only_gap_value"] = (
        orders["ordered_qty"] - orders["invoiced_qty"]
    ).clip(lower=0) * orders["pts_inr"]
    orders["_quarter"] = fiscal_quarter(orders["invoice_date"])
    cfa_months = sales_order.groupby("cnf_code").apply(
        lambda group: _months(group, "invoice_date"), include_groups=False
    ).to_dict()
    for cfa, cfa_rows in orders.groupby("cnf_code"):
        all_cfa_periods = sales_order.loc[sales_order["cnf_code"].eq(cfa), "_quarter"].dropna().astype(str).unique()
        for metric, problem, method in (
            ("_uncovered_value", f"Unfilled-order pack value after free goods — {cfa}",
             "max(ordered_qty − summed invoiced_qty − summed free_qty, 0) × PTS; free packs treated as shipped fulfillment; value is a screening proxy, not lost sales"),
            ("_invoice_only_gap_value", f"Invoiced-only gap before free goods — {cfa} (non-additive)",
             "max(ordered_qty − summed invoiced_qty, 0) × PTS; overlapping diagnostic because free packs may fulfill the order"),
        ):
            grouped = {}
            positive = cfa_rows[cfa_rows[metric] > 0]
            for period, group in positive.groupby("_quarter"):
                examples = []
                for _, row in group.head(3).iterrows():
                    source_refs = ", ".join(str(int(source_row)) for source_row in row["source_rows"])
                    examples.append(f"primary_sales.csv:rows {source_refs} ({row['invoice_no']})")
                grouped[str(period)] = (float(group[metric].sum()), "; ".join(examples))
            for period in all_cfa_periods:
                grouped.setdefault(period, (0.0, ""))
            _period_rows(result_rows, problem=problem, grouped=grouped,
                     total_months=int(cfa_months.get(cfa, 0)), policy="— (order gap signal; not a policy breach)",
                     forecast="no as a stand-alone forecast — the national forecast is split by a separate allocation decision; order status and demand remain unverified.",
                     method_note=f"{method}; aggregate grain is invoice + stockist + SKU + CFA + date")

    # 8. Process performance, not rupees. Include all valid claims by quarter.
    time_rows = claims.dropna(subset=["claim_date", "credit_note_date"]).copy()
    time_rows["_days_to_credit"] = (time_rows["credit_note_date"] - time_rows["claim_date"]).dt.days
    for period in sorted(str(x) for x in claims["_quarter"].dropna().unique()):
        group = time_rows[time_rows["_quarter"].astype("string").eq(period)]
        median = float(group["_days_to_credit"].median()) if not group.empty else float("nan")
        over30 = int((group["_days_to_credit"] > 30).sum())
        example = _examples(group.sort_values("_days_to_credit", ascending=False), "expiry_claims.csv", extra="claim_no")
        result_rows.append({
            "problem": "Claims processing time (days; not INR)",
            "inr_value": "",
            "period": period,
            "method": f"{len(group)} claims with both dates; median={median:.1f} days; {over30} over 30 days. Claim date used as recorded; no separate received timestamp.",
            "source_rows_example": example,
            "policy_clause": "CO-POL-014 §5.6",
            "forecast_fixes": "no — forecasting does not shorten claim verification or credit-note processing.",
        })
    median = float(time_rows["_days_to_credit"].median()) if not time_rows.empty else float("nan")
    over30_total = int((time_rows["_days_to_credit"] > 30).sum())
    result_rows.append({
        "problem": "Claims processing time (days; not INR)", "inr_value": "",
        "period": f"All observed ({claim_months} months)",
        "method": f"{len(time_rows)} claims with both dates; median={median:.1f} days; {over30_total} over 30 days. No annualization for a rate/time KPI.",
        "source_rows_example": _examples(time_rows.sort_values("_days_to_credit", ascending=False), "expiry_claims.csv", extra="claim_no"),
        "policy_clause": "CO-POL-014 §5.6",
        "forecast_fixes": "no — forecasting does not shorten claim verification or credit-note processing.",
    })

    # Count overlaps before applying the mutually-exclusive priority buckets.
    priority_candidates = claims[claims["status"].str.strip().str.upper().isin({"CREDITED", "SETTLED", "APPROVED"})].copy()
    duplicate_set = set(duplicates.index)
    outside_set = set(window_candidates.index)
    over_set = over_candidate_indices
    no_ref_set = set(claims.index[claims.index.isin(credited_indices) & claims["original_invoice_ref"].astype("string").str.strip().eq("")])
    overlap = {
        "credited_claims": len(priority_candidates),
        "duplicate_credit_later_records": len(duplicate_set),
        "outside_window_credited_records": len(outside_set),
        "over_quantity_records_before_priority": len(over_set),
        "credited_blank_reference_after_priority": len(no_ref_set),
        "duplicate_and_window_candidates": len(duplicate_set & outside_set),
        "duplicate_and_over_quantity_candidates": len(duplicate_set & over_set),
        "window_and_over_quantity_candidates": len(outside_set & over_set),
        "duplicate_or_window_or_over_quantity_candidates": len(duplicate_set | outside_set | over_set),
        "credited_blank_invoice_candidates_before_priority": len(no_ref_set),
        "credited_blank_invoice_candidates_after_priority": len(no_invoice),
    }

    results = pd.DataFrame(result_rows, columns=RESULT_COLUMNS)
    annual_rows = results[results["period"].astype("string").str.startswith("Annualized")]
    availability_problem_size = float(annual_rows.loc[
        annual_rows["problem"].str.startswith("Unfilled-order pack value after free goods"), "inr_value"
    ].sum())
    invoice_only_gap = float(results.loc[
        results["period"].astype("string").str.startswith("Annualized")
        & results["problem"].str.startswith("Invoiced-only gap before free goods"), "inr_value"
    ].sum())
    q1_sales = sales[sales["_quarter"].eq("FY27 Q1")]
    q1_free_pct = float(q1_sales["_free_value"].sum() / q1_sales["net_value_inr"].sum() * 100) if q1_sales["net_value_inr"].sum() else 0.0
    q1_orders = sales_order[sales_order["_quarter"].eq("FY27 Q1")].groupby(order_key, dropna=False).agg(
        ordered_qty=("ordered_qty", "max"), invoiced_qty=("invoiced_qty", "sum")
    )
    q1_fill_rate = float(q1_orders["invoiced_qty"].sum() / q1_orders["ordered_qty"].sum() * 100) if q1_orders["ordered_qty"].sum() else 0.0
    q1_fill_rate_with_free = float(
        (q1_orders["invoiced_qty"].sum() + q1_sales.loc[q1_sales["_quarter"].eq("FY27 Q1"), "free_qty"].sum())
        / q1_orders["ordered_qty"].sum() * 100
    ) if q1_orders["ordered_qty"].sum() else 0.0
    quarter_end_concentration, cfa_mix = calculate_driver_tables(sales)
    # Exclude the order-gap proxy as requested. Available evidence does not
    # validate any rupee amount as directly recoverable through forecasting.
    summary = {
        "sales_observed_months": sales_months,
        "claims_observed_months": claim_months,
        "availability_problem_size_annualized_inr": availability_problem_size,
        "invoice_only_gap_annualized_diagnostic_inr": invoice_only_gap,
        "fy27_q1_free_goods_pct": q1_free_pct,
        "fy27_q1_fill_rate_by_sizing_method_pct": q1_fill_rate,
        "fy27_q1_fill_rate_including_free_pct": q1_fill_rate_with_free,
        "expiry_claims_above_1pct_target_annualized_inr": round(expiry_target_total * 12 / results_expiry_months, 2) if results_expiry_months else 0.0,
        "expiry_target_gap_observed_inr": round(expiry_target_total, 2),
        "forecast_share_of_quantified_recoverable_inr_pct": 0.0,
        "forecast_share_status": "0% demonstrated from available data; no forecast-linked recoverable rupee amount is established.",
        "quarter_end_concentration": quarter_end_concentration,
        "cfa_order_mix_and_fill": cfa_mix,
        "overlaps": overlap,
    }
    return results, summary


def calculate_gst_credit_note_timing(frames: dict[str, pd.DataFrame], *, deadline_month: int = 11,
                                     deadline_day: int = 30) -> tuple[dict[str, Any], pd.DataFrame]:
    """Credited claims whose credit note is dated after the CGST §34(2) window of the original invoice.

    The window ends on `deadline_day`/`deadline_month` following the 31 March that closes the
    invoice's financial year (30 November in the text as amended by the Finance Act 2022, which
    could not be read at source; pass month 9, day 30 for the as-enacted September limit).
    """
    data = _prepare(frames)
    claims = data["expiry_claims.csv"]
    sales = data["primary_sales.csv"]
    credited = claims[claims["status"].astype("string").str.strip().str.upper().eq("CREDITED")].copy()
    credited["_ref"] = credited["original_invoice_ref"].astype("string").str.strip().str.upper()
    first_invoice = (sales.assign(_ref=sales["invoice_no"].astype("string").str.strip().str.upper())
                     .dropna(subset=["invoice_date"]).drop_duplicates("_ref")[["_ref", "invoice_date"]])
    joined = credited.merge(first_invoice, on="_ref", how="inner")
    joined = joined.dropna(subset=["credit_note_date"])
    fy_end_year = joined["invoice_date"].dt.year + (joined["invoice_date"].dt.month > 3).astype(int)
    deadline = pd.to_datetime(dict(year=fy_end_year, month=deadline_month, day=deadline_day))
    joined["_late"] = joined["credit_note_date"] > deadline
    late = joined[joined["_late"]]
    months = _months(claims, "claim_date")
    total = float(joined["credit_value_inr"].sum())
    late_value = float(late["credit_value_inr"].sum())
    by_type = (joined.groupby("claim_type")
               .apply(lambda g: pd.Series({
                   "credited": len(g), "late": int(g["_late"].sum()),
                   "late_value_share_pct": round(float(g.loc[g["_late"], "credit_value_inr"].sum() / g["credit_value_inr"].sum() * 100), 1)
                   if g["credit_value_inr"].sum() else 0.0}), include_groups=False)
               .reset_index())
    row = {
        "problem": "Credit notes issued after the CGST §34(2) window (GST may not be reversible; not sized)",
        "inr_value": round(late_value * 12 / months, 2) if months else 0.0,
        "period": f"Annualized run-rate ({months} observed months)",
        "method": (f"{len(late)} of {len(joined)} credited claims with a matched invoice reference have credit_note_date after "
                   f"{deadline_day:02d}-{deadline_month:02d} following the invoice FY end; late credit value ₹{late_value:,.2f} "
                   f"of ₹{total:,.2f} ({late_value / total * 100:.1f}%) ÷ {months} months × 12. Credited value, not GST amount."),
        "source_rows_example": _examples(late.sort_values("credit_value_inr", ascending=False), "expiry_claims.csv", extra="claim_no"),
        "policy_clause": "CGST Act 2017 §34(2); CO-POL-014 §5.7",
        "forecast_fixes": "no — timing follows shelf life and claim filing, not the forecast.",
    }
    return row, by_type


def calculate_register_controls(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Signs in the claims register that the C&F checks (C&F SOP 2.6) were not recorded.

    SOP step 4 requires the physical verification result in the remarks column; a credited claim
    with blank remarks has no recorded result. Overlaps the other claim screens; not additive.
    """
    data = _prepare(frames)
    claims = data["expiry_claims.csv"]
    status = claims["status"].astype("string").str.strip().str.upper()
    remarks = claims["remarks"].astype("string").fillna("").str.strip()
    credited = claims[status.eq("CREDITED")]
    blank = credited[remarks[status.eq("CREDITED")].eq("")]
    months = _months(claims, "claim_date")
    blank_value = float(blank["credit_value_inr"].sum())
    no_invoice = credited[credited["original_invoice_ref"].astype("string").fillna("").str.strip().eq("")]
    counts = {
        "credited": int(len(credited)),
        "rejected": int(status.eq("REJECTED").sum()),
        "rejected_remarks": remarks[status.eq("REJECTED")].value_counts().to_dict(),
        "credited_blank_remarks": int(len(blank)),
        "credited_blank_remarks_with_verifier_name": int(blank["verified_by"].astype("string").fillna("").str.strip().ne("").sum()),
        "credited_no_invoice_by_remark": no_invoice["remarks"].astype("string").fillna("").str.strip().value_counts().to_dict(),
    }
    row = {
        "problem": "Credited claims with no recorded C&F verification result (blank remarks; overlaps other screens)",
        "inr_value": round(blank_value * 12 / months, 2) if months else 0.0,
        "period": f"Annualized run-rate ({months} observed months)",
        "method": (f"{len(blank)} of {len(credited)} credited claims have blank remarks although C&F SOP 2.6 step 4 requires the "
                   f"verification result there; credit value ₹{blank_value:,.2f} ÷ {months} months × 12. Not additive."),
        "source_rows_example": _examples(blank.sort_values("credit_value_inr", ascending=False), "expiry_claims.csv", extra="claim_no"),
        "policy_clause": "C&F agreement SC-AGR-CF-003 Schedule 2 §2.6",
        "forecast_fixes": "no — a forecast does not record verification.",
    }
    return row, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="CSV directory (default: starter/data)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="CSV output path (default: discovery/sizing_results.csv)")
    args = parser.parse_args()

    frames = load_data(args.data_dir)
    results, summary = calculate_sizing(frames)
    gst_row, gst_by_type = calculate_gst_credit_note_timing(frames)
    control_row, control_counts = calculate_register_controls(frames)
    results = pd.concat([results, pd.DataFrame([gst_row, control_row], columns=RESULT_COLUMNS)], ignore_index=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)

    print("\nSizing results (quarterly observations and separate annualized run rates):")
    with pd.option_context("display.max_rows", None, "display.width", 120):
        # Provenance and full formulas remain in the CSV; keep the terminal
        # review table compact enough to scan without losing the period/value.
        print(results[["problem", "inr_value", "period"]].to_string(index=False))
    print("\nClaim screen overlap counts (priority categories 2 > 3 > 4 > 5):")
    for name, count in summary["overlaps"].items():
        print(f"  {name}: {count:,}")
    print("\nWhat would a forecast recover?")
    print("  Availability problem size (upper bound, not lost sales; excluded from recoverability share): "
          f"₹{summary['availability_problem_size_annualized_inr']:,.2f}")
    print("  Overlapping invoiced-only gap before free packs (excluded from denominator): "
          f"₹{summary['invoice_only_gap_annualized_diagnostic_inr']:,.2f}")
    print(f"  Share of quantified recoverable rupees attributable to forecasting: {summary['forecast_share_of_quantified_recoverable_inr_pct']:.1f}% demonstrated; actual recoverability is not measurable from these extracts.")
    print(f"  Expiry-claims-above-target screen that planning might influence: ₹{summary['expiry_claims_above_1pct_target_annualized_inr']:,.2f}/year, but no causal attribution is established.")
    print("\nWhy it may be happening — descriptive signals, not causal proof:")
    print("Quarter-end primary pack concentration and FOC by FY quarter:")
    print(summary["quarter_end_concentration"].to_string(index=False))
    print("\nCFA order share and fill rate by fiscal year (free packs included in displayed fill rate):")
    print(summary["cfa_order_mix_and_fill"].to_string(index=False))
    print("\nQBR reconciliation checks (case-pack figures, Q1 FY27):")
    print(f"  FOC / primary sales from extracts: {summary['fy27_q1_free_goods_pct']:.2f}% (QBR: 3.69%)")
    print(f"  Invoice quantity / ordered quantity: {summary['fy27_q1_fill_rate_by_sizing_method_pct']:.2f}%; including free packs: {summary['fy27_q1_fill_rate_including_free_pct']:.2f}% (QBR: 90.9%). Including free packs nearly reconciles; confirm the official numerator/denominator and whether free packs count as fulfillment.")
    print("\nCredit notes after the CGST §34(2) window (30 Nov after invoice FY end), by claim type:")
    print(gst_by_type.to_string(index=False))
    print(f"  {gst_row['method']}")
    print("\nClaims register controls (C&F SOP 2.6):")
    for name, value in control_counts.items():
        print(f"  {name}: {value}")
    print(f"  {control_row['method']}")
    print(f"\nWrote {len(results):,} rows to {args.output}")


if __name__ == "__main__":
    main()
