"""
Dashboard interativo dos gastos públicos (Streamlit) — etapa 11.

Clique em um deputado no ranking para ver somente os dados dele.
"""

from __future__ import annotations

import html
import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

import config

st.set_page_config(page_title="Gastos Públicos | Câmara dos Deputados",
                   layout="wide", page_icon="📊")

alt.data_transformers.disable_max_rows()

COR_PADRAO = "#1e3a5f"
COR_SELECAO = "#c9a227"

CORES_CLUSTERS = [
    "#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea",
    "#0891b2", "#ea580c", "#be185d", "#4f46e5", "#0d9488",
]

NOMES_MESES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}
ORDEM_MESES = list(NOMES_MESES.values())

EIXO_BRL = alt.Axis(
    labelExpr=(
        "abs(datum.value) >= 1000000 ? "
        "'R$ ' + replace(format(datum.value, ',.0f'), ',', '.') : "
        "abs(datum.value) >= 1000 ? "
        "'R$ ' + replace(format(datum.value, ',.0f'), ',', '.') : "
        "'R$ ' + replace(format(datum.value, '.2f'), '.', ',')"
    )
)


@st.cache_data
def carregar_deputados() -> pd.DataFrame:
    con = sqlite3.connect(config.BANCO)
    df = pd.read_sql_query(
        "SELECT id_deputado, nome, sigla_partido, sigla_uf, url_foto FROM deputados",
        con,
    )
    con.close()
    df["url_foto"] = df["url_foto"].fillna("").replace(
        "", pd.NA
    )
    df["url_foto"] = df["url_foto"].fillna(
        df["id_deputado"].apply(
            lambda i: f"https://www.camara.leg.br/internet/deputado/bandep/{i}.jpg"
        )
    )
    return df


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    con = sqlite3.connect(config.BANCO)
    df = pd.read_sql_query(
        """
        SELECT d.*, dep.nome AS nome_deputado, dep.sigla_partido, dep.sigla_uf,
               f.nome AS nome_fornecedor
        FROM despesas d
        JOIN deputados dep ON dep.id_deputado = d.id_deputado
        LEFT JOIN fornecedores f ON f.cnpj_cpf = d.cnpj_cpf_fornecedor
        """,
        con,
    )
    con.close()
    df["data_documento"] = pd.to_datetime(df["data_documento"], errors="coerce")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    return df


@st.cache_data
def carregar_clusters() -> pd.DataFrame | None:
    caminho = config.DIR_SAIDAS / "clusters_deputados.csv"
    return pd.read_csv(caminho) if caminho.exists() else None


@st.cache_data
def carregar_anomalias() -> pd.DataFrame | None:
    caminho = config.DIR_SAIDAS / "anomalias_top.csv"
    return pd.read_csv(caminho) if caminho.exists() else None


def moeda(v: float) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def com_moeda(df: pd.DataFrame, coluna: str, nome_fmt: str = "valor_fmt") -> pd.DataFrame:
    out = df.copy()
    out[nome_fmt] = out[coluna].apply(moeda)
    return out


