"""Training script: load data, preprocess, train TF-IDF + LR, and save the model."""

import logging
import sys
from pathlib import Path

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from triage.data.loader import LABEL_NAMES, load_dataset
from triage.data.preprocessor import preprocess_texts
from triage.model.tfidf_lr import TFIDFLogisticClassifier
from triage.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Train and save the medical triage classifier."""
    settings = get_settings()
    settings.model_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. Load data
    # -------------------------------------------------------------------------
    logger.info("Loading dataset from %s ...", settings.data_raw_dir)
    df = load_dataset(
        data_dir=settings.data_raw_dir,
        random_seed=settings.random_seed,
    )
    logger.info("Dataset size: %d rows", len(df))

    # -------------------------------------------------------------------------
    # 2. Preprocess text
    # -------------------------------------------------------------------------
    logger.info("Preprocessing texts ...")
    df["text_clean"] = preprocess_texts(df["text"].tolist())

    # -------------------------------------------------------------------------
    # 3. Train / test split (temporal-like: last 20% is test)
    # -------------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        df["text_clean"].tolist(),
        df["label"].tolist(),
        test_size=0.2,
        random_state=settings.random_seed,
        stratify=df["label"].tolist(),
    )
    logger.info("Train: %d | Test: %d", len(X_train), len(X_test))

    # -------------------------------------------------------------------------
    # 4. Train the classifier
    # -------------------------------------------------------------------------
    clf = TFIDFLogisticClassifier()
    clf.fit(X_train, y_train)

    # -------------------------------------------------------------------------
    # 5. Evaluate
    # -------------------------------------------------------------------------
    y_pred = clf.predict(X_test)
    target_names = [LABEL_NAMES[i] for i in sorted(LABEL_NAMES.keys())]
    report = classification_report(y_test, y_pred, target_names=target_names)
    logger.info("Classification Report:\n%s", report)

    # -------------------------------------------------------------------------
    # 6. Save the model
    # -------------------------------------------------------------------------
    model_path = settings.model_dir / "classifier.joblib"
    clf.save(model_path)
    logger.info("✅ Model saved to %s", model_path)


if __name__ == "__main__":
    main()
