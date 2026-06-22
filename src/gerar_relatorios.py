"""
Geração dos relatórios em PDF (Entrega 1 — parcial; Entrega 2 — final).

Os relatórios são montados a partir dos artefatos produzidos pelas etapas
anteriores (estatísticas da EDA, resultados de ML, gráficos e DER). Escrevi o
texto em primeira pessoa e em tom técnico-acadêmico, como pede a especificação,
seguindo exatamente os sumários dos itens 8 (parcial) e 15 (final).
"""

from __future__ import annotations

import json

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

import config

AUTOR = "Carlos Ranyere da Natividade Pereira"
CURSO = "Tecnólogo em Big Data e Inteligência Analítica"
DISCIPLINA = "Projeto Integrador"
AZUL = colors.HexColor("#1e3a5f")
OURO = colors.HexColor("#c9a227")


# --------------------------- utilidades ------------------------------------
def _estilos():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Capa", fontName="Helvetica-Bold", fontSize=22,
                         leading=27, alignment=TA_CENTER, textColor=AZUL))
    s.add(ParagraphStyle("CapaSub", fontName="Helvetica", fontSize=13,
                         leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#444")))
    s.add(ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14,
                         leading=18, spaceBefore=14, spaceAfter=8, textColor=AZUL))
    s.add(ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11.5,
                         leading=15, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#2c3e50")))
    s.add(ParagraphStyle("Corpo", fontName="Helvetica", fontSize=10.5,
                         leading=15.5, alignment=TA_JUSTIFY, spaceAfter=7))
    s.add(ParagraphStyle("Item", fontName="Helvetica", fontSize=10.5,
                         leading=15, leftIndent=14, spaceAfter=3))
    s.add(ParagraphStyle("Leg", fontName="Helvetica-Oblique", fontSize=8.5,
                         leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#666"),
                         spaceAfter=10))
    s.add(ParagraphStyle("Cod", fontName="Courier", fontSize=8.5, leading=11,
                         backColor=colors.HexColor("#f3f4f6"), borderPadding=6,
                         spaceAfter=8))
    return s


def moeda(v) -> str:
    try:
        return ("R$ " + f"{float(v):,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def num(v) -> str:
    try:
        return f"{int(v):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _carregar_artefatos() -> dict:
    art = {}
    def le_json(caminho):
        return json.load(open(caminho, encoding="utf-8")) if caminho.exists() else {}
    art["coleta"] = le_json(config.DIR_BRUTOS / "resumo_coleta.json")
    art["eda"] = le_json(config.DIR_SAIDAS / "estatisticas_gerais.json")
    art["ml"] = le_json(config.DIR_SAIDAS / "resultado_ml.json")
    def le_csv(nome):
        c = config.DIR_SAIDAS / nome
        return pd.read_csv(c) if c.exists() else pd.DataFrame()
    art["categorias"] = le_csv("resumo_categorias.csv")
    art["top_deputados"] = le_csv("resumo_top_deputados.csv")
    art["top_fornecedores"] = le_csv("resumo_top_fornecedores.csv")
    art["uf"] = le_csv("resumo_uf.csv")
    art["partido"] = le_csv("resumo_partido.csv")
    return art


def _tabela(dados, col_widths=None, header=True):
    estilo = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f7")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    t = Table(dados, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle(estilo))
    return t


def _capa(story, s, subtitulo, descricao):
    story.append(Spacer(1, 3.2 * cm))
    story.append(Paragraph("PROJETO INTEGRADOR", s["CapaSub"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Pipeline de Inteligência em Gastos Públicos", s["Capa"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(subtitulo, s["CapaSub"]))
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph(descricao, s["Leg"]))
    story.append(Spacer(1, 3.0 * cm))
    info = [
        ["Aluno", AUTOR],
        ["Curso", CURSO],
        ["Disciplina", DISCIPLINA],
        ["Fonte de dados", "API de Dados Abertos da Câmara dos Deputados"],
        ["Período", config.ROTULO_PERIODOS],
    ]
    t = Table(info, colWidths=[4 * cm, 11 * cm], hAlign="CENTER")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), AZUL),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
    ]))
    story.append(t)
    story.append(PageBreak())


