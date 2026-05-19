
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

# ─── Equipamentos da fazenda ───────────────────────────────────────────────
EQUIPAMENTOS = [
    {"id": 1, "nome": "Pivô Central A", "tipo": "irrigacao", "potencia_kw": 75.0},
    {"id": 2, "nome": "Pivô Central B", "tipo": "irrigacao", "potencia_kw": 60.0},
    {"id": 3, "nome": "Silo Secador 1", "tipo": "secagem", "potencia_kw": 45.0},
    {"id": 4, "nome": "Silo Secador 2", "tipo": "secagem", "potencia_kw": 40.0},
    {"id": 5, "nome": "Trator Elétrico Alpha", "tipo": "trator", "potencia_kw": 30.0},
    {"id": 6, "nome": "Trator Elétrico Beta", "tipo": "trator", "potencia_kw": 30.0},
    {"id": 7, "nome": "Ordenhadeira Robótica", "tipo": "ordenha", "potencia_kw": 15.0},
    {"id": 8, "nome": "Câmara Fria Grãos", "tipo": "refrigeracao", "potencia_kw": 20.0},
]

# ─── Funções de simulação ──────────────────────────────────────────────────
def irradiancia_solar(hora, mes):
    """Irradiância em W/m² simulada por hora e mês (Brasil Central)."""
    if hora < 6 or hora >= 19:
        return 0.0
    pico = 950 + (mes in [10, 11, 12, 1, 2]) * 80 - (mes in [6, 7]) * 120
    curva = np.sin(np.pi * (hora - 6) / 13) ** 1.4
    ruido = np.random.normal(1.0, 0.08)
    return max(0.0, pico * curva * ruido)

def geracao_solar_kwh(irradiancia, area_paineis_m2=180, eficiencia=0.195):
    """Geração solar em kWh para o intervalo de 15 minutos."""
    potencia_w = irradiancia * area_paineis_m2 * eficiencia
    return round(potencia_w / 1000 * 0.25, 4)  # 15 min = 0.25h

def tarifa_horaria(hora, dia_semana):
    """Retorna tarifa em R$/kWh (bandeira verde + ANEEL pico/fora pico)."""
    if dia_semana >= 5:  # fim de semana
        return 0.58
    if 18 <= hora < 21:  # horário de ponta
        return 1.42
    if 6 <= hora < 18:  # intermediário
        return 0.74
    return 0.52  # madrugada

def fator_operacao(equip_tipo, hora, mes, dia_semana):
    """Probabilidade de o equipamento estar ligado neste momento."""
    if equip_tipo == "irrigacao":
        if mes in [3, 4, 5, 9]:  # entressafra: irrigação reduzida
            return 0.3 if 8 <= hora < 18 else 0.05
        return 0.7 if 8 <= hora < 18 else 0.15
    if equip_tipo == "secagem":
        if mes in [6, 7, 8]:  # safra soja/milho: secagem intensa
            return 0.85 if 6 <= hora < 22 else 0.4
        return 0.2
    if equip_tipo == "trator":
        return 0.6 if (6 <= hora < 18 and dia_semana < 5) else 0.05
    if equip_tipo == "ordenha":
        return 0.9 if hora in [5, 6, 14, 15, 16] else 0.1
    if equip_tipo == "refrigeracao":
        temp_fator = 1.2 if mes in [11, 12, 1, 2, 3] else 0.8
        return min(0.95, 0.7 * temp_fator)
    return 0.5

def consumo_kwh(potencia_kw, operando, equip_tipo):
    """Consumo em kWh para 15 minutos com variação realista."""
    if not operando:
        standby = potencia_kw * 0.015  # stand-by ~1.5%
        return round(standby * 0.25 * np.random.uniform(0.8, 1.2), 4)
    fator = np.random.normal(0.82, 0.07)
    fator = np.clip(fator, 0.55, 1.0)
    if equip_tipo == "irrigacao":
        fator *= np.random.uniform(0.9, 1.1)  # variação por pressão
    return round(potencia_kw * fator * 0.25, 4)

