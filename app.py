import streamlit as st
import pandas as pd
import os
import re
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIGURAÇÕES INICIAIS
# =========================
st.set_page_config(
    page_title="Retificação / Ratificação de Despesa",
    layout="centered"
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

styles = getSampleStyleSheet()

# =========================
# FUNÇÕES AUXILIARES
# =========================
def normalizar(texto):
    return re.sub(r"\s+", " ", str(texto).strip().lower())

def reduzir_natureza(codigo):
    nums = re.sub(r"\D", "", str(codigo))
    if len(nums) < 6:
        return codigo
    return f"{nums[0]}.{nums[1]}.{nums[2:4]}.{nums[4:6]}"

def draw_paragraph(c, text, x, y, width):
    style = styles["Normal"]
    style.fontName = "Helvetica"
    style.fontSize = 11
    style.leading = 14

    p = Paragraph(text.replace("\n", "<br/>"), style)
    w, h = p.wrap(width, 1000)
    p.drawOn(c, x, y - h)
    return y - h

# =========================
# LEITURA DOS ARQUIVOS
# =========================
@st.cache_data(show_spinner=False)
def carregar_dados():
    data = {}

    for fname in os.listdir(DATA_DIR):
        if not fname.lower().endswith((".xlsx", ".xls", ".csv")):
            continue

        match = re.search(r"(20\d{2})", fname)
        if not match:
            continue

        ano = match.group(1)
        path = os.path.join(DATA_DIR, fname)

        try:
            if fname.endswith(".csv"):
                df = pd.read_csv(path, dtype=str)
            else:
                df = pd.read_excel(path, dtype=str)
        except Exception:
            continue

        df = df.fillna("")
        data[ano] = df

    return data

# =========================
# PDF
# =========================
def gerar_pdf(prev, curr):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, "RETIFICAÇÃO / RATIFICAÇÃO")
    y -= 25
    c.drawCentredString(width / 2, y, "NÚMERO CADASTRAL DE DESPESA")
    y -= 40

    texto_inicial = (
        "A presente manifestação tem por finalidade retificar ou ratificar "
        "o número cadastral da despesa, conforme comparação entre os exercícios analisados."
    )
    y = draw_paragraph(c, texto_inicial, 50, y, width - 100)
    y -= 30

    # --- EXERCÍCIO ANTERIOR ---
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Dotação Orçamentária Anterior:")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Despesa nº: {prev['numero']} - Exercício: {prev['ano']}")
    y -= 18

    y = draw_paragraph(
        c,
        f"{prev['funcao']} . {prev['subfuncao']} . {prev['programa']} . "
        f"{prev['acao']} - {prev['descricao_acao']}",
        50, y, width - 100
    )
    y -= 10

    y = draw_paragraph(
        c,
        f"<b>{reduzir_natureza(prev['natureza'])}</b> - {prev['descricao_natureza']}",
        50, y, width - 100
    )
    y -= 30

    # --- EXERCÍCIO ATUAL ---
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Dotação Orçamentária Atual:")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Despesa nº: {curr['numero']} - Exercício: {curr['ano']}")
    y -= 18

    y = draw_paragraph(
        c,
        f"{curr['funcao']} . {curr['subfuncao']} . {curr['programa']} . "
        f"{curr['acao']} - {curr['descricao_acao']}",
        50, y, width - 100
    )
    y -= 10

    y = draw_paragraph(
        c,
        f"<b>{reduzir_natureza(curr['natureza'])}</b> - {curr['descricao_natureza']}",
        50, y, width - 100
    )

    y -= 40
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, "Diretoria de Planejamento Orçamentário")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# =========================
# INTERFACE
# =========================
st.title("Retificação / Ratificação de Despesa")

data = carregar_dados()

if not data:
    st.warning("Nenhum arquivo encontrado na pasta /data.")
    st.stop()

# ---- ENTIDADES (COLUNA A)
entidades = sorted({
    str(valor).strip()
    for df in data.values()
    for valor in df.iloc[:, 0].dropna().unique()
    if str(valor).strip()
})

entidade = st.selectbox("Entidade", entidades)

anos = sorted(data.keys())
ex_prev = st.selectbox("Exercício anterior", anos, index=max(0, len(anos) - 2))
ex_curr = st.selectbox("Exercício atual", anos, index=len(anos) - 1)

numero = st.text_input("Número da despesa")

if not entidade or not numero:
    st.info("Selecione a entidade e informe o número da despesa.")
    st.stop()

# =========================
# BUSCA
# =========================
df_prev = data[ex_prev].copy()
df_curr = data[ex_curr].copy()

df_prev = df_prev[df_prev.iloc[:, 0].str.strip() == entidade]
df_curr = df_curr[df_curr.iloc[:, 0].str.strip() == entidade]

def localizar(df, numero):
    for _, r in df.iterrows():
        if normalizar(r["Número da despesa"]) == normalizar(numero):
            return r
    return None

prev_row = localizar(df_prev, numero)

if prev_row is None:
    st.error("Despesa não encontrada no exercício anterior.")
    st.stop()

curr_row = None
for _, r in df_curr.iterrows():
    if (
        normalizar(r["Descrição do programa"]) == normalizar(prev_row["Descrição do programa"])
        and normalizar(r["Descrição da natureza de despesa"]) == normalizar(prev_row["Descrição da natureza de despesa"])
    ):
        curr_row = r
        break

st.subheader("Resultado da Comparação")

st.markdown("**Exercício anterior**")
st.write(prev_row)

if curr_row is not None:
    st.markdown("**Exercício atual**")
    st.write(curr_row)

    pdf = gerar_pdf(
        {
            "ano": ex_prev,
            "numero": prev_row["Número da despesa"],
            "funcao": prev_row["Número da função"],
            "subfuncao": prev_row["Número da subfunção"],
            "programa": prev_row["Descrição do programa"],
            "acao": prev_row["Número da ação"],
            "descricao_acao": prev_row["Descrição do programa"],
            "natureza": prev_row["Natureza de Despesa"],
            "descricao_natureza": prev_row["Descrição da natureza de despesa"],
        },
        {
            "ano": ex_curr,
            "numero": curr_row["Número da despesa"],
            "funcao": curr_row["Número da função"],
            "subfuncao": curr_row["Número da subfunção"],
            "programa": curr_row["Descrição do programa"],
            "acao": curr_row["Número da ação"],
            "descricao_acao": curr_row["Descrição do programa"],
            "natureza": curr_row["Natureza de Despesa"],
            "descricao_natureza": curr_row["Descrição da natureza de despesa"],
        }
    )

    st.download_button(
        "📄 Gerar PDF",
        data=pdf,
        file_name=f"Retificacao_Despesa_{ex_curr}.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Não existe despesa correspondente no exercício atual.")
