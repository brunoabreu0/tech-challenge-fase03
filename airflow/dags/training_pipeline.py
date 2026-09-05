"""Airflow DAG: Medical Triage Training Pipeline.

This DAG orchestrates the full training lifecycle for the medical triage
NLP classifier:

    ingest → preprocess → train → save_model

Schedule: Weekly (every Monday at 02:00 UTC) or triggered manually.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default arguments for all tasks
# ---------------------------------------------------------------------------
DEFAULT_ARGS = {
    "owner": "fiap-9mlet-grupo17",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

# ---------------------------------------------------------------------------
# Path config (can be overridden via Airflow Variables)
# ---------------------------------------------------------------------------
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", "/opt/airflow/data/raw"))
DATA_PROCESSED_DIR = Path(
    os.getenv("DATA_PROCESSED_DIR", "/opt/airflow/data/processed")
)
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/opt/airflow/models"))
SRC_DIR = Path(os.getenv("SRC_DIR", "/opt/airflow/src"))

# Ensure src is importable inside Airflow workers
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Task functions
# ---------------------------------------------------------------------------
def task_ingest(**context) -> None:
    """Task 1 — Ingest: load raw dataset and save to processed directory.

    Loads the medical triage dataset (real CSV or synthetic fallback)
    and saves it as ``processed/train.csv`` for downstream tasks.
    """
    from triage.data.loader import load_dataset

    logger.info("=== TASK: ingest — Loading dataset from %s ===", DATA_RAW_DIR)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset(data_dir=DATA_RAW_DIR, random_seed=42)
    output_path = DATA_PROCESSED_DIR / "train.csv"
    df.to_csv(output_path, index=False)

    logger.info(
        "Ingested %d samples → saved to %s (label distribution: %s)",
        len(df),
        output_path,
        df["label"].value_counts().to_dict(),
    )


def task_preprocess(**context) -> None:
    """Task 2 — Preprocess: apply text cleaning to the ingested dataset.

    Reads ``processed/train.csv``, applies ``clean_text`` and saves
    the result as ``processed/train_clean.csv``.
    """
    import pandas as pd

    from triage.data.preprocessor import preprocess_texts

    logger.info("=== TASK: preprocess — Cleaning text ===")
    input_path = DATA_PROCESSED_DIR / "train.csv"
    df = pd.read_csv(input_path)

    df["text"] = preprocess_texts(df["text"].tolist())
    output_path = DATA_PROCESSED_DIR / "train_clean.csv"
    df.to_csv(output_path, index=False)

    logger.info("Preprocessed %d records → saved to %s", len(df), output_path)


def task_train(**context) -> None:
    """Task 3 — Train: fit the TF-IDF + LR classifier on cleaned data.

    Reads ``processed/train_clean.csv``, trains the model and pushes
    the fitted classifier via XCom for the save_model task.
    """

    import pandas as pd

    from triage.model.tfidf_lr import TFIDFLogisticClassifier

    logger.info("=== TASK: train — Fitting TF-IDF + LR model ===")
    df = pd.read_csv(DATA_PROCESSED_DIR / "train_clean.csv")

    texts = df["text"].tolist()
    labels = df["label"].tolist()

    clf = TFIDFLogisticClassifier()
    clf.fit(texts, labels)

    # Evaluate on training set (quick sanity check)
    from sklearn.metrics import accuracy_score

    preds = clf.predict(texts)
    acc = accuracy_score(labels, preds)
    logger.info("Training accuracy (sanity check): %.4f", acc)

    # Save to a temporary path and push to XCom
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = MODEL_DIR / "classifier_new.joblib"
    clf.save(temp_path)
    context["ti"].xcom_push(key="model_path", value=str(temp_path))
    logger.info("Model saved temporarily to %s", temp_path)


def task_save_model(**context) -> None:
    """Task 4 — Save Model: promote the newly trained model to production.

    Renames the temporary model file to the stable ``classifier.joblib``
    path (overwriting the previous version).

    Also exports an ONNX version for faster inference.
    """
    import shutil

    from triage.model.tfidf_lr import TFIDFLogisticClassifier

    logger.info("=== TASK: save_model — Promoting model to production ===")
    temp_path = Path(context["ti"].xcom_pull(key="model_path", task_ids="train"))
    final_path = MODEL_DIR / "classifier.joblib"

    shutil.move(str(temp_path), str(final_path))
    logger.info("Model promoted: %s → %s", temp_path, final_path)

    # Export to ONNX for optimised inference
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import StringTensorType

        clf = TFIDFLogisticClassifier.load(final_path)
        pipeline = clf.get_sklearn_pipeline()
        initial_type = [("input", StringTensorType([None, 1]))]
        onnx_model = convert_sklearn(
            pipeline,
            initial_types=initial_type,
            target_opset=17,
            options={type(pipeline.named_steps["clf"]): {"zipmap": True}},
        )
        onnx_path = MODEL_DIR / "classifier.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        logger.info("ONNX model exported to %s", onnx_path)
    except Exception as e:
        logger.warning("ONNX export skipped (non-fatal): %s", e)

    logger.info("✅ Training pipeline completed successfully.")


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="medical_triage_training",
    description="Weekly retraining pipeline for the medical triage NLP classifier",
    schedule="0 2 * * 1",  # Every Monday at 02:00 UTC
    start_date=datetime(2026, 9, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["mlops", "nlp", "triage", "fiap-9mlet"],
    doc_md="""
    # Medical Triage Training Pipeline

    Retrains the TF-IDF + Logistic Regression classifier weekly.

    ## Tasks
    1. **ingest** — Loads raw dataset (real or synthetic)
    2. **preprocess** — Cleans and normalises text
    3. **train** — Fits TF-IDF + LR sklearn pipeline
    4. **save_model** — Promotes trained model; exports ONNX

    ## Dataset
    Place `medical_abstracts.csv` in `/opt/airflow/data/raw/` or
    the DAG will use synthetic data automatically.
    """,
) as dag:
    ingest = PythonOperator(
        task_id="ingest",
        python_callable=task_ingest,
    )

    preprocess = PythonOperator(
        task_id="preprocess",
        python_callable=task_preprocess,
    )

    train = PythonOperator(
        task_id="train",
        python_callable=task_train,
    )

    save_model = PythonOperator(
        task_id="save_model",
        python_callable=task_save_model,
    )

    # Pipeline: ingest → preprocess → train → save_model
    ingest >> preprocess >> train >> save_model
