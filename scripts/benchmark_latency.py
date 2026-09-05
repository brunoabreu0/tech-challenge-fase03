"""Latency benchmark: compare sklearn vs ONNX Runtime inference speed."""

import logging
import sys
import time
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from triage.data.loader import generate_synthetic_dataset
from triage.data.preprocessor import preprocess_texts
from triage.model.factory import ClassifierFactory
from triage.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Number of warmup + benchmark iterations
WARMUP_RUNS = 5
BENCHMARK_RUNS = 100
BATCH_SIZE = 1  # single-sample latency (real-time inference)


def benchmark(clf, texts: list[str], n_runs: int) -> list[float]:
    """Run n_runs inference calls and return latency in milliseconds."""
    latencies = []
    for _ in range(n_runs):
        start = time.perf_counter()
        clf.predict(texts[:BATCH_SIZE])
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
    return latencies


def main() -> None:
    """Compare sklearn vs ONNX Runtime latency."""
    settings = get_settings()
    sklearn_path = settings.model_dir / "classifier.joblib"
    onnx_path = settings.model_dir / "classifier.onnx"

    if not sklearn_path.exists():
        logger.error("sklearn model not found. Run scripts/train.py first.")
        sys.exit(1)

    if not onnx_path.exists():
        logger.error("ONNX model not found. Run scripts/export_onnx.py first.")
        sys.exit(1)

    # Prepare test data
    df = generate_synthetic_dataset(n_samples=200, random_seed=99)
    texts = preprocess_texts(df["text"].tolist())

    logger.info(
        "Benchmarking with batch_size=%d, runs=%d ...", BATCH_SIZE, BENCHMARK_RUNS
    )

    # -------------------------------------------------------------------------
    # sklearn benchmark
    # -------------------------------------------------------------------------
    sklearn_clf = ClassifierFactory.load("tfidf_lr", sklearn_path)
    # Warmup
    benchmark(sklearn_clf, texts, WARMUP_RUNS)
    sklearn_latencies = benchmark(sklearn_clf, texts, BENCHMARK_RUNS)

    # -------------------------------------------------------------------------
    # ONNX Runtime benchmark
    # -------------------------------------------------------------------------
    onnx_clf = ClassifierFactory.load("onnx", onnx_path)
    # Warmup
    benchmark(onnx_clf, texts, WARMUP_RUNS)
    onnx_latencies = benchmark(onnx_clf, texts, BENCHMARK_RUNS)

    # -------------------------------------------------------------------------
    # Results
    # -------------------------------------------------------------------------
    sklearn_avg = mean(sklearn_latencies)
    sklearn_std = stdev(sklearn_latencies)
    onnx_avg = mean(onnx_latencies)
    onnx_std = stdev(onnx_latencies)
    speedup = sklearn_avg / onnx_avg if onnx_avg > 0 else float("inf")

    print("\n" + "=" * 60)
    print("LATENCY BENCHMARK RESULTS")
    print("=" * 60)
    print(f"{'Model':<20} {'Avg (ms)':>10} {'Std (ms)':>10}")
    print("-" * 60)
    print(f"{'sklearn (TF-IDF+LR)':<20} {sklearn_avg:>10.3f} {sklearn_std:>10.3f}")
    print(f"{'ONNX Runtime':<20} {onnx_avg:>10.3f} {onnx_std:>10.3f}")
    print("-" * 60)
    print(f"Speedup (sklearn / ONNX): {speedup:.2f}x faster with ONNX")
    print("=" * 60)
    print(f"\nConfiguration: batch_size={BATCH_SIZE}, runs={BENCHMARK_RUNS}")


if __name__ == "__main__":
    main()
