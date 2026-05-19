import tkinter as tk
from tkinter import ttk
from tkinter import font

import pandas as pd
import numpy as np
import joblib
import os

import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =========================================================
# CAMINHOS
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEP_DIR = os.path.join(BASE_DIR, "dep")
MODELS_DIR = os.path.join(BASE_DIR, "models")

CSV_PATH = os.path.join(DEP_DIR, "leituras_energia.csv")
MODEL_PATH = os.path.join(MODELS_DIR, "random_forest.pkl")

# =========================================================
# FUNDO GRID
# =========================================================

class FundoGrid:

    def __init__(self, canvas, largura, altura):

        espacamento = 80
        tamanho = 2

        for i in range(0, largura, espacamento):
            for j in range(0, altura, espacamento):

                canvas.create_oval(
                    i,
                    j,
                    i + tamanho,
                    j + tamanho,
                    fill="#00FF88",
                    outline=""
                )

# =========================================================
# DASHBOARD
# =========================================================

class AgroDashboard:

    def __init__(self, root):

        self.root = root
        self.root.title("AGROENERGY AI")
        self.root.geometry("1600x950")
        self.root.configure(bg="black")

        self.usuario = os.getlogin().upper()

        # =====================================================
        # FONTES
        # =====================================================

        self.font_titulo = font.Font(
            family="OCR A Extended",
            size=32,
            weight="bold"
        )

        self.font_sub = font.Font(
            family="OCR A Extended",
            size=12,
            weight="bold"
        )

        # =====================================================
        # CANVAS
        # =====================================================

        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        FundoGrid(self.canvas, 1600, 950)

        self.canvas.create_rectangle(
            10, 10, 1590, 940,
            outline="#00FF88",
            width=2
        )

        # =====================================================
        # TITULO
        # =====================================================

        self.label_titulo = tk.Label(
            root,
            text="AGROENERGY DASHBOARD",
            fg="white",
            bg="black",
            font=self.font_titulo
        )

        self.label_titulo.place(relx=0.5, y=50, anchor="center")

        self.label_sub = tk.Label(
            root,
            text=f"USUÁRIO: {self.usuario} | IA ENERGÉTICA AGRÍCOLA",
            fg="#00FF88",
            bg="black",
            font=self.font_sub
        )

        self.label_sub.place(relx=0.5, y=110, anchor="center")

        # =====================================================
        # LINHA
        # =====================================================

        linha = tk.Frame(root, bg="#00FF88", height=2)
        linha.place(x=40, y=145, width=1520)

        # =====================================================
        # MENU
        # =====================================================

        self.frame_menu = tk.Frame(
            root,
            bg="black",
            highlightbackground="#00FF88",
            highlightthickness=2
        )

        self.frame_menu.place(x=40, y=180, width=320, height=720)

        # =====================================================
        # DASHBOARD
        # =====================================================

        self.frame_dashboard = tk.Frame(
            root,
            bg="black",
            highlightbackground="#00FF88",
            highlightthickness=2
        )

        self.frame_dashboard.place(x=390, y=180, width=1170, height=720)

        # =====================================================
        # DADOS
        # =====================================================

        self.df = pd.read_csv(CSV_PATH)

        self.modelo = joblib.load(MODEL_PATH)

        # =====================================================
        # BOTÕES
        # =====================================================

        botoes = [

            ("⚡ VISÃO GERAL", self.visao_geral),
            ("📊 CONSUMO x SOLAR", self.grafico_consumo_solar),
            ("⚠️ RISCO ENERGÉTICO", self.grafico_risco),
            ("🌞 APROVEITAMENTO SOLAR", self.grafico_solar),
            ("💰 CUSTOS", self.grafico_custos),
            ("🚨 ALERTAS", self.alertas),
            ("🤖 RECOMENDAÇÕES IA", self.recomendacoes_ia),
            ("📈 ESTATÍSTICAS", self.estatisticas),
            ("🌲 RANDOM FOREST", self.random_forest),
            ("🚪 SAIR", self.root.destroy)

        ]

        for texto, comando in botoes:

            btn = tk.Button(
                self.frame_menu,
                text=texto,
                command=comando,
                fg="#00FF88",
                bg="black",
                activebackground="#002211",
                activeforeground="#00FF88",
                font=("OCR A Extended", 10, "bold"),
                width=26,
                height=2,
                highlightbackground="#00FF88",
                highlightthickness=2,
                relief="flat",
                cursor="hand2"
            )

            btn.pack(pady=10)

        self.visao_geral()

    # =====================================================
    # LIMPAR
    # =====================================================

    def limpar_dashboard(self):

        for widget in self.frame_dashboard.winfo_children():
            widget.destroy()

    # =====================================================
    # FIGURA
    # =====================================================

    def mostrar_figura(self, fig):

        self.limpar_dashboard()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_dashboard)

        canvas.draw()

        canvas.get_tk_widget().pack(fill="both", expand=True)

    # =====================================================
    # SCORE IA
    # =====================================================

    def obter_score(self):

        ultimo = self.df.iloc[-1]

        features = [[
            ultimo["hora"],
            ultimo["dia_semana"],
            ultimo["mes"],
            ultimo["operando"],
            ultimo["consumo_kwh"],
            ultimo["solar_kwh"],
            ultimo["irradiancia_wm2"],
            ultimo["tarifa_rs_kwh"],
            ultimo["temperatura_c"]
        ]]

        probabilidades = self.modelo.predict_proba(features)[0]

        score = int(probabilidades[2] * 100)

        classe = ["EFICIENTE", "ATENÇÃO", "CRÍTICO"][
            np.argmax(probabilidades)
        ]

        return score, classe

    # =====================================================
    # VISÃO GERAL
    # =====================================================

    def visao_geral(self):

        self.limpar_dashboard()

        score, classe = self.obter_score()

        ultimo = self.df.iloc[-1]

        frame = tk.Frame(
            self.frame_dashboard,
            bg="black"
        )

        frame.pack(fill="both", expand=True)

        titulo = tk.Label(
            frame,
            text="PAINEL PRINCIPAL",
            fg="#00FF88",
            bg="black",
            font=("OCR A Extended", 24, "bold")
        )

        titulo.pack(pady=30)

        infos = [

            f"SCORE DE RISCO: {score}/100",
            f"CLASSE: {classe}",
            f"CONSUMO ATUAL: {ultimo['consumo_kwh']:.2f} kWh",
            f"GERAÇÃO SOLAR: {ultimo['solar_kwh']:.2f} kWh",
            f"TARIFA: R$ {ultimo['tarifa_rs_kwh']:.2f}",
            f"COBERTURA SOLAR: {ultimo['cobertura_solar_pct']:.1f}%"

        ]

        for info in infos:

            lbl = tk.Label(
                frame,
                text=info,
                fg="white",
                bg="black",
                font=("OCR A Extended", 16)
            )

            lbl.pack(pady=10)

    # =====================================================
    # CONSUMO x SOLAR
    # =====================================================

    def grafico_consumo_solar(self):

        dados = self.df.groupby("hora").agg({
            "consumo_kwh": "mean",
            "solar_kwh": "mean"
        }).reset_index()

        fig, ax = plt.subplots(figsize=(12,6))

        ax.plot(
            dados["hora"],
            dados["consumo_kwh"],
            linewidth=3,
            label="Consumo"
        )

        ax.plot(
            dados["hora"],
            dados["solar_kwh"],
            linewidth=3,
            label="Solar"
        )

        ax.set_title("Consumo x Geração Solar")

        ax.legend()

        self.mostrar_figura(fig)

    # =====================================================
    # RISCO
    # =====================================================

    def grafico_risco(self):

        fig, ax = plt.subplots(figsize=(10,6))

        sns.countplot(
            data=self.df,
            x="classe_risco",
            hue="classe_risco",
            palette="viridis",
            legend=False,
            ax=ax
        )

        ax.set_title("Distribuição de Risco Energético")

        self.mostrar_figura(fig)

    # =====================================================
    # SOLAR
    # =====================================================

    def grafico_solar(self):

        fig, ax = plt.subplots(figsize=(10,6))

        sns.histplot(
            self.df["cobertura_solar_pct"],
            bins=30,
            kde=True,
            ax=ax
        )

        ax.set_title("Aproveitamento Solar")

        self.mostrar_figura(fig)

    # =====================================================
    # CUSTOS
    # =====================================================

    def grafico_custos(self):

        dados = self.df.groupby("equipamento_id")["custo_rs"].sum()

        fig, ax = plt.subplots(figsize=(10,6))

        ax.bar(
            dados.index.astype(str),
            dados.values
        )

        ax.set_title("Custo por Equipamento")

        self.mostrar_figura(fig)

    # =====================================================
    # ALERTAS
    # =====================================================

    def alertas(self):

        self.limpar_dashboard()

        txt = tk.Text(
            self.frame_dashboard,
            bg="black",
            fg="#00FF88",
            font=("OCR A Extended", 12)
        )

        txt.pack(fill="both", expand=True)

        mensagens = [

            "⚠️ Tarifa de pico detectada",
            "⚠️ Baixa geração solar",
            "⚠️ Alto consumo energético",
            "⚠️ Horário crítico operacional",
            "⚠️ Considere mover irrigação para 10h–14h"

        ]

        for msg in mensagens:

            txt.insert("end", f"{msg}\n\n")

    # =====================================================
    # IA
    # =====================================================

    def recomendacoes_ia(self):

        self.limpar_dashboard()

        score, classe = self.obter_score()

        txt = tk.Text(
            self.frame_dashboard,
            bg="black",
            fg="#00FF88",
            font=("OCR A Extended", 13)
        )

        txt.pack(fill="both", expand=True)

        if score >= 80:

            recomendacao = """

RISCO CRÍTICO DETECTADO

• Não ligar pivôs neste momento
• Tarifa de ponta ativa
• Baixa cobertura solar

Economia estimada:
R$ 48 nas próximas 2h

Sugestão:
Mover operação para 10h–14h
"""

        elif score >= 50:

            recomendacao = """

RISCO MODERADO

• Operação permitida
• Priorizar equipamentos essenciais
• Aproveitamento solar parcial
"""

        else:

            recomendacao = """

OPERAÇÃO IDEAL

• Alta geração solar
• Baixo custo energético
• Momento eficiente para operação
"""

        txt.insert("end", recomendacao)

    # =====================================================
    # ESTATÍSTICAS
    # =====================================================

    def estatisticas(self):

        self.limpar_dashboard()

        txt = tk.Text(
            self.frame_dashboard,
            bg="black",
            fg="#00FF88"
        )

        txt.pack(fill="both", expand=True)

        txt.insert("end", str(self.df.describe()))

    # =====================================================
    # RANDOM FOREST
    # =====================================================

    def random_forest(self):

        self.limpar_dashboard()

        tree = ttk.Treeview(
            self.frame_dashboard,
            columns=("item", "valor"),
            show="headings"
        )

        tree.heading("item", text="MÉTRICA")
        tree.heading("valor", text="VALOR")

        tree.pack(fill="both", expand=True)

        score, classe = self.obter_score()

        dados = [

            ("Modelo", "Random Forest"),
            ("Features", "9"),
            ("Classes", "3"),
            ("Score Atual", f"{score}/100"),
            ("Classe Atual", classe),
            ("Dataset", f"{len(self.df):,} registros")

        ]

        for d in dados:

            tree.insert("", "end", values=d)

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = AgroDashboard(root)

    root.mainloop()