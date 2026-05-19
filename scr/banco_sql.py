
import os
import pandas as pd
import oracledb

# ────────────────────────────────────────────────────────────────────────────
# CAMINHOS DO PROJETO
# ────────────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEP_DIR = os.path.join(BASE_DIR, "dep")

CSV_PATH = os.path.join(DEP_DIR, "leituras_energia.csv")

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO ORACLE
# ────────────────────────────────────────────────────────────────────────────

ORACLE_CONFIG = {
    "user": "RM573950",
    "password": "110699",
    "dsn": "oracle.fiap.com.br:1521/ORCL"
}

# ────────────────────────────────────────────────────────────────────────────
# EQUIPAMENTOS
# ────────────────────────────────────────────────────────────────────────────

EQUIPAMENTOS = [
    (1, "Pivô Central A", "irrigacao", 75.0),
    (2, "Pivô Central B", "irrigacao", 60.0),
    (3, "Silo Secador 1", "secagem", 45.0),
    (4, "Silo Secador 2", "secagem", 40.0),
    (5, "Trator Elétrico Alpha", "trator", 30.0),
    (6, "Trator Elétrico Beta", "trator", 30.0),
    (7, "Ordenhadeira Robótica", "ordenha", 15.0),
    (8, "Câmara Fria Grãos", "refrigeracao", 20.0),
]

# ────────────────────────────────────────────────────────────────────────────
# CONEXÃO ORACLE
# ────────────────────────────────────────────────────────────────────────────

def conectar():

    return oracledb.connect(
        user=ORACLE_CONFIG["user"],
        password=ORACLE_CONFIG["password"],
        dsn=ORACLE_CONFIG["dsn"]
    )

# ────────────────────────────────────────────────────────────────────────────
# CRIAÇÃO DAS TABELAS
# ────────────────────────────────────────────────────────────────────────────

def criar_tabelas(cursor):

    tabelas = [

        """
        CREATE TABLE equipamentos (
            id                  NUMBER PRIMARY KEY,
            nome                VARCHAR2(100) NOT NULL,
            tipo                VARCHAR2(50) NOT NULL,
            potencia_kw         NUMBER(10,2) NOT NULL,
            ativo               NUMBER(1) DEFAULT 1,
            criado_em           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE leituras_energia (
            id                      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            equipamento_id          NUMBER NOT NULL,
            timestamp_leitura       TIMESTAMP NOT NULL,
            hora                    NUMBER,
            minuto                  NUMBER,
            dia_semana              NUMBER,
            mes                     NUMBER,
            operando                NUMBER(1),
            consumo_kwh             NUMBER(10,4),
            solar_kwh               NUMBER(10,4),
            irradiancia_wm2         NUMBER(10,2),
            tarifa_rs_kwh           NUMBER(10,4),
            temperatura_c           NUMBER(10,2),
            cobertura_solar_pct     NUMBER(10,2),
            classe_risco            NUMBER,
            score_risco             NUMBER,
            custo_rs                NUMBER(10,4),

            CONSTRAINT fk_equipamento
            FOREIGN KEY (equipamento_id)
            REFERENCES equipamentos(id)
        )
        """,

        """
        CREATE TABLE score_risco_diario (
            id                          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            equipamento_id              NUMBER NOT NULL,
            data_ref                    DATE NOT NULL,
            score_medio                 NUMBER(10,2),
            score_maximo                NUMBER,
            consumo_total               NUMBER(12,2),
            solar_total                 NUMBER(12,2),
            custo_total                 NUMBER(12,2),
            horas_critico               NUMBER,
            classe_predominante         NUMBER,

            CONSTRAINT fk_score_equip
            FOREIGN KEY (equipamento_id)
            REFERENCES equipamentos(id)
        )
        """,

        """
        CREATE TABLE alertas (
            id                  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            equipamento_id      NUMBER,
            tipo                VARCHAR2(50),
            severidade          VARCHAR2(20),
            mensagem            VARCHAR2(500),
            economia_rs         NUMBER(10,2),
            resolvido           NUMBER(1) DEFAULT 0,
            criado_em           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE previsoes (
            id                      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            equipamento_id          NUMBER NOT NULL,
            gerado_em               TIMESTAMP,
            hora_alvo               TIMESTAMP,
            consumo_previsto        NUMBER(10,2),
            score_previsto          NUMBER,
            recomendacao            VARCHAR2(500)
        )
        """
    ]

    for sql in tabelas:

        try:
            cursor.execute(sql)
            print("Tabela criada.")

        except Exception:
            print("Tabela já existe.")

# ────────────────────────────────────────────────────────────────────────────
# INSERIR EQUIPAMENTOS
# ────────────────────────────────────────────────────────────────────────────

def inserir_equipamentos(cursor):

    sql = """
        INSERT INTO equipamentos (
            id,
            nome,
            tipo,
            potencia_kw
        )
        VALUES (
            :1, :2, :3, :4
        )
    """

    for eq in EQUIPAMENTOS:

        try:
            cursor.execute(sql, eq)

        except Exception:
            pass

# ────────────────────────────────────────────────────────────────────────────
# IMPORTAR CSV
# ────────────────────────────────────────────────────────────────────────────

def importar_csv(cursor):

    print("\nLendo CSV...")

    if not os.path.exists(CSV_PATH):

        print(f"CSV não encontrado: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)

    print(f"{len(df):,} registros encontrados.")

    sql = """
        INSERT INTO leituras_energia (
            equipamento_id,
            timestamp_leitura,
            hora,
            minuto,
            dia_semana,
            mes,
            operando,
            consumo_kwh,
            solar_kwh,
            irradiancia_wm2,
            tarifa_rs_kwh,
            temperatura_c,
            cobertura_solar_pct,
            classe_risco,
            score_risco,
            custo_rs
        )
        VALUES (
            :1,:2,:3,:4,:5,:6,:7,:8,
            :9,:10,:11,:12,:13,:14,:15,:16
        )
    """

    dados = []

    for _, row in df.iterrows():

        timestamp_convertido = pd.to_datetime(
            row["timestamp"]
        ).to_pydatetime()

        dados.append((
            int(row["equipamento_id"]),
            timestamp_convertido,
            int(row["hora"]),
            int(row["minuto"]),
            int(row["dia_semana"]),
            int(row["mes"]),
            int(row["operando"]),
            float(row["consumo_kwh"]),
            float(row["solar_kwh"]),
            float(row["irradiancia_wm2"]),
            float(row["tarifa_rs_kwh"]),
            float(row["temperatura_c"]),
            float(row["cobertura_solar_pct"]),
            int(row["classe_risco"]),
            int(row["score_risco"]),
            float(row["custo_rs"])
        ))

    print("Inserindo dados no Oracle...")

    cursor.executemany(sql, dados)

    print("CSV importado com sucesso.")

# ────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────

def main():

    print("=" * 60)
    print("AGROENERGY — ORACLE DATABASE")
    print("=" * 60)

    try:

        print("\nConectando ao Oracle...")

        conn = conectar()

        cursor = conn.cursor()

        print("Conexão realizada.")

        print("\nCriando tabelas...")
        criar_tabelas(cursor)

        print("\nInserindo equipamentos...")
        inserir_equipamentos(cursor)

        print("\nImportando leituras...")
        importar_csv(cursor)

        conn.commit()

        print("\nBanco Oracle populado com sucesso.")

        cursor.close()
        conn.close()

    except Exception as erro:

        print("\nERRO:")
        print(erro)

# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()