def classificar_risco(consumo_kwh_total, solar_kwh, tarifa, hora):
    """
    Classifica o risco energético do período:
      0 = eficiente  (solar cobre demanda, tarifa baixa)
      1 = atenção    (tarifa intermediária ou solar parcial)
      2 = crítico    (pico de tarifa e/ou alta demanda sem solar)
    """
    cobertura_solar = solar_kwh / (consumo_kwh_total + 1e-6)
    if tarifa >= 1.20 and consumo_kwh_total > 10:
        return 2
    if tarifa >= 0.90 or (consumo_kwh_total > 15 and cobertura_solar < 0.2):
        return 2
    if tarifa >= 0.65 or cobertura_solar < 0.4:
        return 1
    return 0

def score_risco(classe, consumo, solar, tarifa):
    """Score 0–100 contínuo baseado na classe e magnitudes."""
    base = {0: 10, 1: 45, 2: 78}[classe]
    penalidade_tarifa = (tarifa - 0.52) / (1.42 - 0.52) * 20
    penalidade_solar = max(0, 1 - solar / (consumo + 1e-6)) * 10
    score = base + penalidade_tarifa + penalidade_solar
    score += np.random.normal(0, 3)
    return int(np.clip(score, 0, 100))

# ─── Gerar registros ───────────────────────────────────────────────────────
def gerar_dataset(dias=60):
    print(f"Gerando dataset de {dias} dias × {len(EQUIPAMENTOS)} equipamentos × 96 leituras/dia...")
    registros = []
    inicio = datetime(2024, 5, 1, 0, 0)

    for d in range(dias):
        dt_base = inicio + timedelta(days=d)
        mes = dt_base.month
        dia_semana = dt_base.weekday()

        for hora in range(24):
            for minuto in [0, 15, 30, 45]:
                ts = dt_base + timedelta(hours=hora, minutes=minuto)
                irrad = irradiancia_solar(hora, mes)
                solar = geracao_solar_kwh(irrad)
                tarifa = tarifa_horaria(hora, dia_semana)
                temp_amb = 22 + 8 * np.sin(np.pi * hora / 14) + (mes in [11,12,1,2]) * 4 + np.random.normal(0, 1.5)
                consumo_total = 0.0

                for eq in EQUIPAMENTOS:
                    p_oper = fator_operacao(eq["tipo"], hora, mes, dia_semana)
                    operando = random.random() < p_oper
                    cons = consumo_kwh(eq["potencia_kw"], operando, eq["tipo"])
                    consumo_total += cons

                    classe = classificar_risco(cons, solar, tarifa, hora)
                    sc = score_risco(classe, cons, solar, tarifa)

                    registros.append({
                        "equipamento_id": eq["id"],
                        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "hora": hora,
                        "minuto": minuto,
                        "dia_semana": dia_semana,
                        "mes": mes,
                        "operando": int(operando),
                        "consumo_kwh": cons,
                        "solar_kwh": round(solar, 4),
                        "irradiancia_wm2": round(irrad, 2),
                        "tarifa_rs_kwh": tarifa,
                        "temperatura_c": round(temp_amb, 1),
                        "cobertura_solar_pct": round(min(1.0, solar / (cons + 1e-6)) * 100, 1),
                        "classe_risco": classe,
                        "score_risco": sc,
                        "custo_rs": round(cons * tarifa, 4),
                    })

    df = pd.DataFrame(registros)
    print(f"  Total de registros: {len(df):,}")
    print(f"  Período: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"  Consumo total: {df['consumo_kwh'].sum():,.1f} kWh")
    print(f"  Custo total simulado: R$ {df['custo_rs'].sum():,.2f}")
    print(f"  Distribuição de classes:")
    for c, n in df['classe_risco'].value_counts().sort_index().items():
        label = ['eficiente', 'atenção', 'crítico'][c]
        print(f"    {c} ({label}): {n:,} ({n/len(df)*100:.1f}%)")
    return df

# ─── Salvar CSV ────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # Pasta raiz do projeto (AGRO_ENERGY)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Pasta dep já existente
    DEP_DIR = os.path.join(BASE_DIR, "dep")

    # Gera dataset
    df = gerar_dataset(dias=60)

    # Caminho do CSV
    csv_path = os.path.join(DEP_DIR, "leituras_energia.csv")

    # Salva CSV dentro de /dep
    df.to_csv(csv_path, index=False)

    print(f"\nDataset salvo em: {csv_path}")