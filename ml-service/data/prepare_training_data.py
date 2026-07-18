"""
prepare_training_data.py
=========================
Builds the LightGBM training corpus from the user's two real datasets:

  data/raw/address-table1.csv  -> county_name, street_nbr, street_name, zip5
  data/raw/address-table2.csv  -> city, countyOrParish, stateOrProvince, address, shortAddress

It replaces `generate_data.py` (synthetic Google/NYC-style addresses) as the source of
`training_data.csv`. The legacy generator is left in place for reference / fallback only.

WHAT THIS SCRIPT DOES
----------------------
1. Cleans each source file (drops unusable rows, dedupes, fixes obvious corruption).
2. Builds (raw_address, canonical_address, is_correct) pairs:
     - table2 rows already contain a clean, human-verified `address` -> used as the
       canonical/ground-truth address. A noisy "raw" counterpart is synthetically generated
       from it (abbreviations, dropped zip, case changes, typos) -> label 1.
     - table1 rows have NO city/state, only county + street + zip. City is IMPUTED from
       table2's zip->city / county->city lookup (NY only). This is an assumption, not
       ground truth, and is flagged in the data quality report.
     - Negative pairs (label 0) are created by cross-pairing a raw address from one record
       with the canonical address of an unrelated record.
3. Splits the pairs into:
     - data/training_data.csv        (85% -- consumed by app/retraining.py, which further
                                        splits 80/20 internally for its own train/val report)
     - data/validation_holdout.csv   (15% -- NEVER touched during training; used by
                                        validate.py to measure true generalization)
4. Writes data/data_quality_report.json documenting every row dropped/imputed and why.

USAGE
-----
    cd ml-service
    python data/prepare_training_data.py

Re-run any time the raw CSVs in data/raw/ change.
"""
import csv
import json
import os
import random
import re

import pandas as pd

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_TABLE1 = os.path.join(HERE, "raw", "address-table1.csv")
RAW_TABLE2 = os.path.join(HERE, "raw", "address-table2.csv")
OUT_TRAINING = os.path.join(HERE, "training_data.csv")
OUT_HOLDOUT = os.path.join(HERE, "validation_holdout.csv")
OUT_REPORT = os.path.join(HERE, "data_quality_report.json")

HOLDOUT_FRACTION = 0.15
NEGATIVE_PAIR_FRACTION = 0.15  # negatives as a fraction of total positive pairs

# Kept in sync with ml-service/app/standardizer.py so synthetic noise uses the same vocabulary
SUFFIX_FULL_TO_ABBR = {
    "street": ["St", "St."], "avenue": ["Ave", "Ave."], "road": ["Rd", "Rd."],
    "lane": ["Ln", "Ln."], "drive": ["Dr", "Dr."], "court": ["Ct", "Ct."],
    "place": ["Pl", "Pl."], "boulevard": ["Blvd", "Blvd."], "parkway": ["Pkwy", "Pkwy."],
    "way": ["Wy"], "terrace": ["Ter", "Ter."],
}
SUFFIX_ABBR_TO_FULL = {
    "dr": "Drive", "dr.": "Drive", "rd": "Road", "rd.": "Road", "st": "Street", "st.": "Street",
    "ave": "Avenue", "ave.": "Avenue", "ln": "Lane", "ln.": "Lane", "ct": "Court", "ct.": "Court",
    "pl": "Place", "pl.": "Place", "blvd": "Boulevard", "blvd.": "Boulevard",
    "pkwy": "Parkway", "pkwy.": "Parkway", "wy": "Way", "ter": "Terrace", "ter.": "Terrace",
    "rt": "Route", "rte": "Route",
}
DIRECTIONAL_FULL_TO_ABBR = {
    "north": "N", "south": "S", "east": "E", "west": "W",
    "northeast": "NE", "northwest": "NW", "southeast": "SE", "southwest": "SW",
}


def log_section(report: dict, key: str, value):
    report[key] = value


# ──────────────────────────────────────────────────────────────────────────
# Noise generation (used to fabricate a "raw" input from a clean canonical one)
# ──────────────────────────────────────────────────────────────────────────
def noisify_address(canonical: str) -> str:
    text = canonical

    # 1. Abbreviate a street suffix word if present (case-insensitive whole-word)
    for full, abbrs in SUFFIX_FULL_TO_ABBR.items():
        pattern = re.compile(rf"\b{full}\b", re.IGNORECASE)
        if pattern.search(text) and random.random() < 0.7:
            text = pattern.sub(random.choice(abbrs), text, count=1)
            break

    # 2. Abbreviate a leading/embedded directional word
    for full, abbr in DIRECTIONAL_FULL_TO_ABBR.items():
        pattern = re.compile(rf"\b{full}\b", re.IGNORECASE)
        if pattern.search(text) and random.random() < 0.5:
            text = pattern.sub(abbr, text, count=1)
            break

    # 3. Drop the ZIP code ~20% of the time
    if random.random() < 0.20:
        text = re.sub(r"\s*\d{5}(-\d{4})?\s*$", "", text)

    # 4. Mangle state casing/format ~40% of the time, e.g. "NY" -> "ny" or "N.Y."
    m = re.search(r",\s*([A-Z]{2})(\s|$)", text)
    if m and random.random() < 0.4:
        state = m.group(1)
        variant = random.choice([state.lower(), f"{state[0]}.{state[1]}."])
        text = text[: m.start(1)] + variant + text[m.end(1):]

    # 5. Random comma removal (people often type addresses without commas)
    if random.random() < 0.25:
        text = text.replace(",", "", 1)

    # 6. Single-character transposition typo ~12% of the time
    if random.random() < 0.12 and len(text) > 10:
        idx = random.randint(2, len(text) - 3)
        text = text[:idx] + text[idx + 1] + text[idx] + text[idx + 2:]

    return text.strip()