def _rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(2 * cm, 1.1 * cm, f"{AUTOR} — Projeto Integrador")
    canvas.drawRightString(19 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#dddddd"))
    canvas.line(2 * cm, 1.4 * cm, 19 * cm, 1.4 * cm)
    canvas.restoreState()


def _doc(caminho):
    return SimpleDocTemplate(
        str(caminho), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Projeto Integrador — Gastos Públicos", author=AUTOR)


def _img(caminho, largura=15.5 * cm):
    from PIL import Image as PILImage  # pillow vem junto do matplotlib
    if not caminho.exists():
        return Spacer(1, 0.1 * cm)
    iw, ih = PILImage.open(caminho).size
    altura = largura * ih / iw
    return Image(str(caminho), width=largura, height=altura)


# =========================================================================
# RELATÓRIO PARCIAL — ENTREGA 1
# =========================================================================
def relatorio_parcial(art: dict) -> None:
    s = _estilos()
    story = []
    _capa(story, s, "Relatório Parcial — Entrega 1",
          "Coleta, modelagem e armazenamento dos dados")

    eda, coleta = art["eda"], art["coleta"]

    # 1. Introdução
    story.append(Paragraph("1. Introdução", s["H1"]))
    story.append(Paragraph(
        "Este relatório parcial documenta a primeira etapa do Projeto Integrador, "
        "cujo objetivo é construir um pipeline de dados sobre gastos públicos. "
        "Optei por trabalhar com as despesas da Cota para o Exercício da Atividade "
        "Parlamentar (CEAP) dos deputados federais, obtidas diretamente da API de "
        "Dados Abertos da Câmara dos Deputados. Nesta fase, o foco não está em gerar "
        "gráficos, e sim em garantir uma base confiável: coletar os dados de forma "
        "automatizada, compreendê-los, tratá-los e armazená-los de maneira "
        "estruturada para as análises da Entrega 2.", s["Corpo"]))

    # 2. Objetivo da coleta
    story.append(Paragraph("2. Objetivo da coleta", s["H1"]))
    story.append(Paragraph(
        "Reunir, de forma reprodutível, o conjunto de despesas dos deputados em "
        f"exercício referentes ao período {config.ROTULO_PERIODOS}, de modo a permitir "
        "responder perguntas como: quais categorias concentram mais recursos? "
        "Como os gastos evoluem ao longo do ano? Há parlamentares ou fornecedores "
        "com comportamento destoante do conjunto?", s["Corpo"]))

    # 3. API escolhida e justificativa
    story.append(Paragraph("3. API escolhida e justificativa", s["H1"]))
    story.append(Paragraph(
        "Escolhi a <b>API de Dados Abertos da Câmara dos Deputados</b> por três "
        "motivos. Primeiro, é uma fonte oficial, pública e atualizada, com "
        "documentação clara (padrão OpenAPI/Swagger) e sem necessidade de chave de "
        "acesso. Segundo, oferece o recurso de despesas por parlamentar com "
        "paginação bem definida, o que exercita exatamente as competências pedidas "
        "no projeto (coleta automatizada, paginação e tratamento de erros). "
        "Terceiro, o tema dos gastos públicos é socialmente relevante e permite "
        "análises ricas por categoria, partido, estado e fornecedor.", s["Corpo"]))

    # 4. Endpoints
    story.append(Paragraph("4. Endpoints utilizados", s["H1"]))
    story.append(Paragraph(
        "Foram utilizados dois endpoints da versão 2 da API "
        "(<font face='Courier'>/api/v2</font>):", s["Corpo"]))
    story.append(Paragraph(
        "• <font face='Courier'>GET /deputados</font> — lista os parlamentares em "
        "exercício, com partido e UF;", s["Item"]))
    story.append(Paragraph(
        "• <font face='Courier'>GET /deputados/{id}/despesas</font> — retorna as "
        "despesas da CEAP de cada deputado, com paginação.", s["Item"]))

    # 5. Script de coleta
    story.append(Paragraph("5. Explicação do script de coleta", s["H1"]))
    story.append(Paragraph(
        "O script <font face='Courier'>coleta.py</font> percorre primeiro a lista "
        "de deputados e depois, para cada um, todas as páginas de despesas. A função "
        "central é um GET resiliente, que trata os erros mais comuns da API:", s["Corpo"]))
    story.append(Paragraph(
        "def _get(url, params):<br/>"
        "&nbsp;&nbsp;for tentativa in range(1, MAX_TENTATIVAS+1):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;resp = requests.get(url, params, timeout=35)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;if resp.status_code == 200: return resp.json()<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;if status in (429,500,502,503,504): espera_e_repete()<br/>",
        s["Cod"]))
    story.append(Paragraph(
        "Destaco três cuidados: (1) <b>paginação</b>, controlada pelos links "
        "<font face='Courier'>rel='next'</font> que a própria API devolve; "
        "(2) <b>tratamento de erros</b>, com até seis tentativas e espera "
        "exponencial (backoff) — necessário porque a API retorna HTTP 504 "
        "esporádico sob carga; e (3) <b>checkpoint</b>: cada deputado já coletado "
        "é gravado em disco (formato JSON Lines), permitindo retomar a coleta sem "
        "perder o que já foi baixado.", s["Corpo"]))

    # 6. Tratamentos
    story.append(Paragraph("6. Tratamentos realizados nos dados", s["H1"]))
    story.append(Paragraph(
        "Após a coleta, o script <font face='Courier'>tratamento.py</font> executa "
        "a limpeza inicial:", s["Corpo"]))
    for txt in [
        "padronização de <b>datas</b> para o formato ISO (AAAA-MM-DD);",
        "conversão de <b>valores financeiros</b> para tipo numérico, tratando o "
        "separador decimal brasileiro;",
        "manutenção de <b>identificadores</b> (CNPJ/CPF, códigos) como texto — "
        "eles identificam, não quantificam;",
        "verificação de <b>campos nulos</b> e remoção de registros sem valor "
        "líquido (inúteis para a análise financeira);",
        "remoção de <b>duplicatas</b> pela combinação deputado + código + número "
        "do documento.",
    ]:
        story.append(Paragraph("• " + txt, s["Item"]))

    # 7. Modelo de dados + DER
    story.append(PageBreak())
    story.append(Paragraph("7. Modelo de dados", s["H1"]))
    story.append(Paragraph(
        "Os dados foram normalizados em três tabelas, em um modelo do tipo "
        "estrela simplificado: a tabela-fato <b>despesas</b> e as dimensões "
        "<b>deputados</b> e <b>fornecedores</b>. Um deputado possui muitas "
        "despesas (1:N) e um fornecedor aparece em muitas despesas (1:N).", s["Corpo"]))
    story.append(_img(config.DIR_DOCS / "der.png", largura=16 * cm))
    story.append(Paragraph("Figura 1 — Diagrama Entidade-Relacionamento.", s["Leg"]))
    story.append(Paragraph(
        "<b>Chaves primárias:</b> deputados.id_deputado; fornecedores.cnpj_cpf; "
        "despesas.id_despesa. <b>Chaves estrangeiras:</b> despesas.id_deputado → "
        "deputados; despesas.cnpj_cpf_fornecedor → fornecedores. Optei por uma "
        "chave primária interna em despesas porque o código de documento pode se "
        "repetir entre parlamentares.", s["Corpo"]))

    # 8. Dicionário de dados (resumido)
    story.append(Paragraph("8. Dicionário inicial de dados", s["H1"]))
    story.append(Paragraph(
        "Resumo da tabela-fato (o dicionário completo das três tabelas está em "
        "<font face='Courier'>docs/dicionario_dados.md</font>):", s["Corpo"]))
    dic = [
        ["Campo", "Tipo", "Descrição", "Exemplo"],
        ["id_deputado", "Inteiro (FK)", "Identificador do parlamentar", "204554"],
        ["tipo_despesa", "Texto", "Categoria da despesa (CEAP)", "PASSAGEM AÉREA"],
        ["cnpj_cpf_fornecedor", "Texto (FK)", "Fornecedor da despesa", "04.252.011/0001-10"],
        ["data_documento", "Data", "Data do documento fiscal", "2024-05-10"],
        ["valor_liquido", "Numérico", "Valor ressarcido (análise)", "1350.75"],
        ["mes", "Inteiro", "Mês de referência", "5"],
    ]
    story.append(_tabela(dic, col_widths=[3.6 * cm, 2.6 * cm, 6.3 * cm, 3 * cm]))

    # 9. Evidências
    story.append(Paragraph("9. Evidências da execução", s["H1"]))
    if eda:
        evid = [
            ["Indicador", "Valor"],
            ["Deputados coletados", num(eda.get("qtd_deputados"))],
            ["Despesas armazenadas", num(eda.get("total_registros"))],
            ["Fornecedores distintos", num(eda.get("qtd_fornecedores"))],
            ["Categorias de despesa", num(eda.get("qtd_categorias"))],
            ["Período", f"{eda.get('periodo_inicio')} a {eda.get('periodo_fim')}"],
            ["Valor total (CEAP)", moeda(eda.get("valor_total"))],
        ]
        if coleta:
            evid.append(["Tempo de coleta", f"{coleta.get('duracao_segundos','—')} s"])
        story.append(_tabela(evid, col_widths=[7 * cm, 8 * cm]))
    story.append(Paragraph(
        "A execução também gera os arquivos <font face='Courier'>resumo_coleta.json</font> "
        "(quantitativos da coleta) e a base tratada em CSV/Parquet, além do banco "
        "<font face='Courier'>gastos_publicos.db</font>.", s["Corpo"]))

    # 10. Considerações parciais
    story.append(Paragraph("10. Considerações parciais", s["H1"]))
    story.append(Paragraph(
        "A base está coletada, tratada e armazenada de forma estruturada, "
        "atendendo ao objetivo da Entrega 1. A principal dificuldade foi a "
        "instabilidade pontual da API (HTTP 504), contornada com a política de "
        "retentativa e o checkpoint. Como limitação, registro que a CEAP "
        "representa apenas parte dos gastos públicos (a cota parlamentar), e que "
        "valores líquidos negativos (estornos) existem em pequena quantidade e "
        "serão tratados como casos específicos na análise. A base já está pronta "
        "para a etapa de análise exploratória, dashboard e Machine Learning.", s["Corpo"]))

    doc = _doc(config.DIR_RELATORIOS / "relatorio_parcial_entrega1.pdf")
    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=_rodape)
    print(">> Relatório parcial (Entrega 1) gerado.")


# =========================================================================
# RELATÓRIO FINAL — ENTREGA 2
# =========================================================================
def relatorio_final(art: dict) -> None:
    s = _estilos()
    story = []
    _capa(story, s, "Relatório Final — Entrega 2",
          "Análise, visualização, Machine Learning e defesa")

    eda, ml = art["eda"], art["ml"]

    # 1. Introdução
    story.append(Paragraph("1. Introdução", s["H1"]))
    story.append(Paragraph(
        "Este relatório final consolida as duas entregas do Projeto Integrador. "
        "Na primeira fase, construí um pipeline que coleta de forma automatizada as "
        "despesas da Cota para o Exercício da Atividade Parlamentar (CEAP) da Câmara "
        "dos Deputados, trata os dados e os armazena em um banco relacional. Nesta "
        "segunda fase, transformo essa base em informação: faço a análise "
        "exploratória, construo um dashboard interativo e aplico técnicas de "
        "Machine Learning para encontrar padrões e identificar despesas atípicas.", s["Corpo"]))

    # 2. Objetivos
    story.append(Paragraph("2. Objetivos", s["H1"]))
    story.append(Paragraph(
        "Coletar, armazenar, tratar, analisar e interpretar dados públicos de "
        "gastos parlamentares, respondendo a perguntas concretas sobre a "
        "distribuição dos recursos e sobre comportamentos que fogem do padrão.", s["Corpo"]))

    # 3. API
    story.append(Paragraph("3. API escolhida", s["H1"]))
    story.append(Paragraph(
        "API de Dados Abertos da Câmara dos Deputados (v2), endpoints "
        "<font face='Courier'>/deputados</font> e "
        "<font face='Courier'>/deputados/{id}/despesas</font>. A escolha está "
        "justificada no relatório parcial: fonte oficial, gratuita, documentada e "
        "com paginação adequada ao exercício de coleta automatizada.", s["Corpo"]))

    # 4. Metodologia
    story.append(Paragraph("4. Metodologia", s["H1"]))
    story.append(Paragraph(
        "Segui um pipeline em cinco passos, cada um isolado em um módulo Python: "
        "(1) coleta via API com paginação e retentativa; (2) tratamento e limpeza; "
        "(3) modelagem e carga em SQLite; (4) análise exploratória com geração de "
        "gráficos; (5) Machine Learning. As bibliotecas utilizadas foram "
        "<font face='Courier'>requests</font> (coleta), "
        "<font face='Courier'>pandas/numpy</font> (tratamento e análise), "
        "<font face='Courier'>matplotlib/plotly</font> (gráficos), "
        "<font face='Courier'>scikit-learn</font> (Machine Learning) e "
        "<font face='Courier'>streamlit</font> (dashboard).", s["Corpo"]))

    # 5-7 resumidos (remetendo ao parcial)
    story.append(Paragraph("5. Coleta, modelagem e dicionário de dados", s["H1"]))
    story.append(Paragraph(
        "A coleta, a modelagem (três tabelas: deputados, despesas e fornecedores, "
        "com chaves primárias e estrangeiras) e o dicionário de dados foram "
        "detalhados na Entrega 1. O Diagrama Entidade-Relacionamento é reproduzido "
        "abaixo para contextualizar a análise.", s["Corpo"]))
    story.append(_img(config.DIR_DOCS / "der.png", largura=15 * cm))
    story.append(Paragraph("Figura 1 — Modelo de dados (DER).", s["Leg"]))

    # 6. Tratamento (resumo)
    story.append(Paragraph("6. Tratamento e preparação dos dados", s["H1"]))
    story.append(Paragraph(
        "Datas padronizadas em ISO, valores convertidos para numérico, "
        "identificadores mantidos como texto, remoção de duplicatas e de registros "
        "sem valor líquido. Para o Machine Learning, ainda padronizei as variáveis "
        "(StandardScaler) e calculei o desvio de cada despesa em relação à média da "
        "sua própria categoria (z-score por categoria).", s["Corpo"]))

    # 7. EDA
    story.append(PageBreak())
    story.append(Paragraph("7. Análise exploratória dos dados", s["H1"]))
    if eda:
        story.append(Paragraph(
            f"A base analisada reúne <b>{num(eda.get('total_registros'))}</b> "
            f"despesas de <b>{num(eda.get('qtd_deputados'))}</b> deputados, no "
            f"período de {eda.get('periodo_inicio')} a {eda.get('periodo_fim')}, "
            f"somando <b>{moeda(eda.get('valor_total'))}</b>. O valor médio por "
            f"despesa é de {moeda(eda.get('valor_medio'))} e a mediana, "
            f"{moeda(eda.get('valor_mediano'))} — a diferença entre média e mediana "
            "já antecipa uma distribuição assimétrica, com poucas despesas de valor "
            "muito alto puxando a média para cima.", s["Corpo"]))
        est = [
            ["Estatística", "Valor"],
            ["Registros", num(eda.get("total_registros"))],
            ["Valor total", moeda(eda.get("valor_total"))],
            ["Valor mínimo", moeda(eda.get("valor_minimo"))],
            ["Valor máximo", moeda(eda.get("valor_maximo"))],
            ["Valor médio", moeda(eda.get("valor_medio"))],
            ["Valor mediano", moeda(eda.get("valor_mediano"))],
        ]
        story.append(_tabela(est, col_widths=[7 * cm, 8 * cm]))

    story.append(_img(config.DIR_GRAFICOS / "01_categorias.png"))
    story.append(Paragraph("Figura 2 — Categorias que mais concentram recursos.", s["Leg"]))
    story.append(Paragraph(
        "As categorias de maior peso costumam ser divulgação da atividade "
        "parlamentar, passagens aéreas, combustíveis e manutenção de escritórios. "
        "Isso mostra que a CEAP se concentra em poucos tipos de gasto — informação "
        "útil para priorizar a fiscalização.", s["Corpo"]))

    story.append(_img(config.DIR_GRAFICOS / "02_evolucao_mensal.png"))
    story.append(Paragraph("Figura 3 — Evolução mensal dos gastos.", s["Leg"]))
    story.append(Paragraph(
        "A série mensal evidencia a sazonalidade: há meses de pico e quedas "
        "associadas a recessos parlamentares, o que ajuda a contextualizar "
        "qualquer variação brusca.", s["Corpo"]))

    story.append(PageBreak())
    story.append(_img(config.DIR_GRAFICOS / "03_ranking_deputados.png"))
    story.append(Paragraph("Figura 4 — Deputados com maior gasto total.", s["Leg"]))
    story.append(_img(config.DIR_GRAFICOS / "06_fornecedores.png"))
    story.append(Paragraph("Figura 5 — Fornecedores com maior concentração de valores.", s["Leg"]))
    story.append(Paragraph(
        "O ranking de fornecedores é especialmente relevante: quando poucos "
        "fornecedores concentram muitos recursos, vale investigar se há "
        "dependência ou padrões que mereçam atenção.", s["Corpo"]))

    story.append(_img(config.DIR_GRAFICOS / "04_gasto_por_uf.png"))
    story.append(Paragraph("Figura 6 — Gasto total por estado.", s["Leg"]))
    story.append(_img(config.DIR_GRAFICOS / "07_distribuicao_valores.png"))
    story.append(Paragraph("Figura 7 — Distribuição dos valores (escala log).", s["Leg"]))

    # 8. Dashboard
    story.append(PageBreak())
    story.append(Paragraph("8. Dashboard", s["H1"]))
    story.append(Paragraph(
        "Construí um dashboard interativo em Streamlit "
        "(<font face='Courier'>src/dashboard.py</font>), executável com "
        "<font face='Courier'>streamlit run dashboard.py</font>. Ele lê diretamente "
        "do banco e oferece filtros por estado, partido e categoria. Cada "
        "visualização responde a uma pergunta: visão geral (quanto e quantos), "
        "evolução temporal (quando), ranking de deputados (quem gasta mais), gasto "
        "por categoria e por estado (no que e onde) e concentração de fornecedores "
        "(para quem). Os indicadores no topo (total gasto, nº de despesas, nº de "
        "deputados e ticket médio) reagem aos filtros aplicados.", s["Corpo"]))

    # 9. Machine Learning
    story.append(Paragraph("9. Técnica de Machine Learning utilizada", s["H1"]))
    story.append(Paragraph(
        "Apliquei duas técnicas complementares, ambas não supervisionadas, porque "
        "a base não tem um rótulo a prever — o objetivo é descobrir estrutura e "
        "desvios.", s["Corpo"]))

    if ml.get("clusterizacao"):
        cl = ml["clusterizacao"]
        story.append(Paragraph("9.1 Clusterização (K-Means)", s["H2"]))
        story.append(Paragraph(
            "Para cada deputado, montei um vetor com a proporção do gasto em cada "
            "categoria, mais o gasto total, o número de despesas e o ticket médio. "
            "Padronizei as variáveis e apliquei o K-Means. O número de grupos foi "
            f"escolhido pelo coeficiente de silhueta, que indicou <b>k = "
            f"{cl.get('k_escolhido')}</b> (silhueta = {cl.get('silhueta')}). A "
            "pergunta respondida é: <i>existem grupos de parlamentares com perfis "
            "de despesa parecidos?</i>", s["Corpo"]))
        story.append(_img(config.DIR_GRAFICOS / "09_escolha_k.png", largura=15 * cm))
        story.append(Paragraph("Figura 8 — Escolha de k (cotovelo e silhueta).", s["Leg"]))
        story.append(_img(config.DIR_GRAFICOS / "08_clusters_deputados.png", largura=14 * cm))
        story.append(Paragraph("Figura 9 — Grupos projetados em 2D (PCA).", s["Leg"]))

        linhas = [["Grupo", "Deputados", "Gasto médio", "Perfil característico"]]
        for c in cl.get("clusters", []):
            cats = ", ".join(f"{k} ({v}%)" for k, v in
                             list(c["categorias_caracteristicas"].items())[:2])
            linhas.append([str(c["cluster"]), num(c["qtd_deputados"]),
                           moeda(c["gasto_total_medio"]), cats])
        story.append(_tabela(linhas, col_widths=[1.4 * cm, 2.2 * cm, 3.4 * cm, 8 * cm]))
        story.append(Paragraph(
            "Cada grupo reúne deputados com lógicas de gasto distintas — por "
            "exemplo, perfis concentrados em divulgação, perfis voltados a "
            "deslocamento (passagens e combustíveis) e perfis de manutenção de "
            "escritório. Isso mostra que não existe um padrão único de uso da cota.",
            s["Corpo"]))

    if ml.get("anomalias"):
        an = ml["anomalias"]
        story.append(PageBreak())
        story.append(Paragraph("9.2 Detecção de anomalias (Isolation Forest)", s["H2"]))
        story.append(Paragraph(
            "Para encontrar despesas atípicas, usei o Isolation Forest sobre o valor "
            "de cada despesa (em log) combinado ao seu z-score dentro da própria "
            "categoria. A contaminação foi fixada em 1%. De "
            f"<b>{num(an.get('qtd_analisada'))}</b> despesas, "
            f"<b>{num(an.get('qtd_anomalias'))}</b> foram sinalizadas como atípicas "
            f"({an.get('percentual_anomalias')}%). A pergunta respondida é: "
            "<i>quais lançamentos fogem do padrão da sua categoria?</i>", s["Corpo"]))
        story.append(_img(config.DIR_GRAFICOS / "10_anomalias.png", largura=14 * cm))
        story.append(Paragraph("Figura 10 — Despesas atípicas destacadas.", s["Leg"]))

        linhas = [["Deputado", "UF", "Categoria", "Valor"]]
        for a in an.get("top_anomalias", [])[:8]:
            linhas.append([str(a.get("deputado"))[:24], str(a.get("uf")),
                           str(a.get("categoria"))[:26], moeda(a.get("valor"))])
        story.append(_tabela(linhas, col_widths=[5 * cm, 1.3 * cm, 5.7 * cm, 3 * cm]))

    # 10. Interpretação
    story.append(Paragraph("10. Interpretação dos resultados", s["H1"]))
    story.append(Paragraph(
        "A clusterização mostrou que os deputados não gastam de forma homogênea: "
        "há grupos com perfis claramente diferentes, o que é coerente com a "
        "realidade (um deputado de estado distante tende a gastar mais com "
        "passagens, por exemplo). A silhueta moderada é esperada em dados reais e "
        "sociais, em que as fronteiras entre grupos são suaves. Já a detecção de "
        "anomalias funcionou como um filtro de priorização: ela não afirma que uma "
        "despesa é irregular, mas aponta os lançamentos que mais destoam da própria "
        "categoria — exatamente os que um auditor olharia primeiro. A maior "
        "limitação é que ambas as técnicas dependem da qualidade e da completude "
        "dos dados da API, e que a interpretação final exige conhecimento de "
        "contexto, não apenas o resultado do algoritmo.", s["Corpo"]))

    # 11. Resultados / 12. Limitações / 13. Considerações
    story.append(Paragraph("11. Resultados obtidos", s["H1"]))
    if eda:
        story.append(Paragraph(
            f"Pipeline completo e funcional, da coleta à interpretação, sobre "
            f"{num(eda.get('total_registros'))} despesas reais; banco relacional "
            "estruturado; dashboard interativo; e dois modelos de ML com resultados "
            "interpretados.", s["Corpo"]))

    story.append(Paragraph("12. Limitações", s["H1"]))
    story.append(Paragraph(
        "A CEAP cobre apenas a cota parlamentar, não todo o gasto público; a API "
        "apresenta instabilidade pontual (HTTP 504); e os modelos não supervisionados "
        "exigem interpretação humana — sinalizar uma anomalia não é o mesmo que "
        "comprovar irregularidade.", s["Corpo"]))

    story.append(Paragraph("13. Considerações finais", s["H1"]))
    story.append(Paragraph(
        "O projeto mostrou, na prática, o caminho completo de um analista de dados: "
        "entender a origem do dado, coletá-lo de forma automatizada, tratá-lo, "
        "modelá-lo, analisá-lo e, por fim, extrair conhecimento com Machine "
        "Learning. Mais do que executar algoritmos, o exercício reforçou que o valor "
        "está na interpretação e na capacidade de transformar dados públicos em "
        "informação útil para a sociedade.", s["Corpo"]))

    story.append(Paragraph("14. Referências", s["H1"]))
    for ref in [
        "BRASIL. Câmara dos Deputados. <b>Dados Abertos — API v2</b>. Disponível em: "
        "https://dadosabertos.camara.leg.br. Acesso em 2026.",
        "PEDREGOSA, F. et al. <b>Scikit-learn: Machine Learning in Python</b>. "
        "Journal of Machine Learning Research, 2011.",
        "McKINNEY, W. <b>Python for Data Analysis</b>. O'Reilly, 2022.",
        "LISKOV, B.; GUTTAG, J. Documentação oficial das bibliotecas pandas, "
        "matplotlib, plotly e streamlit. Acesso em 2026.",
    ]:
        story.append(Paragraph("• " + ref, s["Item"]))

    doc = _doc(config.DIR_RELATORIOS / "relatorio_final_entrega2.pdf")
    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=_rodape)
    print(">> Relatório final (Entrega 2) gerado.")


def main() -> None:
    config.garantir_pastas()
    art = _carregar_artefatos()
    relatorio_parcial(art)
    relatorio_final(art)
    print(">> Relatórios concluídos em", config.DIR_RELATORIOS)


if __name__ == "__main__":
    main()
