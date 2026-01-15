import streamlit as st
import pandas as pd
import os, re
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------------
# CONFIG STREAMLIT
# ----------------------------
st.set_page_config(
    page_title="Retificação de Despesa",
    layout="centered"
)

# ----------------------------
# PASTAS
# ----------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ----------------------------
# UTILIDADES
# ----------------------------
def reduzir_natureza(codigo):
    nums = re.sub(r"\D", "", str(codigo))
    if len(nums) < 6:
        return codigo
    return f"{nums[0]}.{nums[1]}.{nums[2:4]}.{nums[4:6]}"

styles = getSampleStyleSheet()

def draw_paragraph(c, text, x, y, width):
    style = styles["Normal"]
    style.fontName = "Helvetica"
    style.fontSize = 11
    style.leading = 14

    p = Paragraph(text, style)
    w, h = p.wrap(width, 1000)
    p.drawOn(c, x, y - h)
    return y - h

# ----------------------------
# LEITURA DOS DADOS
# ----------------------------
@st.cache_data
def read_all_data():
    data = {}

    for fname in os.listdir(DATA_DIR):
        if not fname.lower().endswith((".xlsx", ".xls", ".csv")):
            continue

        m = re.search(r"(20\d{2})", fname)
        if not m:
            continue

        year = m.group(1)
        path = os.path.join(DATA_DIR, fname)

        df = pd.read_excel(path, dtype=str).fillna("")

        # padroniza nomes das colunas
        df.columns = df.columns.str.strip()

        data[year] = df

    return data

# ----------------------------
# PDF
# ----------------------------
def gerar_pdf(prev, curr, entidade):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, "RETIFICAÇÃO / RATIFICAÇÃO")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y, entidade)
    y -= 40

    texto_intro = (
        "A presente manifestação tem por finalidade retificar ou ratificar "
        "o número cadastral da despesa, conforme comparação entre os exercícios analisados."
    )
    y = draw_paragraph(c, texto_intro, 50, y, width - 100)
    y -= 30

    # Exercício anterior
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Dotação Orçamentária Anterior:")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(
        50, y,
        f"Despesa nº {prev['Número da despesa']} – Exercício {prev['exercicio']}"
    )
    y -= 20

    natureza_prev = reduzir_natureza(prev["Natureza de Despesa"])
    y = draw_paragraph(
        c,
        f"<b>{natureza_prev}</b> – {prev['Descrição da natureza de despesa']}",
        50, y, width - 100
    )

    y -= 30

    # Exercício atual
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Dotação Orçamentária Atual:")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(
        50, y,
        f"Despesa nº {curr['Número da despesa']} – Exercício {curr['exercicio']}"
    )
    y -= 20

    natureza_curr = reduzir_natureza(curr["Natureza de Despesa"])
    y = draw_paragraph(
        c,
        f"<b>{natureza_curr}</b> – {curr['Descrição da natureza de despesa']}",
        50, y, width - 100
    )

    y -= 40
    c.drawCentredString(width / 2, y, "Diretoria de Planejamento Orçamentário")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ----------------------------
# INTERFACE
# ----------------------------
st.title("Retificação / Ratificação de Despesa")

data = read_all_data()
anos = sorted(data.keys())

# 🔹 Lista de entidades (coluna A)
entidades = sorted(
    set(
        df.iloc[:, 0].str.strip()
        for df in data.values()
        for _ in [0]
    ).pop()
)

entidade = st.selectbox("Entidade", sorted(set(
    e for df in data.values() for e in df.iloc[:, 0].unique()
)))

col1, col2 = st.columns(2)
with col1:
    ex_prev = st.selectbox("Exercício anterior", anos)
with col2:
    ex_curr = st.selectbox("Exercício atual", anos)

numero = st.text_input("Número da despesa")

if st.button("Buscar"):
    df_prev = data[ex_prev]
    df_curr = data[ex_curr]

    # 🔒 FILTRO POR ENTIDADE (COLUNA A)
    df_prev = df_prev[df_prev.iloc[:, 0] == entidade]
    df_curr = df_curr[df_curr.iloc[:, 0] == entidade]

    prev = df_prev[df_prev["Número da despesa"] == numero]

    if prev.empty:
        st.error("Despesa não encontrada para a entidade selecionada.")
    else:
        prev_row = prev.iloc[0].to_dict()
        prev_row["exercicio"] = ex_prev

        curr = df_curr[
            (df_curr["Descrição do programa"] == prev_row["Descrição do programa"]) &
            (df_curr["Descrição da natureza de despesa"] == prev_row["Descrição da natureza de despesa"])
        ]

        if curr.empty:
            st.warning("Não existe despesa correspondente no exercício atual para esta entidade.")
        else:
            curr_row = curr.iloc[0].to_dict()
            curr_row["exercicio"] = ex_curr

            st.success("Despesa localizada corretamente para a entidade selecionada.")

            pdf = gerar_pdf(prev_row, curr_row, entidade)
            st.download_button(
                "📄 Gerar PDF",
                pdf,
                file_name=f"Retificacao_Despesa_{entidade}_{ex_curr}.pdf",
                mime="application/pdf"
            )
