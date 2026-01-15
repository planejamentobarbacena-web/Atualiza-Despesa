import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Comparação de Despesa", layout="centered")

st.title("Consulta de Despesa")

# =========================================================
# FUNÇÃO – MONTA TEXTO DO BLOCO
# =========================================================
def montar_bloco(dados, titulo):
    st.subheader(titulo)
    st.write(f"**Exercício:** {dados['exercicio']}")
    st.write(f"**Número da despesa:** {dados['numero_despesa']}")
    st.write(f"**Entidade:** {dados['entidade']}")

    st.markdown(
        f"""
{dados['funcao']} · {dados['subfuncao']} · {dados['programa']} · {dados['acao']} – {dados['descricao_acao']}  
{dados['natureza']} – {dados['descricao_natureza']}
"""
    )

# =========================================================
# FORMULÁRIO
# =========================================================
with st.form("consulta"):
    numero_despesa = st.text_input("Número da despesa")
    consultar = st.form_submit_button("Consultar")

# =========================================================
# RESULTADO
# =========================================================
if consultar and numero_despesa:

    # 🔹 EXEMPLO (depois você liga ao CSV real)
    exercicio_anterior = {
        "exercicio": "2023",
        "numero_despesa": numero_despesa,
        "entidade": "Prefeitura Municipal",
        "funcao": "04",
        "subfuncao": "122",
        "programa": "0001",
        "acao": "2001",
        "descricao_acao": "Manutenção das Atividades Administrativas",
        "natureza": "3.3.90.39",
        "descricao_natureza": "Outros Serviços de Terceiros – PJ"
    }

    exercicio_atual = {
        "exercicio": "2024",
        "numero_despesa": numero_despesa,
        "entidade": "Prefeitura Municipal",
        "funcao": "04",
        "subfuncao": "122",
        "programa": "0001",
        "acao": "2001",
        "descricao_acao": "Manutenção das Atividades Administrativas",
        "natureza": "3.3.90.39",
        "descricao_natureza": "Outros Serviços de Terceiros – PJ"
    }

    st.divider()
    montar_bloco(exercicio_anterior, "Exercício anterior")

    st.divider()
    montar_bloco(exercicio_atual, "Exercício atual")

    # =====================================================
    # PDF
    # =====================================================
    def gerar_pdf():
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        y = altura - 50

        pdf.setFont("Helvetica", 10)

        for titulo, dados in [
            ("Exercício anterior", exercicio_anterior),
            ("Exercício atual", exercicio_atual)
        ]:
            pdf.drawString(40, y, titulo)
            y -= 18

            pdf.drawString(40, y, f"Exercício: {dados['exercicio']}")
            y -= 14
            pdf.drawString(40, y, f"Número da despesa: {dados['numero_despesa']}")
            y -= 14
            pdf.drawString(40, y, f"Entidade: {dados['entidade']}")
            y -= 18

            linha1 = (
                f"{dados['funcao']} · {dados['subfuncao']} · "
                f"{dados['programa']} · {dados['acao']} – {dados['descricao_acao']}"
            )
            linha2 = (
                f"{dados['natureza']} – {dados['descricao_natureza']}"
            )

            pdf.drawString(40, y, linha1)
            y -= 14
            pdf.drawString(40, y, linha2)
            y -= 30

        pdf.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = gerar_pdf()

    st.download_button(
        label="📄 Gerar PDF",
        data=pdf_buffer,
        file_name="comparacao_despesa.pdf",
        mime="application/pdf"
    )
