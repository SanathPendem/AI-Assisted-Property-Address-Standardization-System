"""
validate.py
===========
Evaluates the CURRENT trained model (models/lgbm_model.pkl) against
data/validation_holdout.csv -- rows that were held out by
data/prepare_training_data.py and were NEVER used in train.py / retrain_model.

This is the "true generalization" check requested alongside train.py's internal
80/20 split metrics (which only test on a split of the *training* file).

Run inside the ml-service container (needs libpostal):

    docker compose exec ml-service python validate.py

INPUT:  data/validation_holdout.csv  (raw_address, canonical_address, is_correct, source)
OUTPUT: stdout -- overall metrics + a breakdown by `source`
        (table1 / table2 / synthetic_negative) so you can see whether the model
        generalizes better on one source dataset than the other.
"""
import os

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from app.parser import parse_raw_address
from app.standardizer import standardize_parsed_components, format_canonical_address
from app.features import extract_features
from app.model import predict_confidence

_PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
HOLDOUT_PATH = os.environ.get("VALIDATION_DATA_PATH", os.path.join(_PACKAGE_ROOT, "data", "validation_holdout.csv"))
DECISION_THRESHOLD = float(os.environ.get("VALIDATION_THRESHOLD", "0.5"))


def evaluate(df: pd.DataFrame, label: str):
    if df.empty:
        print(f"[{label}] no rows -- skipping")
        return

    y_true, y_pred, confidences = [], [], []
    for _, row in df.iterrows():
        raw = str(row["raw_address"])
        canonical = str(row["canonical_address"])
        is_correct = int(row["is_correct"])

        parsed = parse_raw_address(raw)
        cc = standardize_parsed_components(parsed)
        # NOTE: we score the (raw, canonical) pair as given in the holdout file --
        # i.e. "would the model trust that THIS canonical is the right standardization
        # of THIS raw input" -- so features must compare raw vs the holdout's canonical,
        # not vs whatever the rule-based standardizer would produce on its own.
        feat = extract_features(raw, canonical, parsed, cc)
        confidence = predict_confidence(feat)

        y_true.append(is_correct)
        y_pred.append(1 if confidence >= DECISION_THRESHOLD else 0)
        confidences.append(confidence)

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    avg_conf = sum(confidences) / len(confidences)

    print(f"\n[{label}]  n={len(df)}")
    print(f"  accuracy={acc:.4f}  precision={prec:.4f}  recall={rec:.4f}  f1={f1:.4f}")
    print(f"  mean confidence={avg_conf:.4f}")
    print(f"  confusion matrix [[TN,FP],[FN,TP]] = {cm}")


def main():
    if not os.path.exists(HOLDOUT_PATH):
        print(f"No holdout file at {HOLDOUT_PATH}.")
        print("Run `python data/prepare_training_data.py` first.")
        return

    df = pd.read_csv(HOLDOUT_PATH)
    print(f"Loaded {len(df)} held-out rows from {HOLDOUT_PATH}")

    evaluate(df, "ALL HOLDOUT DATA")

    if "source" in df.columns:
        for source in sorted(df["source"].unique()):
            evaluate(df[df["source"] == source], source)


if __name__ == "__main__":
    main()
