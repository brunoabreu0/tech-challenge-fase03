"""Dataset loading and generation utilities."""

import json
import logging
import os
import random
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Kaggle dataset constants
# ---------------------------------------------------------------------------
_KAGGLE_DATASET = "chaitanyakck/medical-text"
_KAGGLE_DATASET_URL = "https://www.kaggle.com/datasets/chaitanyakck/medical-text"

# ---------------------------------------------------------------------------
# Label mapping
# ---------------------------------------------------------------------------
LABEL_MAP = {
    "normal": 0,
    "atencao": 1,
    "urgente": 2,
}

LABEL_NAMES = {v: k for k, v in LABEL_MAP.items()}


# ---------------------------------------------------------------------------
# Synthetic data generator (fallback when real dataset is unavailable)
# ---------------------------------------------------------------------------
_TEMPLATES: dict[str, list[str]] = {
    "normal": [
        "paciente sem queixas relevantes exame de rotina normal",
        "checkup anual sem alteracoes pressao arterial dentro do esperado",
        "consulta preventiva resultados laboratoriais dentro da normalidade",
        "paciente estavel sem sinais de infeccao ou inflamacao",
        "exame de rotina sem achados significativos hemograma normal",
        "revisao anual paciente saudavel sem medicamentos continuos",
        "consulta de acompanhamento sem novas queixas evolucao satisfatoria",
        "triagem inicial sem urgencia sinais vitais normais",
        "paciente adulto jovem sem comorbidades consulta de rotina",
        "exame clinico normal ausculta cardiaca e pulmonar sem alteracoes",
    ],
    "atencao": [
        "paciente com pressao arterial levemente elevada necessita acompanhamento",
        "dor de cabeca persistente ha tres dias sem melhora com analgesicos",
        "glicemia de jejum alterada necessita investigacao adicional",
        "historico de diabetes tipo dois glicemia descompensada",
        "paciente com tosse produtiva ha mais de dez dias febre baixa",
        "dor lombar cronica com piora nos ultimos dias limitando atividades",
        "paciente com ansiedade e insonia ha duas semanas sem melhora",
        "pressao alta com cefaleia necessita ajuste de medicacao",
        "exame mostra colesterol elevado e triglicerideos acima do normal",
        "paciente relata tontura e mal estar frequentes nos ultimos dias",
    ],
    "urgente": [
        "dor toracica severa irradiando para braco esquerdo suspeita de infarto",
        "paciente com dificuldade respiratoria grave saturacao de oxigenio baixa",
        "traumatismo craniano com perda de consciencia necessita avaliacao imediata",
        "hemorragia abundante sem controle paciente palido e sudorético",
        "suspeita de acidente vascular cerebral com paralisia facial e fala alterada",
        "paciente com crise convulsiva generalizada necessita atendimento urgente",
        "anafilaxia apos picada de inseto com edema de glote em progressao",
        "hipotensao severa e taquicardia sinais de choque circulatorio",
        "queimadura de terceiro grau em area extensa necessita internacao imediata",
        "intoxicacao por medicamento com rebaixamento do nivel de consciencia",
    ],
}