def expand_street_token(token: str) -> str:
    key = token.lower().strip(".")
    if key in SUFFIX_ABBR_TO_FULL:
        return SUFFIX_ABBR_TO_FULL[key]
    if key in DIRECTIONAL_FULL_TO_ABBR.values() or key in {"n", "s", "e", "w"}:
        rev = {v.lower(): k for k, v in DIRECTIONAL_FULL_TO_ABBR.items()}
        return rev.get(key, token).capitalize()
    return token.capitalize()


def expand_street_name(raw_street: str) -> str:
    """'OAKWOOD DR' -> 'Oakwood Drive', 'RT 9' -> 'Route 9'"""
    tokens = raw_street.strip().split()
    return " ".join(expand_street_token(t) for t in tokens)


# ──────────────────────────────────────────────────────────────────────────
# Table 2: city, countyOrParish, stateOrProvince, address, shortAddress
# ──────────────────────────────────────────────────────────────────────────
def load_and_clean_table2(report: dict) -> pd.DataFrame:
    df = pd.read_csv(RAW_TABLE2, dtype=str).fillna("")
    n_raw = len(df)

    dup_count = int(df.duplicated().sum())
    df = df.drop_duplicates()

    # Sentinel/garbage rows: placeholder ZIP 99999 / "Out-of State" city are not real NY addresses
    bad_mask = df["address"].str.contains(r"99999", regex=True) | (df["city"].str.lower() == "out-of state")
    n_bad = int(bad_mask.sum())
    df = df[~bad_mask].copy()

    # Build a zip -> city lookup (used later to impute city for table1)
    zip_match = df["address"].str.extract(r"(\d{5})\s*$")[0]
    df["_zip"] = zip_match
    zip_to_city = (
        df[df["_zip"] != ""]
        .drop_duplicates(subset="_zip")
        .set_index("_zip")["city"]
        .to_dict()
    )
    county_to_cities = df.groupby("countyOrParish")["city"].apply(lambda s: sorted(set(s))).to_dict()
    all_cities = sorted(df["city"].unique().tolist())

    report["table2"] = {
        "rows_loaded": n_raw,
        "exact_duplicates_dropped": dup_count,
        "sentinel_or_out_of_state_rows_dropped": n_bad,
        "rows_kept": len(df),
        "note": "address column treated as ground-truth canonical (already human-clean); "
                "noisy raw counterpart is synthetically generated.",
    }
    return df.drop(columns=["_zip"]), zip_to_city, county_to_cities, all_cities


def build_pairs_from_table2(df: pd.DataFrame) -> list:
    pairs = []
    for _, row in df.iterrows():
        canonical = row["address"].strip()
        if not canonical:
            continue
        raw = noisify_address(canonical)
        # Guarantee raw != canonical isn't required (a clean input is a valid case too)
        pairs.append((raw, canonical, 1, "table2"))
    return pairs


# ──────────────────────────────────────────────────────────────────────────
# Table 1: county_name, street_nbr, street_name, zip5  (no city/state!)
# ──────────────────────────────────────────────────────────────────────────
def clean_street_nbr(value: str) -> str:
    """Returns a usable house number string, or '' if unusable.
    Handles ranges ('75-81'), multi-values ('115, 109'), Excel date corruption
    ('09-Nov' from a typed '9-11'), and junk ('OFF').
    NOTE: returns '' rather than None on purpose -- pandas' nullable string dtype
    silently turns None into the literal text "nan" under .apply(), which then
    leaks into output strings. Empty-string is the safe sentinel for "missing"."""
    value = (value or "").strip()
    if not value:
        return ""
    m = re.match(r"^(\d+)", value)
    if m:
        return m.group(1)
    return ""  # e.g. "OFF", "09-Nov" with no leading digit -> unusable


def clean_zip5(value: str) -> str:
    value = (value or "").strip()
    if re.fullmatch(r"\d{5}", value) and value != "00000":
        return value
    return ""


