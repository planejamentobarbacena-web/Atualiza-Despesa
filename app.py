from flask import Flask, render_template, request, send_file
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

# =========================================================
# FUNÇÃO – FORMATA BLOCO DO EXERCÍCIO (2 LINHAS)
# =========================================================
def montar_bloco(dados, titulo):
    return {
        "titulo": titulo,
        "exercicio": dados["exercicio"],
        "numero_despesa": dados["numero_despesa"],
        "entidade": dados["entidade"],
        "linha1": (
            f"{dados['funcao']} · {dados['subfuncao']} · "
            f"{dados['programa']} · {dados['acao']} – {dados['descricao_acao']}"
        ),
        "linha2": (
            f"{dados['natureza']} – {dados['descricao_natureza']}"
        )
    }

# =========================================================
# ROTA PRINCIPAL
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None

    if request.method == "POST":
        numero_despesa = request.form.get("numero_despesa")

        # 🔹 EXEMPLO – depois você liga ao CSV/DataFrame real
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

        resultado = [
            montar_bloco(exercicio_anterior, "Exercício anterior"),
            montar_bloco(exercicio_atual, "Exercício atual")
        ]

    return render_template("index.html", resultado=resultado)

# =========================================================
# PDF
# =========================================================
@app.route("/gerar_pdf")
def gerar_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    y = altura - 50
    pdf.setFont("Helvetica", 10)

    dados = [
        {
            "titulo": "Exercício anterior",
            "exercicio": "2023",
            "numero_despesa": "12345",
            "entidade": "Prefeitura Municipal",
            "linha1": "04 · 122 · 0001 · 2001 – Manutenção das Atividades Administrativas",
            "linha2": "3.3.90.39 – Outros Serviços de Terceiros – PJ"
        },
        {
            "titulo": "Exercício atual",
            "exercicio": "2024",
            "numero_despesa": "12345",
            "entidade": "Prefeitura Municipal",
            "linha1": "04 · 122 · 0001 · 2001 – Manutenção das Atividades Administrativas",
            "linha2": "3.3.90.39 – Outros Serviços de Terceiros – PJ"
        }
    ]

    for bloco in dados:
        pdf.drawString(40, y, bloco["titulo"])
        y -= 18

        pdf.drawString(40, y, f"Exercício: {bloco['exercicio']}")
        y -= 14
        pdf.drawString(40, y, f"Número da despesa: {bloco['numero_despesa']}")
        y -= 14
        pdf.drawString(40, y, f"Entidade: {bloco['entidade']}")
        y -= 18

        pdf.drawString(40, y, bloco["linha1"])
        y -= 14
        pdf.drawString(40, y, bloco["linha2"])
        y -= 30

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="comparativo_despesa.pdf",
        mimetype="application/pdf"
    )

# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
