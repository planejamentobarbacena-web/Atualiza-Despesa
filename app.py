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
# CONFIGURAÇÃO
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
def normalizar(txt):
    return re.sub(r"\s+", " ", str(txt).strip().lower())

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
    _, h = p.wrap(width, 1000)
    p.drawOn(c, x, y - h)
    return y - h

# =========================
# LEITURA DOS DADOS
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
        except:
            continue

        df = df.fillna("")
        data[ano] = df

    return data

# =========================
# INTERFACE
# =========================
st.title("Retificação / Ratificação de Despesa")

data = carregar_dados()

if not data:
    st.warning("Nenhum arquivo encontrado na pasta /data.")
    st.stop()

# --- ENTIDADES (COLUNA A)
entidades = sorted({
    str(v).strip()
    for df in data.values()
    for v in df.iloc[:, 0].dropna().unique()
    if str(v).strip()
})

entidade = st.selectbox("Entidade", entidades)

anos = sorted(data.keys())
ex_prev = st.selectbox("Exercício anterior", anos, index=max(0, len(anos) - 2))
ex_curr = st.selectbox("Exercício atual", anos, index=len(anos) - 1)

numero = st.text_input("Número da despesa")

consultar = st.button("🔍 Consultar")

if not consultar:
    st.stop()

# =========================
# BUSCA
# =========================
df_prev = data[ex_prev].copy()
df_curr = data[ex_curr].copy()

df_prev = df_prev[df_prev.iloc[:, 0].str.strip() == entidade]
df_curr = df_curr[df_curr.iloc[:, 0].str.strip() == entidade]

def localizar_por_numero(df, numero):
    for _, r in df.iterrows():
        if normalizar(r["Número da despesa"]) == normalizar(numero):
            return r
    return None

prev = localizar_por_numero(df_prev, numero)

if prev is None:
    st.error("Despesa não encontrada no exercício anterior.")
    st.stop()

curr = None
for _, r in df_curr.iterrows():
    if (
        normalizar(r["Descrição da ação"]) == normalizar(prev["Descrição da ação"])
        and normalizar(r["Descrição da natureza de despesa"]) == normalizar(prev["Descrição da natureza de despesa"])
    ):
        curr = r
        break
# =========================
# SALVA RESULTADO NO SESSION_STATE
# =========================
st.session_state["prev"] = prev
st.session_state["curr"] = curr
st.session_state["entidade"] = entidade
st.session_state["ex_prev"] = ex_prev
st.session_state["ex_curr"] = ex_curr

# =========================
# RESULTADO (POR LINHA)
# =========================
def mostrar_resultado_simples(row, ano):
    st.markdown(f"### Exercício {ano}")
    st.markdown(f"**Exercício:** {ano}")
    st.markdown(f"**Número da despesa:** {row['Número da despesa']}")
    st.markdown(f"**Entidade:** {entidade}")

    st.markdown(
        f"""
{row['Número da função']} . {row['Número da subfunção']} . {row['Número do programa']} . {row['Número da ação']} - {row['Descrição da ação']}  
{row['Natureza de Despesa']} - {row['Descrição da natureza de despesa']}
"""
    )

st.subheader("Resultado da Comparação")

st.markdown("#### Exercício anterior")
mostrar_resultado_simples(prev, ex_prev)

if curr is not None:
    st.markdown("---")
    st.markdown("#### Exercício atual")
    mostrar_resultado_simples(curr, ex_curr)
else:
    st.warning("Não existe despesa correspondente no exercício atual.")

# =========================
# PDF (SEM RERUN)
# =========================
if "curr" in st.session_state and st.session_state["curr"] is not None:

    prev = st.session_state["prev"]
    curr = st.session_state["curr"]
    entidade = st.session_state["entidade"]
    ex_prev = st.session_state["ex_prev"]
    ex_curr = st.session_state["ex_curr"]

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60
    margem_x = 50
    largura_texto = width - 2 * margem_x

    # ===== TÍTULO =====
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, "RETIFICAÇÃO – RATIFICAÇÃO")
    y -= 22
    c.drawCentredString(width / 2, y, "NÚMERO CADASTRAL DE DESPESA")
    y -= 30

    # ===== DATA =====
    from datetime import datetime
    data_atual = datetime.now().strftime("%d/%m/%Y")
    c.setFont("Helvetica", 11)
    c.drawRightString(width - margem_x, y, f"Data: {data_atual}")
    y -= 30

    # ===== TEXTO INICIAL =====
    texto_inicial = (
        "A presente manifestação tem por finalidade retificar ou ratificar "
        "o número cadastral da despesa, conforme comparação entre os exercícios analisados."
    )
    y = draw_paragraph(c, texto_inicial, margem_x, y, largura_texto)
    y -= 20

    # ===== ENTIDADE =====
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_x, y, f"Entidade: {entidade}")
    y -= 30

    # ===== ORIGEM =====
    c.drawString(margem_x, y, "Origem")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(margem_x, y, f"Exercício: {ex_prev}")
    y -= 16
    c.drawString(margem_x, y, f"Número da despesa: {prev['Número da despesa']}")
    y -= 22

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_x, y, "Dotação orçamentária:")
    y -= 18

    c.setFont("Helvetica", 11)
    y = draw_paragraph(
        c,
        f"{prev['Número da função']} . {prev['Número da subfunção']} . "
        f"{prev['Número do programa']} . {prev['Número da ação']} - "
        f"{prev['Descrição da ação']}",
        margem_x, y, largura_texto
    )
    y -= 6

    y = draw_paragraph(
        c,
        f"{prev['Natureza de Despesa']} - {prev['Descrição da natureza de despesa']}",
        margem_x, y, largura_texto
    )
    y -= 30

    # ===== ATUALIZAÇÃO =====
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_x, y, "Atualização")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(margem_x, y, f"Exercício: {ex_curr}")
    y -= 16
    c.drawString(margem_x, y, f"Número da despesa: {curr['Número da despesa']}")
    y -= 22

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_x, y, "Dotação orçamentária:")
    y -= 18

    c.setFont("Helvetica", 11)
    y = draw_paragraph(
        c,
        f"{curr['Número da função']} . {curr['Número da subfunção']} . "
        f"{curr['Número do programa']} . {curr['Número da ação']} - "
        f"{curr['Descrição da ação']}",
        margem_x, y, largura_texto
    )
    y -= 6

    y = draw_paragraph(
        c,
        f"{curr['Natureza de Despesa']} - {curr['Descrição da natureza de despesa']}",
        margem_x, y, largura_texto
    )
    y -= 30

    # ===== TEXTO FINAL =====
    texto_final = (
        "Quanto à Fonte de Recurso, considerar a mesma da Declaração Orçamentária original."
    )
    y = draw_paragraph(c, texto_final, margem_x, y, largura_texto)
    y -= 40

    # ===== ASSINATURA =====
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, "Diretoria de Planejamento Orçamentário")

    c.showPage()
    c.save()
    buffer.seek(0)

    st.download_button(
        "📄 Baixar PDF",
        buffer,
        file_name=f"Retificacao_Despesa_{ex_curr}.pdf",
        mime="application/pdf"
    )
