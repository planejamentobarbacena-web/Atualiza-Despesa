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
# PDF
# =========================
if curr is not None:
    gerar_pdf = st.button("📄 Gerar PDF")

    if gerar_pdf:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, y, "RETIFICAÇÃO / RATIFICAÇÃO DE DESPESA")
        y -= 40

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Entidade: {entidade}")
        y -= 20

        c.drawString(50, y, f"Despesa anterior: {prev['Número da despesa']} - Exercício {ex_prev}")
        y -= 20

        y = draw_paragraph(
            c,
            f"{prev['Descrição da ação']}<br/>{prev['Descrição da natureza de despesa']}",
            50, y, width - 100
        )

        y -= 30
        c.drawString(50, y, f"Despesa atual: {curr['Número da despesa']} - Exercício {ex_curr}")
        y -= 20

        y = draw_paragraph(
            c,
            f"{curr['Descrição da ação']}<br/>{curr['Descrição da natureza de despesa']}",
            50, y, width - 100
        )

        y -= 40
        c.drawCentredString(width / 2, y, "Diretoria de Planejamento Orçamentário")

        c.showPage()
        c.save()
        buffer.seek(0)

        st.download_button(
            "⬇️ Baixar PDF",
            buffer,
            file_name=f"Retificacao_Despesa_{ex_curr}.pdf",
            mime="application/pdf"
        )

