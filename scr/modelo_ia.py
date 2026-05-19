import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ─────────────────────────────────────────────────────────────
# CAMINHOS
# ─────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEP_DIR = os.path.join(BASE_DIR, "dep")

MODELS_DIR = os.path.join(BASE_DIR, "models")

CSV_PATH = os.path.join(DEP_DIR, "leituras_energia.csv")

MODEL_PATH = os.path.join(MODELS_DIR, "random_forest.pkl")

os.makedirs(MODELS_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# CARREGAR DATASET
# ─────────────────────────────────────────────────────────────

print("Lendo dataset...")

df = pd.read_csv(CSV_PATH)

print(f"{len(df):,} registros carregados.")

# ─────────────────────────────────────────────────────────────
# FEATURES
# ─────────────────────────────────────────────────────────────

features = [
    "hora",
    "dia_semana",
    "mes",
    "operando",
    "consumo_kwh",
    "solar_kwh",
    "irradiancia_wm2",
    "tarifa_rs_kwh",
    "temperatura_c"
]

X = df[features]

y = df["classe_risco"]

# ─────────────────────────────────────────────────────────────
# TREINO / TESTE
# ─────────────────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# ─────────────────────────────────────────────────────────────
# MODELO RANDOM FOREST
# ─────────────────────────────────────────────────────────────

print("\nTreinando Random Forest...")

modelo = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

modelo.fit(X_train, y_train)

# ─────────────────────────────────────────────────────────────
# AVALIAÇÃO
# ─────────────────────────────────────────────────────────────

print("\nTestando modelo...")

y_pred = modelo.predict(X_test)

acc = accuracy_score(y_test, y_pred)

print(f"\nAcurácia: {acc * 100:.2f}%")

print("\nRelatório de Classificação:\n")

print(classification_report(y_test, y_pred))

# ─────────────────────────────────────────────────────────────
# SALVAR MODELO
# ─────────────────────────────────────────────────────────────

joblib.dump(modelo, MODEL_PATH)

print(f"\nModelo salvo em:\n{MODEL_PATH}")