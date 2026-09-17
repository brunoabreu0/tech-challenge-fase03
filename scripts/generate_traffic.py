#!/usr/bin/env python3
"""Gerador e simulador dinâmico de tráfego clínico para a Medical Triage API.

Simula a admissão contínua de pacientes em um pronto-socorro / hospital moderno,
com alta variabilidade nos textos clínicos, múltiplos perfis e especialidades,
padrões de chegada não-estacionários (turnos, rajadas e calmaria), e monitoramento
de múltiplos endpoints HTTP para observabilidade rica no Grafana.

Uso:
    # Envio de lote pontual com alta variabilidade:
    python scripts/generate_traffic.py --url https://api.triage.cloud-ip.cc --count 30

    # Modo contínuo (daemon para manter o Grafana vivo e dinâmico):
    python scripts/generate_traffic.py --url http://api:8000 --continuous --delay 6
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from collections import Counter

# ==============================================================================
# Corpus Médico Clínico Multidisciplinar (Diversidade e Vocabulário Realista)
# ==============================================================================

CASOS_EMERGENCIAIS = [
    (
        "Paciente masculino, 58 anos, dor precordial opressiva há 40 min "
        "irradiando para mandíbula e braço esquerdo, sudorese fria e dispneia "
        "acentuada."
    ),
    (
        "Mulher de 64 anos com dor retroesternal em queimação súbita, hipotensa "
        "(PA 80x50 mmHg), taquicárdica (FC 122 bpm) e palidez cutânea."
    ),
    (
        "Choque cardiogênico com extremidades frias, tempo de enchimento "
        "capilar > 4s, estertores crepitantes bilaterais e SpO2 81% em ar "
        "ambiente."
    ),
    (
        "Parada cardiorrespiratória em via pública revertida após 2 ciclos de "
        "RCP e desfibrilação por FV; paciente comatoso e intubado."
    ),
    (
        "Dor torácica súbita dilacerante de intensidade 10/10 com irradiação "
        "interescapular e assimetria de pulsos periféricos sugestiva de "
        "dissecção de aorta."
    ),
    (
        "Mulher de 72 anos com hemiparesia à direita de início súbito há 1h, "
        "afasia global, desvio de rima labial e sonolência progressiva (escala "
        "Cincinnati positiva)."
    ),
    (
        "Crise convulsiva generalizada tônico-clônica com duração > 15 minutos "
        "(status epilepticus), sialorréia abundante e cianose perioral."
    ),
    (
        "Cefaleia em trovoada hiperaguda de intensidade máxima instantânea "
        "acompanhada de rigidez de nuca e vômitos em jato (suspeita de HSA)."
    ),
    (
        "Politraumatizado com traumatismo cranioencefálico grave, pontuação "
        "Glasgow 7, anisocoria pupilar direita e respiração atáxica."
    ),
    (
        "Crise asmática severa refratária com tiragem intercostal, batimento de "
        "asa de nariz, fala entrecortada e SpO2 80% sob máscara de O2."
    ),
    (
        "Insuficiência respiratória aguda hipoxêmica grave em paciente com DPOC "
        "exacerbada, cianose central e gasometria com acidose respiratória "
        "severa."
    ),
    (
        "Suspeita de pneumotórax hipertensivo após trauma torácico: hipotensão "
        "grave, turgência jugular patológica e ausência de murmúrio vesicular à "
        "esquerda."
    ),
    (
        "Vítima de colisão auto x anteparo em alta velocidade, choque "
        "hemorrágico hipovolêmico, PA 65x35 mmHg, FC 148 bpm e abdome tenso em "
        "tábua."
    ),
    (
        "Ferimento por arma de fogo em transição toracoabdominal com "
        "sangramento ativo profuso, rebaixamento do nível de consciência e "
        "pulso filiforme."
    ),
    (
        "Choque anafilático grave minutos após contraste iodado: broncoespasmo "
        "severo, estridor laríngeo, edema de glote e colapso circulatório."
    ),
    (
        "Abdome agudo perfurativo com pneumoperitônio volumoso, febre alta, "
        "taquicardia severa e sinais de peritonite generalizada."
    ),
    (
        "Hemorragia digestiva alta maciça com múltiplos episódios de hematêmese "
        "volumosa, hipotensão postural e rebaixamento do sensório."
    ),
]

CASOS_ATENCAO = [
    (
        "Paciente de 45 anos com febre de 38.9C há 4 dias, tosse produtiva com "
        "expectoração purulenta e dor pleurítica em base pulmonar direita."
    ),
    (
        "Criança de 6 anos com vômitos incoercíveis há 24 horas, prostração "
        "moderada, sinais de desidratação leve e febre de 38.3C."
    ),
    (
        "Pneumonia comunitária com consolidação radiológica em lobo médio, "
        "taquipneico leve (FR 24 irpm), afebril no momento sob antitérmico."
    ),
    (
        "Suspeita de infecção de trato urinário alta (pielonefrite): febre "
        "alta, calafrios intensos e sinal de Giordano positivo bilateralmente."
    ),
    (
        "Dor em fossa ilíaca direita há 18 horas de caráter progressivo, "
        "náuseas, anorexia e descompressão dolorosa positiva no ponto de "
        "McBurney."
    ),
    (
        "Dor lombar intensa unilateral tipo cólica irradiando para região "
        "inguinal, associada a náuseas e hematúria macroscópica por cálculo "
        "ureteral."
    ),
    (
        "Epigastralgia intensa em queimação há 6 horas associada a vômitos "
        "biliosos repetidos e histórico prévio de úlcera péptica ativa."
    ),
    (
        "Quadro de colecistite aguda: dor contínua em hipocôndrio direito após "
        "alimentação gordurosa com sinal de Murphy positivo."
    ),
    (
        "Crise hipertensiva sintomática com PA 185x110 mmHg, queixa de cefaleia "
        "occipital pulsátil e escotomas cintilantes, sem déficits motores "
        "focais."
    ),
    (
        "Idosa com dor e edema assimétrico exuberante em membro inferior "
        "esquerdo há 2 dias, empastamento de panturrilha e calor local "
        "sugestivo de TVP."
    ),
    (
        "Palpitações paroxísticas taquicárdicas associadas a mal-estar "
        "indefinido, sem síncope ou dor no peito, FC 118 bpm rítmica."
    ),
    (
        "Entorse de tornozelo de alta energia com deformidade articular "
        "evidente, edema volumoso e impotência funcional completa após trauma "
        "esportivo."
    ),
    (
        "Lombociatalgia aguda incapacitante com irradiação para dermátomo L5 à "
        "esquerda, sem perda de força motora ou disfunção esfincteriana."
    ),
    (
        "Celulite infecciosa em perna direita com eritema quente progressivo de "
        "bordas mal delimitadas, calor local e febre de 38.1C."
    ),
    (
        "Corte contuso profundo em antebraço com sangramento moderado "
        "controlado por compressão mecânica, requerendo sutura e profilaxia "
        "antitetânica."
    ),
]

CASOS_ROTINA = [
    (
        "Paciente de 42 anos assintomático comparece para consulta de rotina "
        "preventiva, check-up anual laboratorial e renovação de receita médica."
    ),
    (
        "Consulta ambulatorial de retorno com exames de perfil lipídico e "
        "glicemia de jejum perfeitamente dentro dos limites da normalidade."
    ),
    (
        "Acompanhamento semestral de puericultura em lactente saudável de 9 "
        "meses, desenvolvimento neuropsicomotor adequado e vacinação em dia."
    ),
    (
        "Avaliação médica ocupacional com eletrocardiograma e hemograma normais "
        "para emissão de ASO admissional sem restrições funcionais."
    ),
    (
        "Paciente assintomática busca orientação nutricional preventiva e "
        "solicitação de mamografia de rastreamento bienal recomendada por "
        "idade."
    ),
    (
        "Queixa de coriza hialina discreta, prurido nasal e espirros eventuais "
        "há 2 dias, afebril, bom estado geral, hidratado e ativo."
    ),
    (
        "Dermatite de contato leve em punho por uso de bijuteria, com prurido "
        "localizado e eritema superficial sem sinais de infecção secundária."
    ),
    (
        "Consulta para atestado médico de aptidão física para prática de "
        "musculação e natação em academia recreativa."
    ),
    (
        "Retirada de pontos cirúrgicos de sutura realizada há 10 dias em "
        "antebraço; ferida operatória limpa, seca e com cicatrização ideal."
    ),
    (
        "Queixa de dor muscular tardia (mialgia leve) em membros inferiores 24 "
        "horas após primeira aula de pilates, sem edema ou limitação grave."
    ),
    (
        "Episódio isolado de pirose e desconforto epigástrico leve após "
        "refeição condimentada, sem vômitos, disfagia ou perda de peso."
    ),
    (
        "Paciente de 28 anos com nevo melanocítico cutâneo em dorso de padrão "
        "estável há anos, solicitando avaliação dermatológica eletiva."
    ),
    (
        "Cefaleia tensional leve no final da tarde relacionada a estresse "
        "laboral no computador, aliviada prontamente com paracetamol comum."
    ),
    (
        "Orientação médica sobre atualização do calendário vacinal do viajante "
        "antes de viagem de férias para região do Pantanal."
    ),
]

# ==============================================================================
# Gerador Procedural de Laudos (Variações Combinatórias Infinitas)
# ==============================================================================

PERFIS_PACIENTE = [
    "Paciente masculino, {idade} anos",
    "Paciente feminina, {idade} anos",
    "Mulher de {idade} anos",
    "Homem de {idade} anos",
    "Idoso de {idade} anos",
    "Idosa de {idade} anos",
    "Jovem de {idade} anos",
    "Criança de {idade} anos",
]

COMORBIDADES = [
    ("com histórico de hipertensão arterial e tabagismo ativo."),
    ("sem antecedentes mórbidos relevantes prévios."),
    ("portador de diabetes mellitus tipo 2 controlado em uso de metformina."),
    ("com antecedente de asma leve intermitente."),
    ("sem comorbidades conhecidas, previamente hígido."),
    ("com história prévia de dislipidemia e sobrepeso."),
    ("em acompanhamento clínico regular ambulatorial."),
]

TEMPOS_EVOLUCAO = [
    "início agudo há 30 minutos",
    "início súbito há cerca de 1 hora",
    "com piora progressiva há 3 horas",
    "evolução há 12 horas",
    "quadro iniciado há 24 horas",
    "queixa com início há 3 dias",
    "sintomas há cerca de 1 semana",
    "evolução arrastada há mais de 15 dias",
]

SINAIS_VITAIS_CRITICOS = [
    ("Sinais vitais: PA 75x40 mmHg, FC 142 bpm, FR 32 irpm, SpO2 83%."),
    ("Parâmetros: PA 60x30 mmHg inaudível, pulso filiforme, SpO2 80%."),
    ("Exame físico: Escala Glasgow 8, extremidades cianóticas e frias."),
    ("Hemodinâmica: PA 210x125 mmHg, FC 115 bpm, sudorese fria profusa."),
]

SINAIS_VITAIS_ESTAVEIS = [
    ("Sinais vitais completamente estáveis: PA 120x80 mmHg, FC 72 bpm, SpO2 98%."),
    ("Parâmetros normais: PA 115x75 mmHg, FC 68 bpm, Tax 36.4C."),
    ("Bom estado geral, acianótico, anictérico, eupneico e orientado."),
    ("Exame físico geral sem alterações patológicas detectáveis."),
]


def gerar_laudo_procedural(categoria: str) -> str:
    """Gera laudo único combinando perfil, evolução e contexto fisiológico."""
    if categoria == "urgente":
        idade = random.choice([random.randint(45, 88), random.randint(18, 40)])
        perfil = random.choice(PERFIS_PACIENTE).format(idade=idade)
        tempo = random.choice(TEMPOS_EVOLUCAO[:4])
        caso_base = random.choice(CASOS_EMERGENCIAIS)
        sv = random.choice(SINAIS_VITAIS_CRITICOS)
        comorb = random.choice(COMORBIDADES)
        if random.random() < 0.5:
            return f"{perfil}, {comorb} Apresenta {caso_base} {sv}"
        return f"{caso_base} Quadro com {tempo}. {sv}"

    elif categoria == "atencao":
        idade = random.randint(4, 78)
        perfil = random.choice(PERFIS_PACIENTE).format(idade=idade)
        tempo = random.choice(TEMPOS_EVOLUCAO[2:6])
        caso_base = random.choice(CASOS_ATENCAO)
        comorb = random.choice(COMORBIDADES)
        if random.random() < 0.5:
            return f"{perfil} {comorb} Queixa principal: {caso_base} Relata {tempo}."
        return f"{caso_base} {perfil}."

    else:  # normal
        idade = random.randint(18, 65)
        perfil = random.choice(PERFIS_PACIENTE).format(idade=idade)
        caso_base = random.choice(CASOS_ROTINA)
        sv = random.choice(SINAIS_VITAIS_ESTAVEIS)
        if random.random() < 0.5:
            return f"{perfil}. {caso_base} {sv}"
        return f"{caso_base} {sv}"


def obter_laudo_clinico(categoria: str) -> str:
    """Retorna um laudo autêntico (estático expandido ou gerado proceduramente)."""
    if random.random() < 0.45:
        # Modo procedural: gera laudo inédito e detalhado
        return gerar_laudo_procedural(categoria)

    # Modo estático curado
    if categoria == "urgente":
        return random.choice(CASOS_EMERGENCIAIS)
    elif categoria == "atencao":
        return random.choice(CASOS_ATENCAO)
    else:
        return random.choice(CASOS_ROTINA)


# ==============================================================================
# Modelagem Dinâmica de Padrões de Tráfego e Turnos Hospitalares
# ==============================================================================

TURNOS = [
    {
        "nome": "🌅 Manhã (Fluxo Ambulatorial & Triagem Mista)",
        "pesos": {"normal": 0.45, "atencao": 0.40, "urgente": 0.15},
        "delay_fator": 1.0,
    },
    {
        "nome": "☀️ Tarde (Pico de Pronto-Socorro & Atendimentos)",
        "pesos": {"normal": 0.30, "atencao": 0.50, "urgente": 0.20},
        "delay_fator": 0.8,
    },
    {
        "nome": "🌙 Plantão Noturno (Predomínio de Urgências & Traumas)",
        "pesos": {"normal": 0.20, "atencao": 0.45, "urgente": 0.35},
        "delay_fator": 1.1,
    },
]


def escolher_categoria(turno: dict) -> str:
    """Sorteia a classe de triagem de acordo com os pesos do turno ativo."""
    pesos = turno["pesos"]
    r = random.random()
    if r < pesos["urgente"]:
        return "urgente"
    elif r < pesos["urgente"] + pesos["atencao"]:
        return "atencao"
    return "normal"


# ==============================================================================
# Funções de Comunicação HTTP com a API
# ==============================================================================


def post_prediction(base_url: str, text: str) -> tuple[int, str | None, float]:
    """Envia o texto do laudo para /predict e calcula o tempo de resposta."""
    url = f"{base_url.rstrip('/')}/predict"
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MedicalTriageSimulator/2.0 (DynamicTraffic)",
        },
        method="POST",
    )

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            label = data.get("predicted_label") or data.get("label")
            return resp.status, label, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return e.code, None, elapsed_ms
    except Exception:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return 0, None, elapsed_ms


def ping_endpoint(base_url: str, path: str) -> int:
    """Envia requisição GET para endpoints auxiliares (health, metrics, docs)."""
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MedicalTriageSimulator/2.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# ==============================================================================
# Loops de Execução (Lote e Contínuo)
# ==============================================================================


def run_batch(base_url: str, count: int, base_delay: float) -> None:
    """Executa um lote de testes com variação de categorias e sinais vitais."""
    print(f"🚀 Enviando lote dinâmico de {count} laudos para {base_url}...")
    turno = TURNOS[0]
    label_counts: Counter[str] = Counter()
    latencies: list[float] = []
    successes = 0

    for i in range(1, count + 1):
        cat = escolher_categoria(turno)
        report = obter_laudo_clinico(cat)
        status, predicted_label, lat_ms = post_prediction(base_url, report)

        if status == 200 and predicted_label:
            successes += 1
            label_counts[predicted_label] += 1
            latencies.append(lat_ms)
            print(
                f"[{i:03d}/{count}] HTTP {status} "
                f"| Inferência: {predicted_label:<8} "
                f"| Latência: {lat_ms:5.1f}ms "
                f"| Texto: {report[:45]}..."
            )
        else:
            print(f"[{i:03d}/{count}] HTTP {status} (Falha na requisição)")

        if i % 5 == 0:
            ping_endpoint(base_url, "/health")
            ping_endpoint(base_url, "/metrics")

        if base_delay > 0:
            # Jitter aleatório realista
            jitter = random.uniform(0.6, 1.4)
            time.sleep(base_delay * jitter)

    print("=" * 65)
    print(f"📊 Lote finalizado: {successes}/{count} sucessos")
    print(f"🏥 Distribuição inferida pelo modelo: {dict(label_counts)}")
    if latencies:
        print(f"⚡ Latência Média da API: {sum(latencies) / len(latencies):.2f}ms")


def run_continuous(base_url: str, base_delay: float) -> None:
    """Executa o gerador contínuo com alternância de turnos e rajadas realistas."""
    print(f"🔄 Gerador de tráfego contínuo iniciado em {base_url}", flush=True)
    print(
        f"⚡ Intervalo base: {base_delay}s (com jitter e rajadas dinâmicas)",
        flush=True,
    )

    step = 0
    turno_idx = 0

    while True:
        step += 1

        # A cada 35 requisições, avança para o próximo turno hospitalar
        if step % 35 == 1:
            turno = TURNOS[turno_idx % len(TURNOS)]
            turno_idx += 1
            print(f"\n⏰ Mudança de Ciclo Hospitalar: {turno['nome']}", flush=True)
            print(f"📈 Proporções estimadas: {turno['pesos']}\n", flush=True)

        # A cada 75 requisições: gera payload inválido para registrar HTTP 422
        if step % 75 == 0:
            status, _, lat_ms = post_prediction(base_url, "")
            print(
                f"[{time.strftime('%X')}] #{step:05d} [PROVA 422] -> "
                f"HTTP {status} ({lat_ms:.1f}ms)",
                flush=True,
            )
            time.sleep(1.0)
            continue

        # Simulação de Rajada (Burst): 20% de chance de chegar 2 a 3 pacientes
        is_burst = random.random() < 0.20
        burst_size = random.randint(2, 3) if is_burst else 1

        for b in range(burst_size):
            cat = escolher_categoria(turno)
            report = obter_laudo_clinico(cat)
            status, label, lat_ms = post_prediction(base_url, report)

            tag = " [BURST] " if burst_size > 1 else " "
            print(
                f"[{time.strftime('%X')}] #{step:05d}{tag}-> HTTP {status} "
                f"| {label or 'erro':<8} ({lat_ms:5.1f}ms) "
                f"| {report[:50]}...",
                flush=True,
            )

            if burst_size > 1 and b < burst_size - 1:
                time.sleep(random.uniform(0.2, 0.6))

        # Acessos auxiliares esporádicos para registrar tráfego em outros endpoints
        if step % 4 == 0:
            ping_endpoint(base_url, "/health")
        if step % 6 == 0:
            ping_endpoint(base_url, "/metrics")
        if step % 18 == 0:
            ping_endpoint(base_url, "/docs")

        # Intervalo com Jitter e modulação pelo turno
        delay_fator = turno.get("delay_fator", 1.0)
        sleep_time = max(1.0, base_delay * delay_fator * random.uniform(0.6, 1.4))
        time.sleep(sleep_time)


# ==============================================================================
# Ponto de Entrada (CLI)
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador Dinâmico de Tráfego Clínico — Medical Triage API"
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
        default=5.0,
        help="Delay base entre requisições (padrão: 5.0s)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Executa em loop contínuo simulando chegada periódica de pacientes",
    )
    args = parser.parse_args()

    if args.continuous:
        run_continuous(args.url, base_delay=args.delay if args.delay > 0.5 else 5.0)
    else:
        run_batch(args.url, count=args.count, base_delay=args.delay)


if __name__ == "__main__":
    main()
