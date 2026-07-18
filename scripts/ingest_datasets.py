"""
scripts/ingest_datasets.py
===========================
Loads address-table1.csv and address-table2.csv into PostgreSQL:

  1. Verbatim into staging tables (mirrors source structure 1:1):
       staging_table1_county_street
       staging_table2_city_address
     -> run database/migrations/003_source_datasets.sql first.

  2. Cleaned + flattened into the production `raw_addresses` table that the
     NestJS backend / ML service actually read from, with:
       source_system    = 'table1_county_street' | 'table2_city_address'
       source_record_id = stable id referencing the staging row
       raw_text          = a single address string built from the source columns

This does NOT call the ML service or write canonical_addresses/standardization_results --
those are populated when the backend's POST /addresses/standardize endpoint (or a batch
caller) processes each raw_addresses row. This script's only job is getting the source
data safely into the database.

USAGE
-----
    pip install psycopg2-binary pandas python-dotenv
    export DATABASE_URL=postgresql://addruser:addrpass@localhost:5432/address_db
    python scripts/ingest_datasets.py \
        --table1 ml-service/data/raw/address-table1.csv \
        --table2 ml-service/data/raw/address-table2.csv

Re-running is safe: staging tables are append-only with a row_number for traceability,
but raw_addresses inserts are skipped if an identical (source_system, source_record_id)
pair already exists (see `_already_ingested`).
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

import pandas as pd
import psycopg2
import psycopg2.extras


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: set DATABASE_URL, e.g.")
        print("  export DATABASE_URL=postgresql://addruser:addrpass@localhost:5432/address_db")
        sys.exit(1)
    return psycopg2.connect(database_url)


def clean_street_nbr(value):
    value = (value or "").strip() if isinstance(value, str) else ""
    if not value:
        return ""
    m = re.match(r"^(\d+)", value)
    return m.group(1) if m else ""


def clean_zip5(value):
    value = (value or "").strip() if isinstance(value, str) else ""
    if re.fullmatch(r"\d{5}", value) and value != "00000":
        return value
    return ""


# ──────────────────────────────────────────────────────────────────────────
def ingest_table1(conn, csv_path: str) -> dict:
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    n_in_file = len(df)

    # Append-only staging insert (verbatim, including duplicates/junk -- the
    # staging table is the audit copy of "what we received")
    records = list(df.itertuples(index=False, name=None))
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO staging_table1_county_street
               (county_name, street_nbr, street_name, zip5, row_number)
               VALUES %s""",
            [(r[0], r[1], r[2], r[3], i + 1) for i, r in enumerate(records)],
        )
    rows_inserted_staging = len(records)

    # Clean for raw_addresses: drop dup rows, drop unusable house numbers / empty streets
    df = df.drop_duplicates()
    df["street_nbr_clean"] = df["street_nbr"].apply(clean_street_nbr)
    df["zip5_clean"] = df["zip5"].apply(clean_zip5)
    skip_reasons = {
        "duplicate_rows": int(n_in_file - len(df)),
        "missing_street_name": int((df["street_name"].str.strip() == "").sum()),
        "unusable_house_number": int((df["street_nbr_clean"] == "").sum()),
    }
    df = df[(df["street_name"].str.strip() != "") & (df["street_nbr_clean"] != "")]

    raw_rows = []
    for idx, row in df.iterrows():
        raw_text = f"{row['street_nbr_clean']} {row['street_name'].strip()}"
        if row["zip5_clean"]:
            raw_text += f" {row['zip5_clean']}"
        source_record_id = f"t1-{idx}"
        parsed_components = json.dumps({
            "county_name": row["county_name"],
            "street_nbr": row["street_nbr_clean"],
            "street_name": row["street_name"],
            "zip5": row["zip5_clean"] or None,
        })
        raw_rows.append((raw_text, "table1_county_street", source_record_id, parsed_components))

    rows_inserted_raw = _insert_raw_addresses(conn, raw_rows)

    return {
        "rows_in_file": n_in_file,
        "rows_inserted_staging": rows_inserted_staging,
        "rows_inserted_raw_addresses": rows_inserted_raw,
        "rows_skipped": n_in_file - rows_inserted_raw,
        "skip_reasons": skip_reasons,
    }


