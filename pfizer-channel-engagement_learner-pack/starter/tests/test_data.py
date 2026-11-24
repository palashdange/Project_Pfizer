"""Coverage for cached CSV loading, exact deduplication, and typed lookups."""

from agent import data


def test_case_csv_row_counts_reflect_exact_deduplication():
    counts = data.row_counts()

    assert counts["primary_sales.csv"] == {
        "raw_rows": 93809,
        "clean_rows": 93064,
        "duplicates_removed": 745,
    }
    assert counts["expiry_claims.csv"] == {
        "raw_rows": 4526,
        "clean_rows": 4503,
        "duplicates_removed": 23,
    }
    assert counts["batch_master.csv"]["clean_rows"] == 663
    assert counts["claim_emails.csv"]["clean_rows"] == 30
    assert counts["cnf_stock_snapshot.csv"]["clean_rows"] == 5015
    assert counts["sku_master.csv"]["clean_rows"] == 36
    assert counts["stockist_master.csv"]["clean_rows"] == 156


def test_lookup_returns_none_when_key_is_not_found():
    assert data.get_claim("CLM-0000-00000") is None


def test_typed_lookups_return_provenance_for_each_master_and_evidence_type():
    claim = data.get_claim("CLM-2603-01616")

    assert claim is not None
    assert data.get_batch(claim["batch_no"])["source_file"] == "batch_master.csv"
    assert data.get_sku(claim["sku_code"])["source_file"] == "sku_master.csv"
    assert data.get_stockist(claim["stockist_code"])["source_file"] == "stockist_master.csv"
    assert data.sales_for(claim["stockist_code"], claim["batch_no"])
    assert data.credited_claims_for(claim["stockist_code"], claim["batch_no"])
    assert data.get_email("EML-017")["source_row"] == 28


def test_rows_keep_original_csv_source_row_after_deduplication():
    rows = data.rows_for("sales")

    assert rows is not None
    assert rows[0]["source_row"] == 2
    assert rows[0]["source_file"] == "primary_sales.csv"
