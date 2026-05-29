# 🌾 AGROENERGY — Inteligência Energética Agrícola
### Challenge FIAP × Sompo Seguros — Sprint 2

> Sistema de monitoramento e predição de risco energético para frotas e equipamentos agrícolas, com banco de dados Oracle, modelos de Machine Learning e dashboard interativo.

---

## 📋 Sumário

1. [Visão Geral da Solução](#visão-geral-da-solução)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Tecnologias Utilizadas](#tecnologias-utilizadas)
4. [Estrutura do Repositório](#estrutura-do-repositório)
5. [Módulos e Integração](#módulos-e-integração)
6. [Modelo de IA — Random Forest](#modelo-de-ia--random-forest)
7. [Validação Estatística](#validação-estatística)
8. [Banco de Dados Oracle](#banco-de-dados-oracle)
9. [Dashboard](#dashboard)
10. [Como Executar](#como-executar)
11. [Evolução em Relação à Sprint 1](#evolução-em-relação-à-sprint-1)
12. [Integrantes](#integrantes)
13. [Vídeo de Apresentação](#vídeo-de-apresentação)

---

## Visão Geral da Solução

O **AGROENERGY** é uma plataforma de inteligência energética voltada para o agronegócio. A solução monitora o consumo de energia elétrica de equipamentos agrícolas (pivôs de irrigação, silos secadores, tratores elétricos, ordenhadeiras e câmaras frias), cruza esse consumo com dados de geração solar fotovoltaica e tarifas horárias da rede elétrica, e aplica Machine Learning para **classificar o risco energético** de cada operação em tempo real.

### Problema Endereçado

A Sompo Seguros enfrenta alta imprevisibilidade de riscos operacionais em frotas agrícolas. O AGROENERGY atua na prevenção: ao identificar padrões de consumo crítico, tarifas de pico e baixo aproveitamento solar, o sistema gera alertas antes que os custos ou incidentes se materializem, **mudando a gestão de reativa para preventiva**.

### Saídas do Sistema

- **Score de Risco** (0–100) por equipamento e período
- **Classificação**: Eficiente (0) / Atenção (1) / Crítico (2)
- **Alertas** de tarifa de ponta, baixa solar e alto consumo
- **Recomendações** de janelas ideais de operação
- **Dashboard visual** com gráficos de consumo, custo e risco

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE DE DADOS                        │
│                                                             │
│  [Sensores / Simulação]                                     │
│         │                                                   │
│         ▼                                                   │
│  gerar_dados.py ──► leituras_energia.csv                    │
│         │                                                   │
│         ▼                                                   │
│  banco_sql.py ──► Oracle DB (FIAP)                         │
│         │              │                                    │
│         │    ┌──────────┘                                   │
│         ▼    ▼                                              │
│  modelo_ia.py ──► random_forest.pkl                        │
│         │                                                   │
│         ▼                                                   │
│  dashboard.py ──► Interface Tkinter (Usuário Final)        │
└─────────────────────────────────────────────────────────────┘
```

**Fluxo:** Dados brutos de sensores → Processamento Python → Persistência Oracle → Modelo ML → Visualização em Dashboard

---

## Tecnologias Utilizadas

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.13 |
| Machine Learning | scikit-learn (RandomForestClassifier) |
| Banco de Dados | Oracle Database (FIAP) via `oracledb` |
| Serialização do Modelo | `joblib` |
| Manipulação de Dados | `pandas`, `numpy` |
| Dashboard | `tkinter`, `matplotlib`, `seaborn` |
| Geração de Dados | Simulação determinística com `random.seed(42)` |

---

## Estrutura do Repositório

```
AGRO_ENERGY/
├── dep/
│   └── leituras_energia.csv       # Dataset simulado (46.080 registros)
├── models/
│   └── random_forest.pkl          # Modelo treinado serializado
├── scr/
│   ├── gerar_dados.py             # Geração do dataset simulado
│   ├── banco_sql.py               # Conexão e população do Oracle
│   ├── modelo_ia.py               # Treinamento do Random Forest
│   └── dashboard.py               # Interface visual Tkinter
├── assets/                        # Imagens e prints de execução
└── README.md
```

---

## Módulos e Integração

### `gerar_dados.py` — Simulação de Dados
Simula 60 dias de operação de 8 equipamentos agrícolas com granularidade de 15 minutos (96 leituras/dia por equipamento), totalizando **46.080 registros**.

Variáveis geradas por registro:
- `equipamento_id`, `timestamp`, `hora`, `minuto`, `dia_semana`, `mes`
- `operando` — status ligado/desligado (baseado em probabilidade por tipo e hora)
- `consumo_kwh` — consumo no período com variação realista por tipo
- `solar_kwh` / `irradiancia_wm2` — geração solar fotovoltaica (180 m², eficiência 19,5%)
- `tarifa_rs_kwh` — tarifa ANEEL (pico: R$1,42 | intermediário: R$0,74 | madrugada: R$0,52)
- `temperatura_c` — temperatura ambiente com variação sazonal
- `cobertura_solar_pct` — percentual do consumo coberto pela geração solar
- `classe_risco` (0/1/2) — label de classificação
- `score_risco` (0–100) — score contínuo de risco
- `custo_rs` — custo monetário do período

**Resultados da simulação:**
- Período: 2024-05-01 → 2024-06-29
- Consumo total: 126.765,0 kWh
- Custo total simulado: R$ 89.500,88
- Distribuição: 12,4% eficiente | 77,9% atenção | 9,7% crítico

### `banco_sql.py` — Oracle Database
Conecta ao Oracle FIAP e cria 5 tabelas relacionais:

- **`equipamentos`** — cadastro dos 8 equipamentos com tipo e potência
- **`leituras_energia`** — série temporal completa (46.080 registros)
- **`score_risco_diario`** — agregação diária de risco por equipamento
- **`alertas`** — registro de alertas gerados pelo sistema
- **`previsoes`** — previsões futuras de consumo e risco

Utiliza `executemany` para inserção em batch, garantindo performance.

### `modelo_ia.py` — Random Forest Classifier
Treina um modelo supervisionado para classificar o risco energético.

**Features de entrada (9):**
`hora`, `dia_semana`, `mes`, `operando`, `consumo_kwh`, `solar_kwh`, `irradiancia_wm2`, `tarifa_rs_kwh`, `temperatura_c`

**Target:** `classe_risco` (0 = eficiente, 1 = atenção, 2 = crítico)

**Hiperparâmetros:** `n_estimators=150`, `max_depth=12`, `random_state=42`

**Justificativa técnica do Random Forest:** O algoritmo foi escolhido por sua robustez a outliers, capacidade de lidar com variáveis de escalas distintas sem normalização prévia, interpretabilidade via feature importance, e desempenho superior em datasets tabulares com features mistas (contínuas + categóricas). Comparado a Regressão Logística, captura não-linearidades críticas como a interação entre tarifa de pico e cobertura solar. Comparado a XGBoost, oferece treino mais rápido e menor risco de overfitting para o tamanho do dataset.

### `dashboard.py` — Interface Visual
Interface desktop em Tkinter com tema AGROENERGY (fundo preto / neon verde), integrando o modelo treinado para inferência em tempo real.

**Telas disponíveis:**
1. Painel Principal — Score e classe atual
2. Consumo × Solar — Gráfico de linha por hora
3. Risco Energético — Distribuição das classes
4. Aproveitamento Solar — Histograma com KDE
5. Custos — Custo total por equipamento
6. Alertas — Alertas ativos do sistema
7. Recomendações IA — Sugestões baseadas no score atual
8. Estatísticas — `df.describe()` completo
9. Random Forest — Métricas do modelo

---

## Modelo de IA — Random Forest

### Treinamento
- Split: 80% treino / 20% teste (`random_state=42`)
- Registros de treino: ~36.864 | Teste: ~9.216

### Resultados

```
Acurácia: 99,92%

              precision    recall  f1-score   support
           0     1.00      1.00      1.00      1165
           1     1.00      1.00      1.00      7155
           2     1.00      1.00      1.00       896
    accuracy                         1.00      9216
   macro avg     1.00      1.00      1.00      9216
weighted avg     1.00      1.00      1.00      9216
```

> **Nota técnica:** A alta acurácia é esperada dado que as labels `classe_risco` foram geradas deterministicamente pelas mesmas variáveis usadas como features. Isso demonstra consistência interna do pipeline — em produção, as labels viriam de registros históricos de incidentes reais da Sompo, e o modelo seria retreinado com esses dados supervisionados.

---

## Validação Estatística

### Correlações entre variáveis principais

| Variável | Correlação com `classe_risco` |
|----------|-------------------------------|
| `tarifa_rs_kwh` | Alta positiva — tarifas de pico elevam diretamente o risco |
| `cobertura_solar_pct` | Alta negativa — maior cobertura solar reduz o risco |
| `consumo_kwh` | Moderada positiva — consumo alto em pico é crítico |
| `hora` | Moderada — horas de ponta (18h–21h) correlacionam com risco crítico |
| `irradiancia_wm2` | Moderada negativa — mais sol = menor risco |
| `temperatura_c` | Baixa — influência indireta via demanda de refrigeração |

### Distribuição das Classes
- **Eficiente (0):** 5.733 registros — 12,4% — operação com solar cobrindo demanda e tarifa baixa
- **Atenção (1):** 35.900 registros — 77,9% — situação intermediária mais frequente
- **Crítico (2):** 4.447 registros — 9,7% — horário de ponta + alta demanda + baixa solar

### Definição das Faixas de Risco

| Score | Classe | Condição |
|-------|--------|----------|
| 0–30 | Eficiente | Solar cobre demanda, tarifa abaixo de R$0,65, cobertura > 40% |
| 31–70 | Atenção | Tarifa intermediária ou cobertura solar parcial |
| 71–100 | Crítico | Tarifa ≥ R$1,20 + consumo > 10 kWh, ou tarifa ≥ R$0,90 + cobertura < 20% |

---

## Banco de Dados Oracle

**Servidor:** oracle.fiap.com.br:1521/ORCL

**Tabelas criadas e populadas:**

| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| `equipamentos` | 8 | Cadastro dos equipamentos agrícolas |
| `leituras_energia` | 46.080 | Série temporal completa de consumo |
| `score_risco_diario` | — | Agregação diária por equipamento |
| `alertas` | — | Alertas gerados pelo sistema |
| `previsoes` | — | Previsões futuras do modelo |

**Evidência de execução:** Oracle SQL Developer mostrando tabela `LEITURAS_ENERGIA` com 17 colunas e conexão ativa ao servidor FIAP.

---

## Dashboard

Interface desktop desenvolvida em Tkinter com tema visual inspirado em terminais de missão crítica (fundo preto, tipografia monoespaçada, acentos neon verde).

**Integração com IA:** O dashboard carrega o `random_forest.pkl` via `joblib` e executa `predict_proba()` sobre o último registro do dataset para gerar o score e a classe em tempo real.

**Prints de execução:** disponíveis na pasta `/assets` do repositório.

---

## Como Executar

### Pré-requisitos
```bash
pip install pandas numpy scikit-learn joblib oracledb matplotlib seaborn
```

### Ordem de execução

```bash
# 1. Gerar o dataset simulado
python scr/gerar_dados.py

# 2. Popular o banco Oracle
python scr/banco_sql.py

# 3. Treinar o modelo de IA
python scr/modelo_ia.py

# 4. Abrir o dashboard
python scr/dashboard.py
```

## Evolução em Relação à Sprint 1

| Entregável | Sprint 1 | Sprint 2 |
|-----------|----------|----------|
| Arquitetura | Conceitual / Diagrama | Implementada e funcional |
| Dados | Planejamento de variáveis | 46.080 registros simulados |
| Banco de Dados | Modelagem de tabelas | Oracle populado com dados reais |
| Modelo de IA | Definição do algoritmo | Random Forest treinado (99,92% acurácia) |
| Dashboard | Wireframe | Interface Tkinter funcional com 9 telas |
| Integração | Inexistente | Pipeline completo: CSV → Oracle → ML → Dashboard |

---

## Integrantes

| Nome | RM |
| CARLOS ANDERSON PARROT SILVA | rm573950 |

---

## Vídeo de Apresentação

🎬 **Link:** _(https://youtube.com/shorts/BCxDFeuG8X8)_

--
