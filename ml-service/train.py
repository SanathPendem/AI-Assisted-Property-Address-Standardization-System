"""
train.py
========
Standalone training entry point -- trains the LightGBM confidence model on
data/training_data.csv (no human feedback required) and saves the model artifact.

This is the script to run the FIRST time you bring up your own dataset. The
/retrain API endpoint (app/main.py) calls the same underlying function
(app.retraining.retrain_model) but additionally folds in human review feedback;
use that endpoint later, once the review queue has produced corrections.

MUST be run with libpostal + the project's Python deps installed -- i.e. inside
the ml-service container:

    docker compose exec ml-service python train.py

Or locally if you've installed libpostal + requirements.txt yourself.

INPUT:  data/training_data.csv  (raw_address, canonical_address, is_correct)
OUTPUT: models/lgbm_model.pkl   (pickled LGBMClassifier)
        stdout: accuracy / precision / recall / f1 on the internal 80/20 split
        optional: a row in the `model_registry` Postgres table (--register)
"""
import argparse
import json
import os
import time

from app.retraining import retrain_model, BASE_DATA_PATH, MODEL_PATH


def register_model_in_db(version: str, metrics: dict, artifact_path: str):
    """Optional: records this training run in the model_registry table.
    Requires DATABASE_URL and psycopg2 -- skipped gracefully if unavailable."""
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed -- skipping model_registry insert.")
        return

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set -- skipping model_registry insert.")
        return

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            # Deactivate the previous active model, activate this one
            cur.execute("UPDATE model_registry SET is_active = FALSE WHERE is_active = TRUE")
            cur.execute(
                """INSERT INTO model_registry
                   (version, artifact_path, training_samples, accuracy,
                    precision_score, recall_score, f1_score, training_log, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)""",
                (
                    version,
                    artifact_path,
                    metrics["training_samples"],
                    metrics["accuracy"],
                    metrics["precision"],
                    metrics["recall"],
                    metrics["f1"],
                    json.dumps(metrics),
                ),
            )
        conn.commit()
        print(f"Registered model {version} in model_registry (set as active).")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true",
                         help="Insert this run into the Postgres model_registry table")
    args = parser.parse_args()

    print(f"Training data: {BASE_DATA_PATH}")
    print(f"Model output:  {MODEL_PATH}")

    metrics = retrain_model(feedback_data=[])  # no human feedback yet -- base data only
    version = f"v{int(time.time())}-base-retrained"

    print("\n=== Training complete ===")
    print(json.dumps(metrics, indent=2))
    print(f"Model version: {version}")
    print(f"Saved to:      {MODEL_PATH}")

    if args.register:
        register_model_in_db(version, metrics, MODEL_PATH)


if __name__ == "__main__":
    main()