def ingest_table2(conn, csv_path: str) -> dict:
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    n_in_file = len(df)

    records = list(df.itertuples(index=False, name=None))
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO staging_table2_city_address
               (city, county_or_parish, state_or_province, address, short_address, row_number)
               VALUES %s""",
            [(r[0], r[1], r[2], r[3], r[4], i + 1) for i, r in enumerate(records)],
        )
    rows_inserted_staging = len(records)

    df_clean = df.drop_duplicates()
    sentinel_mask = df_clean["address"].str.contains("99999", regex=False) | (
        df_clean["city"].str.lower() == "out-of state"
    )
    skip_reasons = {
        "duplicate_rows": int(n_in_file - len(df_clean)),
        "sentinel_or_out_of_state": int(sentinel_mask.sum()),
    }
    df_clean = df_clean[~sentinel_mask]

    raw_rows = []
    for idx, row in df_clean.iterrows():
        raw_text = row["address"].strip()
        source_record_id = f"t2-{idx}"
        parsed_components = json.dumps({
            "city": row["city"],
            "county_or_parish": row["countyOrParish"],
            "state_or_province": row["stateOrProvince"],
            "short_address": row["shortAddress"],
        })
        raw_rows.append((raw_text, "table2_city_address", source_record_id, parsed_components))

    rows_inserted_raw = _insert_raw_addresses(conn, raw_rows)

    return {
        "rows_in_file": n_in_file,
        "rows_inserted_staging": rows_inserted_staging,
        "rows_inserted_raw_addresses": rows_inserted_raw,
        "rows_skipped": n_in_file - rows_inserted_raw,
        "skip_reasons": skip_reasons,
    }


def _insert_raw_addresses(conn, raw_rows: list) -> int:
    """Inserts into raw_addresses, skipping rows whose (source_system, source_record_id)
    already exist (idempotent re-runs)."""
    if not raw_rows:
        return 0
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO raw_addresses (raw_text, source_system, source_record_id, parsed_components)
               VALUES %s
               ON CONFLICT DO NOTHING""",
            raw_rows,
            template="(%s, %s, %s, %s::jsonb)",
        )
        return cur.rowcount


def _log_ingestion(conn, source_file: str, stats: dict, started_at: datetime):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO ingestion_log
               (source_file, rows_in_file, rows_inserted_staging, rows_inserted_raw_addresses,
                rows_skipped, skip_reasons, started_at, finished_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                source_file,
                stats["rows_in_file"],
                stats["rows_inserted_staging"],
                stats["rows_inserted_raw_addresses"],
                stats["rows_skipped"],
                json.dumps(stats["skip_reasons"]),
                started_at,
                datetime.now(timezone.utc),
            ),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table1", default="ml-service/data/raw/address-table1.csv")
    parser.add_argument("--table2", default="ml-service/data/raw/address-table2.csv")
    args = parser.parse_args()

    conn = get_connection()
    try:
        # Note: raw_addresses doesn't have a unique constraint on
        # (source_system, source_record_id) out of the box -- add one if you plan
        # to re-run this script repeatedly against the same data:
        #   ALTER TABLE raw_addresses ADD CONSTRAINT uq_raw_addr_source
        #     UNIQUE (source_system, source_record_id);

        t0 = datetime.now(timezone.utc)
        stats1 = ingest_table1(conn, args.table1)
        _log_ingestion(conn, os.path.basename(args.table1), stats1, t0)

        t1 = datetime.now(timezone.utc)
        stats2 = ingest_table2(conn, args.table2)
        _log_ingestion(conn, os.path.basename(args.table2), stats2, t1)

        conn.commit()
        print("address-table1.csv:", json.dumps(stats1, indent=2))
        print("address-table2.csv:", json.dumps(stats2, indent=2))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
