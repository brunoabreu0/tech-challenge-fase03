"""Dataset loading and generation utilities."""

import logging
import random
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

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

    df = pd.DataFrame(records).sample(frac=1, random_state=random_seed).reset_index(drop=True)
    logger.info(
        "Synthetic dataset generated: %d samples, distribution: %s",
        len(df),
        df["label"].value_counts().to_dict(),
    )
    return df


def load_dataset(
    data_dir: Path,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Load the medical triage dataset from disk, falling back to synthetic data.

    Looks for ``medical_abstracts.csv`` (Medical Abstracts TC Corpus from Kaggle)
    in ``data_dir``. If not found, generates synthetic data automatically.

    Expected CSV columns: ``text``, ``label`` (int: 0=normal, 1=atencao, 2=urgente)
    or ``condition_label``, ``abstract`` (original Kaggle format).

    Args:
        data_dir: Directory containing raw dataset files.
        random_seed: Seed for reproducibility (used in synthetic generation).

    Returns:
        DataFrame with columns ``text`` (str) and ``label`` (int).
    """
    csv_path = Path(data_dir) / "medical_abstracts.csv"

    if csv_path.exists():
        logger.info("Loading real dataset from %s", csv_path)
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
        logger.info("Loaded %d samples from disk.", len(df))
        return df

    logger.warning(
        "Dataset not found at %s — using synthetic data. "
        "Download from https://www.kaggle.com/datasets/chaitanyakck/medical-text",
        csv_path,
    )
    return generate_synthetic_dataset(random_seed=random_seed)
