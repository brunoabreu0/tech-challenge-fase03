#!/usr/bin/env python3
"""Gerador de tráfego sintético e realista para a Medical Triage API.

Envia requisições com variados perfis clínicos (urgente, atenção, normal),
chamadas de healthcheck e métricas para popular os dashboards do Grafana
e alimentar o Prometheus com métricas de negócio e performance.

Uso:
    poetry run python scripts/generate_traffic.py --count 60
    poetry run python scripts/generate_traffic.py --url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from collections import Counter

# Exemplos clínicos realistas para cada categoria de triagem
CLINICAL_CASES = [
    # --- Casos Urgentes (alta prioridade, risco iminente) ---
    (
        "urgente",
        "Paciente masculino, 58 anos, dor precordial opressiva há 40 min com "
        "irradiação para mandíbula e braço esquerdo, sudorese fria e dispneia.",
    ),
    (
        "urgente",
        "Mulher de 72 anos com hemiparesia à direita de início súbito há 1h, "
        "afasia global, desvio de rima labial e sonolência.",
    ),
    (
        "urgente",
        "Vítima de acidente automobilístico com choque hipovolêmico, FC 145 bpm, "
        "PA 70x40 mmHg e abdome em tábua com irritação peritoneal.",
    ),
    (
        "urgente",
        "Crise asmática grave em jovem, tiragem intercostal, cianose labial, "
        "SpO2 82% em ar ambiente e sibilos expiratórios difusos.",
    ),
    (
        "urgente",
        "Choque anafilático pós-picada: edema de glote, estridor laríngeo, "
        "urticária generalizada e hipotensão severa.",
    ),
    # --- Casos de Atenção (moderada prioridade, necessita avaliação breve) ---
    (
        "atencao",
        "Paciente de 45 anos com febre de 38.8C há 4 dias, tosse produtiva "
        "com escarro purulento, dor pleurítica em hemitórax direito.",
    ),
    (
        "atencao",
        "Criança de 6 anos com vômitos incoercíveis há 24 horas, prostração, "
        "sinais leves de desidratação e febre de 38.2C.",
    ),
    (
        "atencao",
        "Dor lombar intensa unilateral irradiando para fossa ilíaca, náuseas "
        "e hematúria macroscópica sugestiva de nefrolitíase.",
    ),
    (
        "atencao",
        "Idosa com dor e edema assimétrico em membro inferior esquerdo há 2d, "
        "empastamento de panturrilha e calor local sugestivo de TVP.",
    ),
    (
        "atencao",
        "Crise hipertensiva assintomática (PA 180x105 mmHg), queixa de cefaleia "
        "occipital pulsátil, sem déficit neurológico focal.",
    ),
    # --- Casos Normais / Rotina (baixa prioridade, ambulatorial) ---
    (
        "normal",
        "Paciente assintomático comparece para consulta de rotina preventiva, "
        "check-up anual laboratorial e renovação de receita médica.",
    ),
    (
        "normal",
        "Paciente de 32 anos solicita encaminhamento dermatológico para "
        "avaliação de nevo melanocítico estável em dorso, sem queixas.",
    ),
    (
        "normal",
        "Retorno ambulatorial para apresentação de exames laboratoriais "
        "com perfil lipídico e glicemia de jejum normais.",
    ),
    (
        "normal",
        "Queixa de coriza hialina e espirros eventuais há 2 dias, afebril, "
        "bom estado geral, sem dispneia ou prostração.",
    ),
    (
        "normal",
        "Consulta de avaliação médica para atestado de aptidão física para "
        "início de atividades desportivas em academia.",
    ),
]


def post_prediction(base_url: str, text: str) -> tuple[int, str | None, float]:
    """Envia requisição POST para /predict.

    Retorna (status_code, label, latência em ms).
    """
    url = f"{base_url.rstrip('/')}/predict"
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "TriageTrafficGen/1.0",
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


def get_endpoint(base_url: str, path: str) -> tuple[int, float]:
    """Envia requisição GET simples para o endpoint."""
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TriageTrafficGen/1.0"},
        method="GET",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return resp.status, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return e.code, elapsed_ms
    except Exception:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return 0, elapsed_ms


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerador de Tráfego da API de Triagem")
    parser.add_argument(
        "--url",
        default="https://api.triage.cloud-ip.cc",
        help="URL base da API (padrão: https://api.triage.cloud-ip.cc)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=45,
        help="Quantidade total de casos de predição a enviar (padrão: 45)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Intervalo em segundos entre requisições (padrão: 0.1s)",
    )
    args = parser.parse_args()

    print(f"🚀 Iniciando envio de tráfego para: {args.url}")
    print(f"📦 Total de predições planejadas: {args.count}")
    print("=" * 60)

    label_counts: Counter[str] = Counter()
    latencies: list[float] = []
    successes = 0
    errors = 0

    # 1. Enviar batch de health checks e metrics
    for _ in range(5):
        get_endpoint(args.url, "/health")
        get_endpoint(args.url, "/metrics")

    # 2. Enviar predições distribuídas
    for i in range(1, args.count + 1):
        expected_label, text = random.choice(CLINICAL_CASES)
        status, predicted_label, lat_ms = post_prediction(args.url, text)

        if status == 200 and predicted_label:
            successes += 1
            label_counts[predicted_label] += 1
            latencies.append(lat_ms)
            msg = (
                f"[{i:03d}/{args.count}] ✅ Status: {status} "
                f"| Predito: {predicted_label:<8} | Latência: {lat_ms:6.2f}ms"
            )
            print(msg)
        else:
            errors += 1
            print(f"[{i:03d}/{args.count}] ❌ Erro: Status HTTP {status}")

        # Ocasionalmente consultar health / metrics como tráfego de fundo
        if i % 5 == 0:
            get_endpoint(args.url, "/health")
            get_endpoint(args.url, "/metrics")

        if args.delay > 0:
            time.sleep(args.delay)

    # 3. Teste de validação (enviar body vazio para registrar status 422)
    post_prediction(args.url, "")

    print("=" * 60)
    print("📊 Resumo do Tráfego Gerado:")
    print(
        f"  • Total de Predições: {args.count} "
        f"(Sucessos: {successes}, Falhas: {errors})"
    )
    print(f"  • Distribuição por Classe: {dict(label_counts)}")
    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"  • Latência Média: {avg_lat:.2f}ms | P95: {p95_lat:.2f}ms")
    print("✅ Métricas atualizadas no Prometheus e prontas no Grafana!")


if __name__ == "__main__":
    main()