def generate_synthetic_dataset(
    n_samples: int = 3000,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Generate a synthetic medical triage dataset.

    Creates balanced samples across three urgency levels using predefined
    medical text templates with random variations.

    Args:
        n_samples: Total number of samples to generate.
        random_seed: Seed for reproducibility.

    Returns:
        DataFrame with columns ``text`` and ``label`` (0=normal, 1=atencao, 2=urgente).
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    records = []
    labels = list(_TEMPLATES.keys())
    per_class = n_samples // len(labels)

    for label_name in labels:
        templates = _TEMPLATES[label_name]
        label_id = LABEL_MAP[label_name]
        for _ in range(per_class):
            # Pick a random template and add minor variations
            base = random.choice(templates)
            # Optionally append a second sentence
            if random.random() > 0.5:
                extra = random.choice(templates)
                base = f"{base} {extra}"
            records.append({"text": base, "label": label_id})

    df = (
        pd.DataFrame(records)
        .sample(frac=1, random_state=random_seed)
        .reset_index(drop=True)
    )
    logger.info(
        "Synthetic dataset generated: %d samples, distribution: %s",
        len(df),
        df["label"].value_counts().to_dict(),
    )
    return df

def _resolve_kaggle_credentials() -> bool:
    """Resolve Kaggle credentials from available sources.

    Checks three sources in priority order:

    1. ``KAGGLE_API_TOKEN`` env var \u2014 new-style Bearer token (``KGAT_***``).
       Writes ``{"token": "<value>"}`` to ``~/.kaggle/kaggle.json`` so the
       SDK (v1.6+) picks it up automatically.
    2. ``KAGGLE_USERNAME`` + ``KAGGLE_KEY`` env vars \u2014 legacy username/key pair.
    3. ``~/.kaggle/kaggle.json`` file already present on disk.

    Returns:
        ``True`` if at least one valid credential source was found.
    """
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"

    # 1. KAGGLE_API_TOKEN \u2014 new Kaggle Bearer token (KGAT_***)
    api_token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    if api_token:
        try:
            kaggle_json.parent.mkdir(parents=True, exist_ok=True)
            kaggle_json.write_text(json.dumps({"token": api_token}))
            kaggle_json.chmod(0o600)
            logger.info(
                "Kaggle credentials loaded from KAGGLE_API_TOKEN (Bearer token)."
            )
            return True
        except OSError as exc:
            logger.warning("Failed to write Kaggle credentials file: %s", exc)

    # 2. Legacy KAGGLE_USERNAME + KAGGLE_KEY env vars
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if username and key:
        logger.info("Kaggle credentials loaded from KAGGLE_USERNAME + KAGGLE_KEY.")
        return True

    # 3. Existing kaggle.json on disk
    if kaggle_json.exists():
        logger.info("Kaggle credentials loaded from %s.", kaggle_json)
        return True

    logger.info(
        "No Kaggle credentials found. Provide one of:\n"
        "  a) KAGGLE_API_TOKEN=KGAT_*** env var (from kaggle.com/settings > API),\n"
        "  b) KAGGLE_USERNAME + KAGGLE_KEY env vars,\n"
        "  c) ~/.kaggle/kaggle.json file."
    )
    return False


def download_kaggle_dataset(data_dir: Path) -> bool:
    """Attempt to download the Medical Abstracts TC Corpus from Kaggle.

    Credentials are resolved automatically from (in order):

    - ``KAGGLE_API_TOKEN`` env var \u2014 new-style Bearer token (``KGAT_***``).
    - ``KAGGLE_USERNAME`` + ``KAGGLE_KEY`` env vars \u2014 legacy pair.
    - ``~/.kaggle/kaggle.json`` file already present on disk.

    The ``kaggle`` Python package must be installed (optional dependency:
    ``poetry install --with kaggle``).

    Args:
        data_dir: Target directory where the dataset will be saved.

    Returns:
        ``True`` if the download succeeded, ``False`` otherwise.
    """
    if not _resolve_kaggle_credentials():
        return False

    try:
        import kaggle  # type: ignore[import-untyped]  # noqa: PLC0415
    except ImportError:
        logger.info(
            "'kaggle' package not installed. "
            "Run `pip install kaggle` to enable automatic download."
        )
        return False

    try:
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Downloading Kaggle dataset '%s' to %s ...", _KAGGLE_DATASET, data_dir
        )

        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            _KAGGLE_DATASET,
            path=str(data_dir),
            unzip=False,
            quiet=False,
        )

        # The downloaded zip contains train.dat — extract and rename
        zip_path = data_dir / "medical-text.zip"
        if zip_path.exists():
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(data_dir)
            zip_path.unlink()
            logger.info("Extracted dataset to %s", data_dir)

        # Rename train.dat → medical_abstracts.csv if needed
        train_dat = data_dir / "train.dat"
        target_csv = data_dir / "medical_abstracts.csv"
        if train_dat.exists() and not target_csv.exists():
            train_dat.rename(target_csv)
            logger.info("Renamed train.dat → medical_abstracts.csv")

        if target_csv.exists():
            logger.info("Dataset ready at %s", target_csv)
            return True

        logger.warning(
            "Download completed but expected file not found at %s", target_csv
        )
        return False

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Kaggle download failed: %s — falling back to synthetic data.", exc
        )
        return False


def _load_csv(csv_path: Path) -> pd.DataFrame:
    """Read and normalise a Medical Abstracts CSV into ``text``/``label`` columns.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        DataFrame with columns ``text`` (str) and ``label`` (int).
    """
    df = pd.read_csv(csv_path)

    # Support original Kaggle column names
    if "abstract" in df.columns and "condition_label" in df.columns:
        df = df.rename(columns={"abstract": "text", "condition_label": "label"})
        # Map 5-class Kaggle labels → 3-class urgency
        # 1=Neoplasms→urgente, 2=Digestive→atencao, 3=Nervous→urgente,
        # 4=Cardiovascular→urgente, 5=General→normal
        kaggle_to_triage = {1: 2, 2: 1, 3: 2, 4: 2, 5: 0}
        df["label"] = df["label"].map(kaggle_to_triage)

    df = df[["text", "label"]].dropna()
    df["label"] = df["label"].astype(int)
    return df


def load_dataset(
    data_dir: Path,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Load the medical triage dataset using a three-tier strategy.

    Resolution order:

    1. **Disk** — looks for ``medical_abstracts.csv`` in *data_dir*.
    2. **Kaggle download** — if credentials are available (``KAGGLE_USERNAME`` +
       ``KAGGLE_KEY`` env vars, or ``~/.kaggle/kaggle.json``) and the ``kaggle``
       package is installed, downloads the Medical Abstracts TC Corpus automatically.
    3. **Synthetic fallback** — generates 3 000 balanced samples in memory.

    Expected CSV columns: ``text``, ``label`` (int: 0=normal, 1=atencao, 2=urgente)
    or ``condition_label``, ``abstract`` (original Kaggle format).

    Args:
        data_dir: Directory containing (or where to download) raw dataset files.
        random_seed: Seed for reproducibility (used in synthetic generation).

    Returns:
        DataFrame with columns ``text`` (str) and ``label`` (int).
    """
    csv_path = Path(data_dir) / "medical_abstracts.csv"

    # 1. Dataset already on disk
    if csv_path.exists():
        logger.info("Loading real dataset from %s", csv_path)
        df = _load_csv(csv_path)
        logger.info("Loaded %d samples from disk.", len(df))
        return df

    # 2. Try Kaggle download
    logger.info("Dataset not found locally — attempting Kaggle download...")
    if download_kaggle_dataset(data_dir) and csv_path.exists():
        logger.info("Loading downloaded dataset from %s", csv_path)
        df = _load_csv(csv_path)
        logger.info("Loaded %d samples from Kaggle.", len(df))
        return df

    # 3. Synthetic fallback
    logger.warning(
        "Could not obtain real dataset. Falling back to synthetic data. "
        "To use the real dataset, either:\n"
        "  a) Place the CSV at %s, or\n"
        "  b) Set KAGGLE_USERNAME + KAGGLE_KEY env vars and install 'kaggle' package.\n"
        "  Dataset URL: %s",
        csv_path,
        _KAGGLE_DATASET_URL,
    )
    return generate_synthetic_dataset(random_seed=random_seed)