def serie_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega gastos por mês (1–12), preenchendo meses sem despesa com zero."""
    totais = df.groupby("mes")["valor_liquido"].sum()
    linhas = []
    for m in range(1, 13):
        linhas.append({
            "mes": m,
            "mes_nome": NOMES_MESES[m],
            "valor_liquido": float(totais.get(m, 0.0)),
        })
    return pd.DataFrame(linhas)


def rotulo_anos(anos: list[int] | None) -> str:
    if not anos:
        return ""
    anos = sorted(int(a) for a in anos)
    if len(anos) == 1:
        return str(anos[0])
    return f"{anos[0]}–{anos[-1]}"


def limpar_deputado() -> None:
    st.session_state.deputado_id = None


def selecionar_deputado(dep_id: int) -> None:
    st.session_state.deputado_id = dep_id


def nome_curto(nome: str, max_len: int = 16) -> str:
    if len(nome) <= max_len:
        return nome
    partes = nome.split()
    if len(partes) >= 2:
        curto = f"{partes[0]} {partes[-1]}"
        if len(curto) <= max_len:
            return curto
    return nome[: max_len - 1] + "…"


def css_galeria() -> str:
    return f"""
    <style>
    .dep-hero {{
        display: flex; align-items: center; gap: 20px;
        padding: 16px 20px; margin-bottom: 12px;
        background: rgba(128, 128, 128, 0.12);
        border-radius: 16px; border: 1px solid rgba(128, 128, 128, 0.25);
    }}
    .dep-hero img {{
        width: 96px; height: 96px; border-radius: 50%;
        object-fit: cover; border: 4px solid {COR_SELECAO};
        box-shadow: 0 4px 14px rgba(0,0,0,.15);
        flex-shrink: 0; background: #ffffff;
    }}
    .dep-hero h3 {{ margin: 0 0 4px; font-size: 1.2rem; }}
    .dep-hero p {{ margin: 0; font-size: .9rem; opacity: 0.85; }}
    /* Coluna da galeria: foto e nome empilhados e centralizados */
    div[data-testid="stHorizontalBlock"]:has(.dep-foto-marker) [data-testid="column"] {{
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(.dep-foto-marker) [data-testid="column"] > div {{
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    div.element-container:has(.dep-foto-marker) {{
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    div.element-container:has(.dep-partido) {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    .dep-partido {{
        text-align: center;
        font-size: 10px;
        font-weight: 700;
        line-height: 1.2;
        margin: 0 auto 4px;
        padding: 0;
        width: 74px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        pointer-events: none;
        letter-spacing: 0.03em;
        opacity: 0.92;
    }}
    .dep-partido.sel {{ color: {COR_SELECAO}; }}
    div.element-container:has(.dep-nome) {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    .dep-nome {{
        text-align: center;
        font-size: 11px;
        line-height: 1.3;
        margin: 6px auto 0;
        padding: 0;
        width: 74px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        word-break: break-word;
        pointer-events: none;
    }}
    .dep-nome.sel {{ color: {COR_SELECAO}; font-weight: 600; }}
    .dep-foto-marker {{ display: none; }}
    </style>
    """


def estilo_botao_foto(marker: str, url_foto: str, selecionado: bool) -> str:
    borda = COR_SELECAO if selecionado else "#6b7280"
    sombra = "0 0 0 2px rgba(201,162,39,.35)" if selecionado else "none"
    url_css = url_foto.replace("'", "%27")
    return f"""
    <div class="dep-foto-marker {marker}"></div>
    <style>
    div.element-container:has(.{marker}) + div.element-container {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 74px !important;
        margin: 0 auto !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}
    div.element-container:has(.{marker}) + div.element-container
        [data-testid="stButton"] {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    div.element-container:has(.{marker}) + div.element-container button {{
        background-image: url('{url_css}') !important;
        background-color: #ffffff !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        width: 74px !important;
        height: 74px !important;
        min-height: 74px !important;
        border-radius: 50% !important;
        border: 3px solid {borda} !important;
        box-shadow: {sombra} !important;
        padding: 0 !important;
        margin: 0 !important;
        font-size: 0 !important;
        color: transparent !important;
        line-height: 0 !important;
        cursor: pointer !important;
    }}
    div.element-container:has(.{marker}) + div.element-container button:hover {{
        transform: scale(1.05);
        transition: transform 0.12s ease;
    }}
    </style>
    """


def render_cartao_hero(dep: pd.Series, gasto: float, n_despesas: int) -> None:
    st.markdown(
        f"""
        <div class="dep-hero">
            <img src="{dep['url_foto']}" alt="{dep['nome_deputado']}">
            <div>
                <h3>{dep['nome_deputado']}</h3>
                <p>{dep['sigla_partido']}/{dep['sigla_uf']} ·
                   Gasto total: <strong>{moeda(gasto)}</strong> ·
                   {n_despesas:,} despesas</p>
            </div>
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )


def render_galeria_deputados(
    deps: pd.DataFrame,
    selecionado: int | None,
    n_despesas_sel: int = 0,
    top_n: int = 10,
) -> None:
    """Uma linha com os top deputados; demais via dropdown na barra lateral."""
    st.markdown(css_galeria(), unsafe_allow_html=True)
    st.markdown("### Detalhar deputado")
    st.caption(
        f"Os {top_n} parlamentares com maior gasto. "
        "**Clique na foto** para detalhar. Veja o ranking completo na **Análise geral**."
    )

    if selecionado is not None:
        dep_sel = deps[deps["id_deputado"] == selecionado]
        if not dep_sel.empty:
            row = dep_sel.iloc[0]
            c_hero, c_btn = st.columns([6, 1])
            with c_hero:
                render_cartao_hero(row, row["gasto"], n_despesas_sel)
            with c_btn:
                st.button("Ver todos", on_click=limpar_deputado, key="btn_limpar_galeria")

    top = deps.head(top_n)
    cols = st.columns(top_n, gap="small")
    for j, dep in enumerate(top.itertuples()):
        dep_id = int(dep.id_deputado)
        sel = selecionado == dep_id
        tooltip = html.escape(
            f"{dep.nome_deputado} ({dep.sigla_partido}/{dep.sigla_uf}) — "
            f"{moeda(dep.gasto)}"
        )
        marker = f"dep-m-{dep_id}-{j}"
        classe_nome = "dep-nome sel" if sel else "dep-nome"
        classe_partido = "dep-partido sel" if sel else "dep-partido"
        partido = html.escape(str(dep.sigla_partido or "—"))
        with cols[j]:
            st.markdown(
                f'<p class="{classe_partido}" title="{tooltip}">{partido}</p>',
                unsafe_allow_html=True,
            )
            st.markdown(estilo_botao_foto(marker, dep.url_foto, sel), unsafe_allow_html=True)
            st.button(
                "\u200b",
                key=f"dep_top_{dep_id}_{j}",
                on_click=selecionar_deputado,
                args=(dep_id,),
                type="tertiary",
            )
            st.markdown(
                f'<p class="{classe_nome}" title="{tooltip}">'
                f"{html.escape(dep.nome_deputado)}</p>",
                unsafe_allow_html=True,
            )


def id_do_clique(state, mapa_por_nome: dict[str, int] | None = None) -> int | None:
    if state is None:
        return None
    sel = getattr(state, "selection", None)
    if not sel:
        return None
    points = sel.get("points", []) if isinstance(sel, dict) else []
    for p in points:
        if "id_deputado" in p:
            return int(p["id_deputado"])
        if mapa_por_nome and "nome_deputado" in p:
            dep_id = mapa_por_nome.get(p["nome_deputado"])
            if dep_id is not None:
                return dep_id
    return None


def grafico_evolucao_mensal(df: pd.DataFrame, cor: str = COR_PADRAO) -> alt.Chart:
    """Gráfico de barras mensais com meses em ordem cronológica (Jan–Dez)."""
    dados = com_moeda(serie_mensal(df), "valor_liquido")
    return (
        alt.Chart(dados)
        .mark_bar(color=cor)
        .encode(
            x=alt.X(
                "mes_nome:N",
                title="Mês",
                sort=ORDEM_MESES,
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("valor_liquido:Q", title="Valor (R$)", axis=EIXO_BRL),
            tooltip=[
                alt.Tooltip("mes_nome:N", title="Mês"),
                alt.Tooltip("valor_fmt:N", title="Valor"),
            ],
        )
        .properties(height=340)
    )


def grafico_linha_mensal(df: pd.DataFrame, cor: str = COR_PADRAO) -> alt.Chart:
    """Linha de evolução mensal (visão geral)."""
    dados = com_moeda(serie_mensal(df), "valor_liquido")
    return (
        alt.Chart(dados)
        .mark_line(point=True, color=cor, strokeWidth=2)
        .encode(
            x=alt.X("mes_nome:N", title="Mês", sort=ORDEM_MESES),
            y=alt.Y("valor_liquido:Q", title="Valor (R$)", axis=EIXO_BRL),
            tooltip=[
                alt.Tooltip("mes_nome:N", title="Mês"),
                alt.Tooltip("valor_fmt:N", title="Valor"),
            ],
        )
        .properties(height=340)
    )


def grafico_barra_h(
    df: pd.DataFrame, x: str, y: str, altura: int = 340, rotulo_y: str = ""
) -> alt.Chart:
    dados = com_moeda(df, x)
    return (
        alt.Chart(dados)
        .mark_bar(color=COR_PADRAO)
        .encode(
            x=alt.X(f"{x}:Q", title="Valor (R$)", axis=EIXO_BRL),
            y=alt.Y(f"{y}:N", sort="-x", title=rotulo_y),
            tooltip=[
                alt.Tooltip(f"{y}:N", title=rotulo_y or "Item"),
                alt.Tooltip("valor_fmt:N", title="Valor"),
            ],
        )
        .properties(height=altura)
    )


def grafico_barra_v(
    df: pd.DataFrame, x: str, y: str, titulo_x: str = "", altura: int = 340
) -> alt.Chart:
    dados = com_moeda(df, y)
    return (
        alt.Chart(dados)
        .mark_bar(color=COR_PADRAO)
        .encode(
            x=alt.X(f"{x}:N", title=titulo_x or x, sort="-y"),
            y=alt.Y(f"{y}:Q", title="Valor (R$)", axis=EIXO_BRL),
            tooltip=[
                alt.Tooltip(f"{x}:N", title=titulo_x or x),
                alt.Tooltip("valor_fmt:N", title="Valor"),
            ],
        )
        .properties(height=altura)
    )


def reordenar_perfis_por_gasto(clusters: pd.DataFrame) -> pd.DataFrame:
    """Perfil 1 = grupo com maior gasto total; demais em ordem decrescente."""
    out = clusters.copy()
    ranking = (
        out.groupby("cluster")["valor_total"]
        .sum()
        .sort_values(ascending=False)
    )
    mapa = {antigo: novo for novo, antigo in enumerate(ranking.index)}
    out["cluster"] = out["cluster"].map(mapa)
    return out


def css_tabela_esquerda() -> str:
    return """
    <style>
    [data-testid="stDataFrame"] [data-testid="glideDataEditor"] td,
    [data-testid="stDataFrame"] [data-testid="glideDataEditor"] th {
        text-align: left !important;
        justify-content: flex-start !important;
    }
    [data-testid="stDataFrame"] [data-testid="glideDataEditor"] td:nth-child(5),
    [data-testid="stDataFrame"] [data-testid="glideDataEditor"] td:nth-child(6),
    [data-testid="stDataFrame"] [data-testid="glideDataEditor"] th:nth-child(5),
    [data-testid="stDataFrame"] [data-testid="glideDataEditor"] th:nth-child(6) {
        text-align: right !important;
        justify-content: flex-end !important;
    }
    </style>
    """


def limpar_perfil_ml() -> None:
    st.session_state.perfil_ml = "Todos"


def selecionar_perfil_ml(perfil: str) -> None:
    st.session_state.perfil_ml = perfil


def grafico_ranking_top10(
    rk: pd.DataFrame, id_selecionado: int | None, total_geral: float
) -> alt.Chart:
    """Ranking horizontal dos 10 maiores gastos, com cores por posição e seleção."""
    dados = rk.copy()
    dados = com_moeda(dados, "valor_liquido")
    dados["pct"] = (dados["valor_liquido"] / total_geral * 100) if total_geral > 0 else 0
    dados["pct_fmt"] = dados["pct"].apply(lambda v: f"{v:.1f}%")
    dados["destaque"] = dados["id_deputado"] == id_selecionado
    dados["pos_label"] = dados["posicao"].apply(lambda p: f"#{p}")

    cores_rank = [
        "#c9a227", "#d4a017", "#e8b923", "#1e5a8a", "#1e3a5f",
        "#2d4a6f", "#3d5a80", "#4d6a90", "#5d7aa0", "#6d8ab0",
    ]
    escala = alt.Scale(
        domain=[str(i) for i in range(1, 11)],
        range=cores_rank[: len(dados)],
    )
    selecao = alt.selection_point(fields=["id_deputado"], empty=True, name="dep_rank")

    return (
        alt.Chart(dados)
        .mark_bar(cornerRadiusEnd=4, height=22)
        .encode(
            y=alt.Y(
                "nome_deputado:N",
                sort=alt.EncodingSortField(field="valor_liquido", order="descending"),
                title="",
                axis=alt.Axis(labelLimit=200),
            ),
            x=alt.X("valor_liquido:Q", title="Gasto total (R$)", axis=EIXO_BRL),
            color=alt.condition(
                "destaque",
                alt.value(COR_SELECAO),
                alt.Color("posicao_str:N", title="Posição", scale=escala, legend=None),
            ),
            opacity=alt.condition(selecao, alt.value(1.0), alt.value(0.88)),
            tooltip=[
                alt.Tooltip("pos_label:N", title="Posição"),
                alt.Tooltip("nome_deputado:N", title="Deputado"),
                alt.Tooltip("sigla_partido:N", title="Partido"),
                alt.Tooltip("sigla_uf:N", title="UF"),
                alt.Tooltip("valor_fmt:N", title="Gasto total"),
                alt.Tooltip("pct_fmt:N", title="% do total filtrado"),
            ],
        )
        .add_params(selecao)
        .properties(height=420)
    )


def render_ranking_top10(
    lista_deps: pd.DataFrame,
    mapa_nome_id: dict[str, int],
    id_selecionado: int | None,
    rotulo_ano: str,
) -> None:
    """Seção explicativa do ranking dos 10 parlamentares com maior gasto."""
    total_geral = float(lista_deps["gasto"].sum())
    top10 = lista_deps.head(10).copy()
    top10["valor_liquido"] = top10["gasto"]
    top10["posicao"] = range(1, len(top10) + 1)
    top10["posicao_str"] = top10["posicao"].astype(str)
    concentracao = (
        float(top10["gasto"].sum()) / total_geral * 100 if total_geral > 0 else 0
    )

    st.markdown("#### Ranking — Top 10 maiores gastos")
    st.caption(
        f"Parlamentares com maior volume de despesas CEAP no período **{rotulo_ano}**. "
        "**Clique em uma barra** para abrir a análise individual do deputado."
    )

    if not top10.empty:
        lider = top10.iloc[0]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Maior gasto", moeda(lider["gasto"]))
        k2.metric(
            "Líder do ranking",
            lider["nome_deputado"],
            delta=f"{lider['sigla_partido']}/{lider['sigla_uf']}",
            delta_color="off",
        )
        k3.metric(
            "Concentração do Top 10",
            f"{concentracao:.1f}%",
            help="Percentual do total gasto (filtros ativos) concentrado nos 10 primeiros.",
        )
        k4.metric("Total dos Top 10", moeda(top10["gasto"].sum()))

    evento = st.altair_chart(
        grafico_ranking_top10(top10, id_selecionado, total_geral),
        use_container_width=True,
        on_select="rerun",
        key="graf_ranking_top10",
    )
    id_clicado = id_do_clique(evento, mapa_nome_id)
    if id_clicado is not None:
        selecionar_deputado(id_clicado)

    st.markdown(css_tabela_esquerda(), unsafe_allow_html=True)
    tabela = top10[
        ["posicao", "nome_deputado", "sigla_partido", "sigla_uf", "gasto"]
    ].copy()
    pct_vals = (top10["gasto"] / total_geral * 100).tolist()
    tabela["gasto_fmt"] = tabela["gasto"].apply(moeda)
    tabela["pct_fmt"] = [f"{v:.1f}%" for v in pct_vals]
    tabela = tabela[
        ["posicao", "nome_deputado", "sigla_partido", "sigla_uf", "gasto_fmt", "pct_fmt"]
    ]
    tabela.columns = ["#", "Deputado", "Partido", "UF", "Gasto total", "% do total"]
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        key="tab_ranking_top10",
        column_config={
            "#": st.column_config.NumberColumn("#", width="small", format="%d"),
            "Deputado": st.column_config.TextColumn("Deputado", width="large"),
            "Partido": st.column_config.TextColumn("Partido", width="small"),
            "UF": st.column_config.TextColumn("UF", width="small"),
            "Gasto total": st.column_config.TextColumn("Gasto total", width="medium"),
            "% do total": st.column_config.TextColumn("% do total", width="small"),
        },
    )


def grafico_clusters_kmeans(
    clusters: pd.DataFrame,
    deputado_sel: bool,
    nome_sel: str | None = None,
    perfil_filtro: str = "Todos",
) -> alt.Chart:
    dados = clusters.copy()
    dados["perfil"] = "Perfil " + (dados["cluster"].astype(int) + 1).astype(str)

    perfis_all = [f"Perfil {c + 1}" for c in sorted(clusters["cluster"].astype(int).unique())]
    escala_cor = alt.Scale(domain=perfis_all, range=CORES_CLUSTERS[: len(perfis_all)])

    if perfil_filtro and perfil_filtro != "Todos":
        dados = dados[dados["perfil"] == perfil_filtro]

    base = alt.Chart(dados).encode(
        x=alt.X("valor_total:Q", title="Gasto total (R$)", axis=EIXO_BRL),
        y=alt.Y("ticket_medio:Q", title="Ticket médio (R$)", axis=EIXO_BRL),
        tooltip=[
            alt.Tooltip("nome:N", title="Deputado"),
            alt.Tooltip("partido:N", title="Partido"),
            alt.Tooltip("uf:N", title="UF"),
            alt.Tooltip("perfil:N", title="Perfil de gasto"),
            alt.Tooltip("gasto_total_fmt:N", title="Gasto total"),
            alt.Tooltip("ticket_fmt:N", title="Ticket médio"),
        ],
    )

    if deputado_sel and nome_sel:
        dados["destaque"] = dados["nome"] == nome_sel
        return base.mark_circle(stroke="white", strokeWidth=0.6).encode(
            color=alt.Color("perfil:N", title="Perfil", scale=escala_cor),
            size=alt.condition("destaque", alt.value(280), alt.value(90)),
            strokeWidth=alt.condition("destaque", alt.value(3), alt.value(0.6)),
            stroke=alt.condition("destaque", alt.value(COR_SELECAO), alt.value("white")),
            opacity=alt.condition("destaque", alt.value(1.0), alt.value(0.8)),
        ).properties(height=420)

    chart = base.mark_circle(size=100, stroke="white", strokeWidth=0.9, opacity=0.9).encode(
        color=alt.Color("perfil:N", title="Perfil", scale=escala_cor),
    )

    if perfil_filtro == "Todos":
        selecao_perfil = alt.selection_point(fields=["perfil"], bind="legend", empty=True)
        chart = chart.add_params(selecao_perfil).transform_filter(selecao_perfil)

    return chart.properties(height=420)


def render_filtro_perfis_ml(clusters: pd.DataFrame) -> str:
    """Filtro clicável de perfis com botões coloridos."""
    if "perfil_ml" not in st.session_state:
        st.session_state.perfil_ml = "Todos"

    perfis = sorted(clusters["cluster"].astype(int).unique())
    opcoes = ["Todos"] + [f"Perfil {c + 1}" for c in perfis]

    st.markdown("**Filtrar por perfil**")
    st.caption("Clique em um perfil para exibir somente os deputados daquele grupo no gráfico.")

    cols = st.columns(len(opcoes))
    for i, op in enumerate(opcoes):
        sel = st.session_state.perfil_ml == op
        with cols[i]:
            st.button(
                op,
                key=f"btn_perfil_{op}",
                on_click=selecionar_perfil_ml,
                args=(op,),
                type="primary" if sel else "secondary",
                use_container_width=True,
            )

    if st.session_state.perfil_ml != "Todos":
        st.button("Limpar filtro de perfil", on_click=limpar_perfil_ml, key="btn_limpar_perfil")

    return st.session_state.perfil_ml


# ============================= ESTADO ======================================
if "deputado_id" not in st.session_state:
    st.session_state.deputado_id = None

df = carregar_dados()
meta_deps = carregar_deputados()

st.title("Pipeline de Inteligência em Gastos Públicos")
st.caption(
    f"Cota para o Exercício da Atividade Parlamentar (CEAP) — "
    f"Câmara dos Deputados · período {config.ROTULO_PERIODOS}"
)

# ============================= SIDEBAR =====================================
st.sidebar.header("Filtros")
anos_disp = sorted(df["ano"].dropna().astype(int).unique().tolist())
ufs = sorted(df["sigla_uf"].dropna().unique())
partidos = sorted(df["sigla_partido"].dropna().unique())
categorias = sorted(df["tipo_despesa"].dropna().unique())

if "filtro_ano" not in st.session_state:
    st.session_state.filtro_ano = anos_disp

f_uf = st.sidebar.multiselect("Estado (UF)", ufs)
f_part = st.sidebar.multiselect("Partido", partidos)
f_cat = st.sidebar.multiselect("Categoria de despesa", categorias)

dados_sem_ano = df.copy()
if f_uf:
    dados_sem_ano = dados_sem_ano[dados_sem_ano["sigla_uf"].isin(f_uf)]
if f_part:
    dados_sem_ano = dados_sem_ano[dados_sem_ano["sigla_partido"].isin(f_part)]
if f_cat:
    dados_sem_ano = dados_sem_ano[dados_sem_ano["tipo_despesa"].isin(f_cat)]

if f_cat:
    dados_sem_ano = dados_sem_ano[dados_sem_ano["tipo_despesa"].isin(f_cat)]

st.divider()

# ============================= FILTRO DE ANO ===============================
st.markdown("### Filtro por ano")
st.multiselect(
    "Selecione o(s) ano(s) para todos os cálculos da página",
    anos_disp,
    key="filtro_ano",
)
f_ano = st.session_state.filtro_ano
rotulo_ano_ativo = rotulo_anos(f_ano) or "—"
st.caption(
    f"Período ativo: **{rotulo_ano_ativo}**. "
    "Indicadores, ranking, gráficos e totais usam somente os anos selecionados."
)

dados_base = dados_sem_ano.copy()
if f_ano:
    dados_base = dados_base[dados_base["ano"].isin(f_ano)]
else:
    dados_base = dados_base.iloc[0:0]

lista_deps = (
    dados_base.groupby(["id_deputado", "nome_deputado", "sigla_partido", "sigla_uf"])
    .agg(gasto=("valor_liquido", "sum"))
    .reset_index()
    .sort_values("gasto", ascending=False)
)
lista_deps = lista_deps.merge(
    meta_deps[["id_deputado", "url_foto"]], on="id_deputado", how="left"
)
mapa_nome_id_por_nome = {
    r.nome_deputado: int(r.id_deputado) for r in lista_deps.itertuples()
}

dados = dados_base.copy()
deputado_sel = st.session_state.deputado_id is not None
if deputado_sel:
    dados = dados[dados["id_deputado"] == st.session_state.deputado_id]

st.divider()

# ============================= GALERIA DE DEPUTADOS ==========================
render_galeria_deputados(
    lista_deps,
    st.session_state.deputado_id,
    n_despesas_sel=len(dados) if deputado_sel else 0,
)

st.divider()

# ============================= MÉTRICAS ====================================
st.markdown("### Indicadores")
if deputado_sel and dados.empty:
    st.warning("Nenhuma despesa do deputado selecionado para o(s) ano(s) escolhido(s).")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total gasto", moeda(dados["valor_liquido"].sum() if not dados.empty else 0))
m2.metric("Despesas", f"{len(dados):,}".replace(",", "."))
total_deps = len(meta_deps)
deps_com_gasto = dados_base["id_deputado"].nunique() if not dados_base.empty else 0
if deputado_sel:
    m3.metric("Deputados", 1)
else:
    m3.metric(
        "Deputados com gasto",
        f"{deps_com_gasto} de {total_deps}",
        help=(
            f"{total_deps - deps_com_gasto} parlamentares sem despesas CEAP "
            f"no período {rotulo_ano_ativo} (ex.: ministros de Estado)."
        ),
    )
m4.metric(
    "Ticket médio",
    moeda(dados["valor_liquido"].mean()) if not dados.empty else moeda(0),
)

st.divider()

# ============================= GRÁFICOS ====================================

if dados.empty:
    st.info("Selecione outro ano ou deputado para visualizar os gráficos.")
elif not deputado_sel:
    # ---- Visão geral ----
    st.markdown("### Análise geral")

    render_ranking_top10(
        lista_deps,
        mapa_nome_id_por_nome,
        st.session_state.deputado_id,
        rotulo_ano_ativo,
    )

    st.divider()

    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"**Evolução mensal dos gastos ({rotulo_ano_ativo})**")
        st.altair_chart(
            grafico_linha_mensal(dados),
            use_container_width=True, key="graf_evolucao",
        )
    with g2:
        st.markdown(f"**Gasto por categoria — top 10 ({rotulo_ano_ativo})**")
        cat = (
            dados.groupby("tipo_despesa")["valor_liquido"].sum()
            .sort_values(ascending=False).head(10).reset_index()
        )
        st.altair_chart(
            grafico_barra_h(cat, "valor_liquido", "tipo_despesa", rotulo_y=""),
            use_container_width=True, key="graf_categorias",
        )

    g3, g4 = st.columns(2)
    with g3:
        st.markdown(f"**Gasto por estado (UF) ({rotulo_ano_ativo})**")
        uf = (
            dados.groupby("sigla_uf")["valor_liquido"].sum()
            .sort_values(ascending=False).reset_index()
        )
        st.altair_chart(
            grafico_barra_v(uf, "sigla_uf", "valor_liquido", titulo_x="UF"),
            use_container_width=True, key="graf_uf",
        )
    with g4:
        st.markdown(f"**Gasto por partido — top 10 ({rotulo_ano_ativo})**")
        part = (
            dados.groupby("sigla_partido")["valor_liquido"].sum()
            .sort_values(ascending=False).head(10).reset_index()
        )
        st.altair_chart(
            grafico_barra_v(part, "sigla_partido", "valor_liquido", titulo_x="Partido"),
            use_container_width=True, key="graf_partido",
        )

    st.markdown(f"**Fornecedores com maior concentração — top 15 ({rotulo_ano_ativo})**")
    forn = (
        dados.dropna(subset=["cnpj_cpf_fornecedor"])
        .groupby("nome_fornecedor")["valor_liquido"].sum()
        .sort_values(ascending=False).head(15).reset_index()
    )
    if forn.empty:
        st.info("Nenhum fornecedor identificado.")
    else:
        st.altair_chart(
            grafico_barra_h(forn, "valor_liquido", "nome_fornecedor", altura=400, rotulo_y=""),
            use_container_width=True, key="graf_fornecedores",
        )

else:
    # ---- Visão do deputado ----
    st.markdown("### Análise do deputado selecionado")

    g1, g2 = st.columns([3, 2])
    with g1:
        st.markdown(f"**Gasto por mês — Jan a Dez ({rotulo_ano_ativo})**")
        st.altair_chart(
            grafico_evolucao_mensal(dados, cor=COR_SELECAO),
            use_container_width=True, key="graf_mes_deputado",
        )
    with g2:
        st.markdown(f"**Distribuição por categoria ({rotulo_ano_ativo})**")
        cat = (
            dados.groupby("tipo_despesa")["valor_liquido"].sum()
            .sort_values(ascending=False).head(8).reset_index()
        )
        st.altair_chart(
            grafico_barra_h(cat, "valor_liquido", "tipo_despesa", altura=340, rotulo_y=""),
            use_container_width=True, key="graf_cat_deputado",
        )

    g3, g4 = st.columns(2)
    with g3:
        st.markdown(f"**Principais fornecedores ({rotulo_ano_ativo})**")
        forn = (
            dados.dropna(subset=["cnpj_cpf_fornecedor"])
            .groupby("nome_fornecedor")["valor_liquido"].sum()
            .sort_values(ascending=False).head(10).reset_index()
        )
        if forn.empty:
            st.info("Sem fornecedores identificados.")
        else:
            st.altair_chart(
                grafico_barra_h(forn, "valor_liquido", "nome_fornecedor", altura=360, rotulo_y=""),
                use_container_width=True, key="graf_forn_dep",
            )
    with g4:
        st.markdown(f"**Maiores despesas individuais ({rotulo_ano_ativo})**")
        top = (
            dados.nlargest(10, "valor_liquido")[
                ["data_documento", "tipo_despesa", "valor_liquido", "ano"]
            ].copy()
        )
        top["data_documento"] = top["data_documento"].dt.strftime("%d/%m/%Y")
        top["valor_liquido"] = top["valor_liquido"].apply(moeda)
        top.columns = ["Data", "Categoria", "Valor", "Ano"]
        st.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown(f"**Todas as despesas ({rotulo_ano_ativo})**")
    tabela = dados[
        ["data_documento", "ano", "tipo_despesa", "nome_fornecedor", "valor_liquido", "url_documento"]
    ].sort_values("valor_liquido", ascending=False).copy()
    tabela["data_documento"] = tabela["data_documento"].dt.strftime("%d/%m/%Y")
    tabela["valor_liquido"] = tabela["valor_liquido"].apply(moeda)
    tabela.columns = ["Data", "Ano", "Categoria", "Fornecedor", "Valor", "Comprovante"]
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Comprovante": st.column_config.LinkColumn("Comprovante", display_text="Abrir"),
        },
    )

# ============================= MACHINE LEARNING ==========================
st.divider()
st.markdown("### Machine Learning")

clusters = carregar_clusters()
if clusters is not None:
    n_perfis = clusters["cluster"].nunique()
    st.markdown(f"**Grupos de deputados por perfil de gasto (K-Means · {n_perfis} perfis)**")
    st.caption(
        "Cada cor representa um perfil distinto de despesa "
        "(proporção por categoria, volume e ticket médio). "
        "**Perfil 1** = grupo com maior gasto total agregado. "
        "Use o filtro abaixo ou clique na legenda do gráfico."
    )
    clusters = reordenar_perfis_por_gasto(clusters.copy())
    clusters["gasto_total_fmt"] = clusters["valor_total"].apply(moeda)
    clusters["ticket_fmt"] = clusters["ticket_medio"].apply(moeda)

    perfil_filtro = render_filtro_perfis_ml(clusters)
    nome_sel = dados["nome_deputado"].iloc[0] if deputado_sel and not dados.empty else None

    if perfil_filtro != "Todos":
        clusters["perfil"] = "Perfil " + (clusters["cluster"].astype(int) + 1).astype(str)
        n_dep = len(clusters[clusters["perfil"] == perfil_filtro])
        st.info(f"Exibindo **{perfil_filtro}** — {n_dep} deputado(s) neste grupo.")

    st.altair_chart(
        grafico_clusters_kmeans(clusters, deputado_sel, nome_sel, perfil_filtro),
        use_container_width=True,
        key="graf_clusters",
    )

    resumo = (
        clusters.groupby("cluster")
        .agg(
            deputados=("nome", "count"),
            gasto_total=("valor_total", "sum"),
            gasto_medio=("valor_total", "mean"),
            ticket_medio=("ticket_medio", "mean"),
        )
        .reset_index()
        .sort_values("cluster")
    )
    resumo["perfil"] = "Perfil " + (resumo["cluster"] + 1).astype(str)
    resumo["gasto_total"] = resumo["gasto_total"].apply(moeda)
    resumo["gasto_medio"] = resumo["gasto_medio"].apply(moeda)
    resumo["ticket_medio"] = resumo["ticket_medio"].apply(moeda)
    resumo = resumo[["perfil", "deputados", "gasto_total", "gasto_medio", "ticket_medio"]]
    resumo.columns = [
        "Perfil", "Deputados", "Gasto total do grupo", "Gasto médio", "Ticket médio",
    ]
    st.markdown(css_tabela_esquerda(), unsafe_allow_html=True)
    st.dataframe(
        resumo,
        use_container_width=True,
        hide_index=True,
        key="resumo_clusters",
        column_config={
            "Perfil": st.column_config.TextColumn("Perfil", width="small"),
            "Deputados": st.column_config.NumberColumn("Deputados", width="small"),
            "Gasto total do grupo": st.column_config.TextColumn(
                "Gasto total do grupo", width="medium"
            ),
            "Gasto médio": st.column_config.TextColumn("Gasto médio", width="medium"),
            "Ticket médio": st.column_config.TextColumn("Ticket médio", width="medium"),
        },
    )

anomalias = carregar_anomalias()
if anomalias is not None:
    st.markdown("**Despesas atípicas (Isolation Forest)**")
    exibir = anomalias.copy()
    if "data_documento" in exibir.columns:
        exibir["data_documento"] = pd.to_datetime(exibir["data_documento"], errors="coerce")
        if f_ano:
            exibir = exibir[exibir["data_documento"].dt.year.isin(f_ano)]
    if deputado_sel and "nome_deputado" in exibir.columns:
        exibir = exibir[exibir["nome_deputado"] == dados["nome_deputado"].iloc[0]]
    if "valor_liquido" in exibir.columns:
        exibir["valor_liquido"] = exibir["valor_liquido"].apply(moeda)
    if exibir.empty:
        st.info("Nenhuma anomalia para os filtros atuais.")
    else:
        st.dataframe(exibir, use_container_width=True, key="tabela_anomalias")

st.caption(
    "Fonte: API de Dados Abertos da Câmara dos Deputados. "
    "Projeto Integrador — Carlos Ranyere da Natividade Pereira."
)
