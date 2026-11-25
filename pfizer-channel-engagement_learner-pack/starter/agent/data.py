"""Cached, normalized access to the case CSVs with source-row provenance."""

import csv
from functools import lru_cache
from pathlib import Path
from typing import Optional, TypedDict


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class SourceRow(TypedDict, total=False):
    """A CSV record enriched with its original file and physical row number."""

    source_file: str
    source_row: int


_FILES = {
    "claim": "expiry_claims.csv",
    "batch": "batch_master.csv",
    "sku": "sku_master.csv",
    "stockist": "stockist_master.csv",
    "sales": "primary_sales.csv",
    "email": "claim_emails.csv",
    "snapshot": "cnf_stock_snapshot.csv",
}

_CODE_FIELDS = {
    "claim_no", "batch_no", "sku_code", "stockist_code", "cnf_code",
    "cfa_code", "email_id", "invoice_no", "original_invoice_ref",
}


def _normalize_row(row: dict) -> dict:
    """Normalize identifiers for matching while retaining other source values."""
    normalized = dict(row)
    for field in _CODE_FIELDS:
        if field in normalized and normalized[field] is not None:
            normalized[field] = normalized[field].strip().upper()
            # CFA and SKU aliases such as CF-E01/CFE01 and PFL-1303/PFL1303 must resolve to the same key
            # (143 claim rows write the SKU with a hyphen).
            if field in {"cnf_code", "cfa_code", "sku_code"}:
                normalized[field] = normalized[field].replace("-", "")
    return normalized


@lru_cache(maxsize=None)
def _read_csv(filename: str, data_dir: Path) -> tuple[tuple[dict, ...], int]:
    """Read once, remove exact duplicates, and keep the first physical source row."""
    path = data_dir / filename
    records = []
    seen = set()
    raw_count = 0
    with path.open(newline="", encoding="utf-8-sig") as source:
        for source_row, row in enumerate(csv.DictReader(source), start=2):
            raw_count += 1
            signature = tuple(row.items())
            if signature in seen:
                continue
            seen.add(signature)
            records.append(_normalize_row({
                **row,
                "source_file": filename,
                "source_row": source_row,
            }))
    return tuple(records), raw_count


def rows_for(dataset: str, data_dir: Path = DATA_DIR) -> Optional[list[SourceRow]]:
    """Return copied deduplicated rows for a named dataset, or None if absent."""
    filename = _FILES.get(dataset)
    if filename is None or not (data_dir / filename).is_file():
        return None
    rows, _ = _read_csv(filename, Path(data_dir))
    # Copy cached records so callers cannot mutate shared cache state.
    return [dict(row) for row in rows]  # type: ignore[return-value]


def row_counts(data_dir: Path = DATA_DIR) -> dict[str, dict[str, int]]:
    """Report raw and exact-deduplicated data-row counts for available CSVs."""
    counts = {}
    for dataset, filename in _FILES.items():
        if not (data_dir / filename).is_file():
            continue
        rows, raw_count = _read_csv(filename, Path(data_dir))
        counts[filename] = {
            "raw_rows": raw_count,
            "clean_rows": len(rows),
            "duplicates_removed": raw_count - len(rows),
        }
    return counts


def missing_files(filenames: tuple[str, ...], data_dir: Path = DATA_DIR) -> list[str]:
    """List absent required files without making tools responsible for file reads."""
    return [name for name in filenames if not (data_dir / name).is_file()]


@lru_cache(maxsize=None)
def _index(dataset: str, fields: tuple[str, ...], data_dir: Path) -> dict[tuple, tuple[dict, ...]]:
    """Group a dataset's cached rows by key fields once, keeping file order within each key."""
    filename = _FILES.get(dataset)
    if filename is None or not (data_dir / filename).is_file():
        return {}
    rows, _ = _read_csv(filename, Path(data_dir))
    grouped: dict[tuple, list[dict]] = {}
    for row in rows:
        grouped.setdefault(tuple(row.get(field) for field in fields), []).append(row)
    return {key: tuple(value) for key, value in grouped.items()}


def _lookup(dataset: str, fields: tuple[str, ...], values: tuple[str, ...], data_dir: Path) -> list[SourceRow]:
    """Return copies of the rows matching normalized key values, in file order."""
    key = tuple(value.strip().upper() if isinstance(value, str) else "" for value in values)
    return [dict(row) for row in _index(dataset, fields, Path(data_dir)).get(key, ())]  # type: ignore[misc]


def _find(dataset: str, field: str, value: str, data_dir: Path) -> Optional[SourceRow]:
    if not isinstance(value, str) or not value.strip():
        return None
    matches = _lookup(dataset, (field,), (value,), data_dir)
    return matches[0] if matches else None


def get_claim(claim_no: str, data_dir: Path = DATA_DIR) -> Optional[SourceRow]:
    """Find one claim by its normalized claim number."""
    return _find("claim", "claim_no", claim_no, data_dir)


def get_batch(batch_no: str, data_dir: Path = DATA_DIR) -> Optional[SourceRow]:
    """Find one batch-master record by batch number."""
    return _find("batch", "batch_no", batch_no, data_dir)


def get_sku(sku_code: str, data_dir: Path = DATA_DIR) -> Optional[SourceRow]:
    """Find one product-master record by SKU code."""
    return _find("sku", "sku_code", sku_code, data_dir)


def get_stockist(code: str, data_dir: Path = DATA_DIR) -> Optional[SourceRow]:
    """Find one stockist-master record by stockist code."""
    return _find("stockist", "stockist_code", code, data_dir)


def sales_for(stockist: str, batch: str, data_dir: Path = DATA_DIR) -> Optional[list[SourceRow]]:
    """Find deduplicated sales rows for a stockist and batch, or None."""
    return _lookup("sales", ("stockist_code", "batch_no"), (stockist, batch), data_dir) or None


def credited_claims_for(stockist: str, batch: str, data_dir: Path = DATA_DIR) -> Optional[list[SourceRow]]:
    """Find credited claim rows for a stockist/batch, or None if there are none."""
    matches = [
        row for row in _lookup("claim", ("stockist_code", "batch_no"), (stockist, batch), data_dir)
        if (row.get("status") or "").casefold() == "credited"
        and bool((row.get("credit_note_no") or "").strip())
    ]
    return matches or None


def claims_for(stockist: str, batch: str, data_dir: Path = DATA_DIR) -> Optional[list[SourceRow]]:
    """Find every claim row, in any status, for a stockist/batch, or None if there are none."""
    return _lookup("claim", ("stockist_code", "batch_no"), (stockist, batch), data_dir) or None


def get_email(email_id: str, data_dir: Path = DATA_DIR) -> Optional[SourceRow]:
    """Find one claim-email record by email ID."""
    return _find("email", "email_id", email_id, data_dir)