def load_and_clean_table1(report: dict) -> pd.DataFrame:
    df = pd.read_csv(RAW_TABLE1, dtype=str).fillna("")
    n_raw = len(df)

    dup_count = int(df.duplicated().sum())
    df = df.drop_duplicates()

    missing_street_name = int((df["street_name"].str.strip() == "").sum())
    df = df[df["street_name"].str.strip() != ""].copy()

    df["street_nbr_clean"] = df["street_nbr"].apply(clean_street_nbr)
    unusable_nbr = int((df["street_nbr_clean"] == "").sum())
    df = df[df["street_nbr_clean"] != ""].copy()

    df["zip5_clean"] = df["zip5"].apply(clean_zip5)
    missing_zip = int((df["zip5_clean"] == "").sum())

    report["table1"] = {
        "rows_loaded": n_raw,
        "exact_duplicates_dropped": dup_count,
        "rows_missing_street_name_dropped": missing_street_name,
        "rows_with_unusable_house_number_dropped": unusable_nbr,
        "rows_kept": len(df),
        "rows_missing_zip5_kept_anyway": missing_zip,
        "note": "No city/state in source. City is IMPUTED via table2's zip->city / "
                "county->city lookup (state assumed 'NY'). This is an assumption, not "
                "verified ground truth -- treat table1-derived canonicals as weaker labels.",
    }
    return df


def build_pairs_from_table1(df: pd.DataFrame, zip_to_city: dict, county_to_cities: dict, all_cities: list) -> list:
    pairs = []
    for _, row in df.iterrows():
        house_num = row["street_nbr_clean"]
        raw_street = row["street_name"].strip()
        zip5 = row["zip5_clean"]
        county = row["county_name"].strip()

        # Impute city: zip match > county match > random NY city
        city = None
        if zip5 and zip5 in zip_to_city:
            city = zip_to_city[zip5]
        elif county in county_to_cities and county_to_cities[county]:
            city = random.choice(county_to_cities[county])
        else:
            city = random.choice(all_cities)

        expanded_street = expand_street_name(raw_street)
        canonical_parts = [f"{house_num} {expanded_street}", f"{city}, NY"]
        if zip5:
            canonical_parts[-1] += f" {zip5}"
        canonical = ", ".join(canonical_parts)

        # Raw = exactly what the source system gave us: abbreviated street, no city/zip
        raw = f"{house_num} {raw_street}".strip()

        pairs.append((raw, canonical, 1, "table1"))
    return pairs


# ──────────────────────────────────────────────────────────────────────────
# Negative pairs
# ──────────────────────────────────────────────────────────────────────────
def build_negative_pairs(positive_pairs: list, n_negative: int) -> list:
    negatives = []
    attempts = 0
    while len(negatives) < n_negative and attempts < n_negative * 20:
        attempts += 1
        a = random.choice(positive_pairs)
        b = random.choice(positive_pairs)
        raw_a, canonical_b = a[0], b[1]
        if raw_a.strip().lower() != canonical_b.strip().lower():
            negatives.append((raw_a, canonical_b, 0, "synthetic_negative"))
    return negatives


# ──────────────────────────────────────────────────────────────────────────
def main():
    report = {}

    df2, zip_to_city, county_to_cities, all_cities = load_and_clean_table2(report)
    df1 = load_and_clean_table1(report)

    pairs2 = build_pairs_from_table2(df2)
    pairs1 = build_pairs_from_table1(df1, zip_to_city, county_to_cities, all_cities)

    positives = pairs1 + pairs2
    random.shuffle(positives)

    n_negative = int(len(positives) * NEGATIVE_PAIR_FRACTION)
    negatives = build_negative_pairs(positives, n_negative)

    all_pairs = positives + negatives
    random.shuffle(all_pairs)

    n_holdout = int(len(all_pairs) * HOLDOUT_FRACTION)
    holdout = all_pairs[:n_holdout]
    training = all_pairs[n_holdout:]

    with open(OUT_TRAINING, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["raw_address", "canonical_address", "is_correct"])
        for raw, canonical, label, _src in training:
            writer.writerow([raw, canonical, label])

    with open(OUT_HOLDOUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["raw_address", "canonical_address", "is_correct", "source"])
        for raw, canonical, label, src in holdout:
            writer.writerow([raw, canonical, label, src])

    report["pairs"] = {
        "table1_positive_pairs": len(pairs1),
        "table2_positive_pairs": len(pairs2),
        "negative_pairs": len(negatives),
        "total_pairs": len(all_pairs),
        "written_to_training_data_csv": len(training),
        "written_to_validation_holdout_csv": len(holdout),
        "holdout_fraction_requested": HOLDOUT_FRACTION,
    }
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote {len(training)} training pairs -> {OUT_TRAINING}")
    print(f"Wrote {len(holdout)} holdout pairs   -> {OUT_HOLDOUT}")
    print(f"Wrote data quality report           -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
