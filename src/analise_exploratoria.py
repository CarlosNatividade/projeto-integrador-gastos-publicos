"""
Análise Exploratória dos Dados (EDA) — etapa 10 da especificação.

Leio a base já tratada do SQLite e respondo às perguntas pedidas: quantos
registros, qual período, principais categorias, estatísticas dos valores,
campos ausentes, evolução no tempo, maiores gastadores e fornecedores mais
concentrados. Cada número vem acompanhado de um gráfico salvo em saidas/graficos.

A interpretação detalhada fica no relatório; aqui produzo os números e as figuras.
"""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")  # backend sem tela (rodando em servidor)
import matplotlib.pyplot as plt
import pandas as pd

import banco
import config

plt.rcParams["figure.dpi"] = 110
plt.rcParams["font.size"] = 9
COR = "#1e3a5f"


def carregar() -> pd.DataFrame:
    con = banco.conectar()
    try:
        df = pd.read_sql_query(
            """
            SELECT d.*, dep.nome AS nome_deputado, dep.sigla_partido,
                   dep.sigla_uf, f.nome AS nome_fornecedor
            FROM despesas d
            JOIN deputados dep ON dep.id_deputado = d.id_deputado
            LEFT JOIN fornecedores f ON f.cnpj_cpf = d.cnpj_cpf_fornecedor
            """,
            con,
        )
    finally:
        con.close()
    df["data_documento"] = pd.to_datetime(df["data_documento"], errors="coerce")
    return df


def _salvar(fig, nome: str) -> None:
    caminho = config.DIR_GRAFICOS / nome
    fig.tight_layout()
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    print(f"   gráfico salvo: {caminho.name}")


def estatisticas_gerais(df: pd.DataFrame) -> dict:
    v = df["valor_liquido"]
    resumo = {
        "total_registros": int(len(df)),
        "qtd_deputados": int(df["id_deputado"].nunique()),
        "qtd_fornecedores": int(df["cnpj_cpf_fornecedor"].nunique()),
        "qtd_categorias": int(df["tipo_despesa"].nunique()),
        "periodo_inicio": str(df["data_documento"].min().date()) if df["data_documento"].notna().any() else None,
        "periodo_fim": str(df["data_documento"].max().date()) if df["data_documento"].notna().any() else None,
        "valor_total": round(float(v.sum()), 2),
        "valor_minimo": round(float(v.min()), 2),
        "valor_maximo": round(float(v.max()), 2),
        "valor_medio": round(float(v.mean()), 2),
        "valor_mediano": round(float(v.median()), 2),
        "campos_ausentes": {
            col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().any()
        },
    }
    return resumo


def grafico_categorias(df: pd.DataFrame) -> pd.DataFrame:
    top = (
        df.groupby("tipo_despesa")["valor_liquido"].sum()
        .sort_values(ascending=False).head(10)
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    top.iloc[::-1].plot.barh(ax=ax, color=COR)
    ax.set_title("Top 10 categorias de despesa por valor total (R$)")
    ax.set_xlabel("Valor líquido total (R$)")
    ax.set_ylabel("")
    _salvar(fig, "01_categorias.png")
    return top.reset_index()


def grafico_evolucao(df: pd.DataFrame) -> pd.DataFrame:
    serie = df.groupby("mes")["valor_liquido"].sum()
    fig, ax = plt.subplots(figsize=(8, 4))
    serie.plot(ax=ax, marker="o", color=COR)
    ax.set_title(f"Evolução mensal dos gastos — {config.ROTULO_PERIODOS}")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Valor líquido (R$)")
    ax.set_xticks(range(1, 13))
    ax.grid(alpha=0.3)
    _salvar(fig, "02_evolucao_mensal.png")
    return serie.reset_index()


def grafico_ranking_deputados(df: pd.DataFrame) -> pd.DataFrame:
    top = (
        df.groupby(["nome_deputado", "sigla_partido", "sigla_uf"])["valor_liquido"]
        .sum().sort_values(ascending=False).head(15)
    )
    fig, ax = plt.subplots(figsize=(8, 5.5))
    top.iloc[::-1].plot.barh(ax=ax, color=COR)
    ax.set_title("Top 15 deputados por gasto total (CEAP)")
    ax.set_xlabel("Valor líquido total (R$)")
    ax.set_ylabel("")
    _salvar(fig, "03_ranking_deputados.png")
    return top.reset_index()


def grafico_uf(df: pd.DataFrame) -> pd.DataFrame:
    por_uf = df.groupby("sigla_uf")["valor_liquido"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 4))
    por_uf.plot.bar(ax=ax, color=COR)
    ax.set_title("Gasto total por estado (UF)")
    ax.set_xlabel("UF")
    ax.set_ylabel("Valor líquido (R$)")
    _salvar(fig, "04_gasto_por_uf.png")
    return por_uf.reset_index()


