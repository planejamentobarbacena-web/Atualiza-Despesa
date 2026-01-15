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

    margem_x = 50
    largura_texto = width - 2 * margem_x

    # =========================
    # LOGO (ACIMA DO TÍTULO)
    # =========================
    logo_path = os.path.join("static", "logo_secretaria.png")

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(
            logo,
            x=(width - 80) / 2,
            y=height - 110,
            width=80,
            height=80,
            mask="auto"
        )

    y = height - 140

    # =========================
    # TÍTULO
    # =========================
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, "RETIFICAÇÃO – RATIFICAÇÃO")
    y -= 22
    c.drawCentredString(width / 2, y, "NÚMERO CADASTRAL DE DESPESA")
    y -= 30

    # =========================
    # DATA
    # =========================
    data_atual = datetime.now().strftime("%d/%m/%Y")
    c.setFont("Helvetica", 11)
    c.drawRightString(width - margem_x, y, f"Data: {data_atual}")
    y -= 30

    # =========================
    # TEXTO INTRODUTÓRIO
    # =========================
    texto_inicial = (
        "A presente manifestação tem por finalidade retificar ou ratificar "
        "o número cadastral da despesa, conforme comparação entre os exercícios analisados."
    )
    y = draw_paragraph(c, texto_inicial, margem_x, y, largura_texto)
    y -= 20

    # =========================
    # ENTIDADE
    # =========================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_x, y, f"Entidade: {entidade}")
    y -= 30

    # =========================
    # ORIGEM
    # =========================
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

    # =========================
    # ATUALIZAÇÃO
    # =========================
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

    # =========================
    # TEXTO FINAL
    # =========================
    texto_final = (
        "Quanto à Fonte de Recurso, considerar a mesma da Declaração Orçamentária original."
    )
    y = draw_paragraph(c, texto_final, margem_x, y, largura_texto)
    y -= 40

    # =========================
    # ASSINATURA
    # =========================
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
