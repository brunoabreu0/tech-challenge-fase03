#!/usr/bin/env python3
"""Gerador e simulador de tráfego clínico para a Medical Triage API.

Envia laudos e resumos médicos reais para a API de triagem, simulando o fluxo
contínuo de admissão de pacientes em um pronto-socorro / hospital.

Uso:
    # Envio de lote pontual:
    python scripts/generate_traffic.py --url https://api.triage.cloud-ip.cc --count 30

    # Modo contínuo (schedulado / daemon para manter o Grafana vivo):
    python scripts/generate_traffic.py --url http://api:8000 --continuous --delay 15
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from collections import Counter

# Textos médicos realistas enviados para triagem.
# A API recebe SOMENTE o texto do laudo e infere a classificação de risco.
CLINICAL_REPORTS = [
    # Casos agudos / emergenciais
    (
        "Paciente masculino, 58 anos, dor precordial opressiva há 40 min com "
        "irradiação para mandíbula e braço esquerdo, sudorese fria e dispneia."
    ),
    (
        "Mulher de 72 anos com hemiparesia à direita de início súbito há 1h, "
        "afasia global, desvio de rima labial e sonolência progressiva."
    ),
    (
        "Vítima de acidente automobilístico com choque hipovolêmico, FC 145 bpm, "
        "PA 70x40 mmHg e abdome em tábua com irritação peritoneal."
    ),
    (
        "Crise asmática grave em jovem, tiragem intercostal, cianose labial, "
        "SpO2 82% em ar ambiente e sibilos expiratórios difusos."
    ),
    (
        "Choque anafilático pós-picada de inseto: edema de glote, estridor "
        "laríngeo, urticária generalizada e hipotensão severa."
    ),
    (
        "Politraumatizado com traumatismo cranioencefálico grave, Glasgow 7, "
        "anisocoria pupilar e respiração atáxica."
    ),
    # Casos de urgência relativa / atenção clínica
    (
        "Paciente de 45 anos com febre de 38.8C há 4 dias, tosse produtiva "
        "com escarro purulento, dor pleurítica em base pulmonar direita."
    ),
    (
        "Criança de 6 anos com vômitos incoercíveis há 24 horas, prostração, "
        "sinais leves de desidratação e febre de 38.2C."
    ),
    (
        "Dor lombar intensa unilateral irradiando para fossa ilíaca, náuseas "
        "e hematúria macroscópica sugestiva de nefrolitíase."
    ),
    (
        "Idosa com dor e edema assimétrico em membro inferior esquerdo há 2d, "
        "empastamento de panturrilha e calor local sugestivo de TVP."
    ),
    (
        "Crise hipertensiva assintomática (PA 180x105 mmHg), queixa de cefaleia "
        "occipital pulsátil, sem déficit neurológico focal agudo."
    ),
    (
        "Epigastralgia intensa em queimação há 6 horas associada a vômitos "
        "biliosos e histórico prévio de úlcera péptica."
    ),
    # Casos ambulatoriais / rotina preventiva
    (
        "Paciente assintomático comparece para consulta de rotina preventiva, "
        "check-up anual laboratorial e renovação de receita médica."
    ),
    (
        "Paciente de 32 anos solicita encaminhamento dermatológico para "
        "avaliação de nevo melanocítico estável em dorso, sem queixas."
    ),
    (
        "Retorno ambulatorial para apresentação de exames laboratoriais "
        "com perfil lipídico e glicemia de jejum dentro dos valores de referência."
    ),
    (
        "Queixa de coriza hialina e espirros eventuais há 2 dias, afebril, "
        "bom estado geral, sem dispneia ou prostração."
    ),
    (
        "Consulta de avaliação médica para atestado de aptidão física para "
        "início de atividades desportivas em academia."
    ),
    (
        "Acompanhamento semestral de puericultura em lactente hígido de 8 meses, "
        "ganho pondero-estatural adequado, sem queixas maternas."
    ),
]


def post_prediction(base_url: str, text: str) -> tuple[int, str | None, float]:
    """Envia o texto do laudo para /predict e recebe a classificação do modelo."""
    url = f"{base_url.rstrip('/')}/predict"
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MedicalTriageSimulator/1.0",
        },
        method="POST",
    )

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            label = data.get("label") or data.get("predicted_label")
            return resp.status, label, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return e.code, None, elapsed_ms
    except Exception:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return 0, None, elapsed_ms


def ping_endpoint(base_url: str, path: str) -> None:
    """Envia requisição GET simples para healthcheck ou métricas."""
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MedicalTriageSimulator/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass


def run_batch(base_url: str, count: int, delay: float) -> None:
    """Executa um lote finito de predições clínicas."""
    print(f"🚀 Enviando lote de {count} laudos para triagem em {base_url}...")
    label_counts: Counter[str] = Counter()
    latencies: list[float] = []
    successes = 0

    for i in range(1, count + 1):
        report = random.choice(CLINICAL_REPORTS)
        status, predicted_label, lat_ms = post_prediction(base_url, report)

        if status == 200 and predicted_label:
            successes += 1
            label_counts[predicted_label] += 1
            latencies.append(lat_ms)
            print(
                f"[{i:03d}/{count}] Status: {status} "
                f"| Classificação: {predicted_label:<8} "
                f"| Latência: {lat_ms:6.2f}ms"
            )
        else:
            print(f"[{i:03d}/{count}] Erro HTTP {status}")

        if i % 4 == 0:
            ping_endpoint(base_url, "/health")
            ping_endpoint(base_url, "/metrics")

        if delay > 0:
            time.sleep(delay)

    print("=" * 60)
    print(f"📊 Lote concluído: {successes}/{count} sucessos")
    print(f"🏥 Distribuição inferida pelo modelo: {dict(label_counts)}")
    if latencies:
        print(f"⏱️ Latência Média: {sum(latencies) / len(latencies):.2f}ms")


def run_continuous(base_url: str, interval: float) -> None:
    """Executa em modo contínuo / daemon, enviando laudos a cada intervalo."""
    print(f"🔄 Modo contínuo iniciado em {base_url} (intervalo: {interval}s)")
    step = 0
    while True:
        step += 1
        report = random.choice(CLINICAL_REPORTS)
        status, label, lat_ms = post_prediction(base_url, report)
        print(
            f"[{time.strftime('%X')}] #{step:04d} -> Status {status} "
            f"| Classificação: {label or 'falha':<8} ({lat_ms:.1f}ms)"
        )

        if step % 3 == 0:
            ping_endpoint(base_url, "/health")
            ping_endpoint(base_url, "/metrics")

        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador de Tráfego Clínico — Medical Triage API"
    )
    parser.add_argument(
        "--url",
        default="https://api.triage.cloud-ip.cc",
        help="URL base da API (padrão: https://api.triage.cloud-ip.cc)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=30,
        help="Quantidade de laudos para o envio em lote (padrão: 30)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay entre requisições no modo lote (padrão: 0.1s)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Executa em loop contínuo simulando chegada periódica de pacientes",
    )
    args = parser.parse_args()

    if args.continuous:
        run_continuous(args.url, interval=args.delay if args.delay > 1 else 15.0)
    else:
        run_batch(args.url, args.count, args.delay)


if __name__ == "__main__":
    main()