def grafico_partido(df: pd.DataFrame) -> pd.DataFrame:
    por_part = (
        df.groupby("sigla_partido")["valor_liquido"].sum()
        .sort_values(ascending=False).head(15)
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    por_part.plot.bar(ax=ax, color=COR)
    ax.set_title("Gasto total por partido (top 15)")
    ax.set_xlabel("Partido")
    ax.set_ylabel("Valor líquido (R$)")
    _salvar(fig, "05_gasto_por_partido.png")
    return por_part.reset_index()


def grafico_fornecedores(df: pd.DataFrame) -> pd.DataFrame:
    top = (
        df.dropna(subset=["cnpj_cpf_fornecedor"])
        .groupby(["nome_fornecedor"])["valor_liquido"]
        .sum().sort_values(ascending=False).head(15)
    )
    fig, ax = plt.subplots(figsize=(8, 5.5))
    top.iloc[::-1].plot.barh(ax=ax, color="#c9a227")
    ax.set_title("Top 15 fornecedores por valor recebido")
    ax.set_xlabel("Valor líquido total (R$)")
    ax.set_ylabel("")
    _salvar(fig, "06_fornecedores.png")
    return top.reset_index()


def grafico_distribuicao(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    # Histograma em escala log para enxergar a cauda longa típica de gastos
    valores = df["valor_liquido"].clip(lower=0.01)
    ax.hist(valores, bins=60, color=COR, alpha=0.85, log=True)
    ax.set_title("Distribuição dos valores das despesas (escala log)")
    ax.set_xlabel("Valor líquido (R$)")
    ax.set_ylabel("Frequência (log)")
    _salvar(fig, "07_distribuicao_valores.png")


def main() -> dict:
    config.garantir_pastas()
    df = carregar()
    print(f">> EDA sobre {len(df)} despesas.")

    resumo = estatisticas_gerais(df)
    cat = grafico_categorias(df)
    evo = grafico_evolucao(df)
    dep = grafico_ranking_deputados(df)
    uf = grafico_uf(df)
    part = grafico_partido(df)
    forn = grafico_fornecedores(df)
    grafico_distribuicao(df)

    # Salvo tabelas-resumo em CSV para o relatório
    cat.to_csv(config.DIR_SAIDAS / "resumo_categorias.csv", index=False)
    dep.to_csv(config.DIR_SAIDAS / "resumo_top_deputados.csv", index=False)
    forn.to_csv(config.DIR_SAIDAS / "resumo_top_fornecedores.csv", index=False)
    uf.to_csv(config.DIR_SAIDAS / "resumo_uf.csv", index=False)
    part.to_csv(config.DIR_SAIDAS / "resumo_partido.csv", index=False)

    with open(config.DIR_SAIDAS / "estatisticas_gerais.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print(">> EDA concluída. Estatísticas gerais:")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return resumo


if __name__ == "__main__":
    main()
