"""
Machine Learning aplicado aos gastos parlamentares — etapas 12 e 13.

Apliquei DUAS técnicas, porque elas respondem a perguntas diferentes e se
complementam bem nesta base:

1) CLUSTERIZAÇÃO (K-Means) sobre o PERFIL DE GASTO de cada deputado.
   Pergunta: "existem grupos de parlamentares com padrões de despesa parecidos?"
   Construo, para cada deputado, um vetor com o quanto ele gastou em cada
   categoria (em proporção do seu total) + gasto total e nº de despesas.
   Padronizo (StandardScaler), escolho k pelo método do cotovelo + silhueta e
   interpreto cada grupo.

2) DETECÇÃO DE ANOMALIAS (Isolation Forest) sobre as DESPESAS individuais.
   Pergunta: "quais lançamentos fogem do padrão da sua categoria?"
   Uso o valor da despesa comparado à categoria (z-score dentro do tipo) mais o
   valor absoluto, e deixo o Isolation Forest sinalizar os pontos atípicos.

A interpretação dos resultados é gravada em saidas/ junto com os gráficos.
"""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

import banco
import config

plt.rcParams["figure.dpi"] = 110
plt.rcParams["font.size"] = 9


def carregar() -> pd.DataFrame:
    con = banco.conectar()
    try:
        df = pd.read_sql_query(
            """
            SELECT d.id_deputado, dep.nome AS nome_deputado, dep.sigla_partido,
                   dep.sigla_uf, d.tipo_despesa, d.valor_liquido
            FROM despesas d
            JOIN deputados dep ON dep.id_deputado = d.id_deputado
            WHERE d.valor_liquido > 0
            """,
            con,
        )
    finally:
        con.close()
    return df


# ---------------------------------------------------------------------------
# 1) Clusterização de deputados por perfil de gasto
# ---------------------------------------------------------------------------
def montar_matriz_perfil(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Matriz deputado x categoria (soma gasta em cada categoria)
    pivot = df.pivot_table(
        index="id_deputado", columns="tipo_despesa",
        values="valor_liquido", aggfunc="sum", fill_value=0.0,
    )
    total = pivot.sum(axis=1)
    # Proporção por categoria (perfil de gasto, independe do volume absoluto)
    proporcao = pivot.div(total.replace(0, np.nan), axis=0).fillna(0.0)
    proporcao.columns = [f"prop_{c}" for c in proporcao.columns]

    n_despesas = df.groupby("id_deputado").size().rename("n_despesas")
    perfil = proporcao.copy()
    perfil["valor_total"] = total
    perfil["n_despesas"] = n_despesas
    perfil["ticket_medio"] = total / n_despesas

    meta = (
        df.groupby("id_deputado")
        .agg(nome=("nome_deputado", "first"),
             partido=("sigla_partido", "first"),
             uf=("sigla_uf", "first"))
    )
    return perfil, meta


def escolher_k(X: np.ndarray, k_min: int | None = None, k_max: int | None = None) -> tuple[int, dict]:
    k_min = k_min if k_min is not None else config.K_MEANS_MIN
    k_max = k_max if k_max is not None else config.K_MEANS_MAX
    inercias, silhuetas = {}, {}
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        rotulos = km.fit_predict(X)
        inercias[k] = float(km.inertia_)
        silhuetas[k] = float(silhouette_score(X, rotulos))
    melhor_k = max(silhuetas, key=silhuetas.get)
    return melhor_k, {"inercia": inercias, "silhueta": silhuetas}


def clusterizar() -> dict:
    print(">> [ML] Clusterização de deputados por perfil de gasto (K-Means)...")
    df = carregar()
    perfil, meta = montar_matriz_perfil(df)

    X = StandardScaler().fit_transform(perfil.values)
    melhor_k, metricas = escolher_k(X)
    print(f"   k escolhido pela silhueta: {melhor_k}")

    km = KMeans(n_clusters=melhor_k, random_state=42, n_init=10)
    perfil["cluster"] = km.fit_predict(X)

    # Perfil 0 = grupo com maior gasto total agregado (vira Perfil 1 no dashboard).
    totais_grupo = perfil.groupby("cluster")["valor_total"].sum().sort_values(ascending=False)
    mapa_perfil = {antigo: novo for novo, antigo in enumerate(totais_grupo.index)}
    perfil["cluster"] = perfil["cluster"].map(mapa_perfil)

    perfil = perfil.join(meta)

    # Projeção 2D (PCA) só para visualizar os grupos
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)
    cores = ["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea",
             "#0891b2", "#ea580c", "#be185d", "#4f46e5", "#0d9488"]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sc = ax.scatter(
        coords[:, 0], coords[:, 1], c=perfil["cluster"],
        cmap=matplotlib.colors.ListedColormap(cores[:melhor_k]),
        alpha=0.85, s=32, edgecolors="white", linewidths=0.4,
    )
    ax.set_title(f"Grupos de deputados por perfil de gasto (K-Means, k={melhor_k})")
    ax.set_xlabel("Componente principal 1")
    ax.set_ylabel("Componente principal 2")
    legenda = ax.legend(*sc.legend_elements(), title="Cluster", loc="best")
    ax.add_artist(legenda)
    fig.tight_layout()
    fig.savefig(config.DIR_GRAFICOS / "08_clusters_deputados.png", bbox_inches="tight")
    plt.close(fig)

    # Gráfico do método do cotovelo + silhueta
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    a1.plot(list(metricas["inercia"]), list(metricas["inercia"].values()), "o-", color="#1e3a5f")
    a1.set_title("Método do cotovelo"); a1.set_xlabel("k"); a1.set_ylabel("Inércia")
    a2.plot(list(metricas["silhueta"]), list(metricas["silhueta"].values()), "o-", color="#c9a227")
    a2.set_title("Coeficiente de silhueta"); a2.set_xlabel("k"); a2.set_ylabel("Silhueta")
    fig.tight_layout()
    fig.savefig(config.DIR_GRAFICOS / "09_escolha_k.png", bbox_inches="tight")
    plt.close(fig)

    # Caracterização dos clusters (para interpretar)
    resumo_clusters = []
    prop_cols = [c for c in perfil.columns if c.startswith("prop_")]
    for c in sorted(perfil["cluster"].unique()):
        grupo = perfil[perfil["cluster"] == c]
        # 3 categorias que mais distinguem o grupo (maior proporção média)
        top_cats = (
            grupo[prop_cols].mean().sort_values(ascending=False).head(3)
        )
        resumo_clusters.append({
            "cluster": int(c),
            "qtd_deputados": int(len(grupo)),
            "gasto_total_medio": round(float(grupo["valor_total"].mean()), 2),
            "ticket_medio": round(float(grupo["ticket_medio"].mean()), 2),
            "n_despesas_medio": round(float(grupo["n_despesas"].mean()), 1),
            "categorias_caracteristicas": {
                k.replace("prop_", ""): round(float(v) * 100, 1) for k, v in top_cats.items()
            },
            "exemplos_deputados": grupo.sort_values("valor_total", ascending=False)
                                       ["nome"].head(4).tolist(),
        })

    perfil.reset_index()[["id_deputado", "nome", "partido", "uf",
                          "valor_total", "n_despesas", "ticket_medio", "cluster"]] \
        .to_csv(config.DIR_SAIDAS / "clusters_deputados.csv", index=False)

    resultado = {
        "tecnica": "K-Means",
        "k_escolhido": int(melhor_k),
        "silhueta": round(metricas["silhueta"][melhor_k], 3),
        "variancia_explicada_pca": [round(float(v), 3) for v in pca.explained_variance_ratio_],
        "clusters": resumo_clusters,
    }
    print(f"   {melhor_k} grupos identificados (silhueta={resultado['silhueta']}).")
    return resultado


# ---------------------------------------------------------------------------
# 2) Detecção de anomalias em despesas individuais
# ---------------------------------------------------------------------------
def detectar_anomalias() -> dict:
    print(">> [ML] Detecção de anomalias nas despesas (Isolation Forest)...")
    con = banco.conectar()
    try:
        df = pd.read_sql_query(
            """
            SELECT d.id_despesa, d.id_deputado, dep.nome AS nome_deputado,
                   dep.sigla_uf, dep.sigla_partido, d.tipo_despesa,
                   d.valor_liquido, f.nome AS nome_fornecedor, d.data_documento
            FROM despesas d
            JOIN deputados dep ON dep.id_deputado = d.id_deputado
            LEFT JOIN fornecedores f ON f.cnpj_cpf = d.cnpj_cpf_fornecedor
            WHERE d.valor_liquido > 0
            """,
            con,
        )
    finally:
        con.close()

    # z-score do valor DENTRO da categoria: o que importa é fugir do padrão
    # da própria categoria, não comparar passagem aérea com cafezinho.
    estat = df.groupby("tipo_despesa")["valor_liquido"].transform("mean")
    desvio = df.groupby("tipo_despesa")["valor_liquido"].transform("std").replace(0, np.nan)
    df["z_categoria"] = ((df["valor_liquido"] - estat) / desvio).fillna(0.0)
    df["log_valor"] = np.log1p(df["valor_liquido"])

    X = StandardScaler().fit_transform(df[["log_valor", "z_categoria"]].values)
    iso = IsolationForest(n_estimators=200, contamination=0.01, random_state=42)
    df["anomalia"] = iso.fit_predict(X)            # -1 = anomalia
    df["score_anomalia"] = iso.decision_function(X)  # quanto menor, mais anômalo

    anomalias = df[df["anomalia"] == -1].sort_values("score_anomalia")
    print(f"   {len(anomalias)} despesas sinalizadas como atípicas "
          f"({len(anomalias)/len(df)*100:.2f}% do total).")

    # Gráfico: valor x z-score, destacando anomalias
    fig, ax = plt.subplots(figsize=(8, 5))
    normal = df[df["anomalia"] == 1]
    ax.scatter(normal["valor_liquido"], normal["z_categoria"],
               s=8, alpha=0.3, color="#1e3a5f", label="Normal")
    ax.scatter(anomalias["valor_liquido"], anomalias["z_categoria"],
               s=22, alpha=0.9, color="#d64545", label="Anomalia")
    ax.set_xscale("log")
    ax.set_title("Detecção de anomalias em despesas (Isolation Forest)")
    ax.set_xlabel("Valor líquido (R$, escala log)")
    ax.set_ylabel("z-score dentro da categoria")
    ax.legend()
    fig.tight_layout()
    fig.savefig(config.DIR_GRAFICOS / "10_anomalias.png", bbox_inches="tight")
    plt.close(fig)

    cols = ["nome_deputado", "sigla_uf", "sigla_partido", "tipo_despesa",
            "valor_liquido", "nome_fornecedor", "data_documento", "score_anomalia"]
    anomalias[cols].head(40).to_csv(
        config.DIR_SAIDAS / "anomalias_top.csv", index=False)

    resultado = {
        "tecnica": "Isolation Forest",
        "contaminacao": 0.01,
        "qtd_analisada": int(len(df)),
        "qtd_anomalias": int(len(anomalias)),
        "percentual_anomalias": round(len(anomalias) / len(df) * 100, 2),
        "top_anomalias": [
            {
                "deputado": r.nome_deputado,
                "uf": r.sigla_uf,
                "categoria": r.tipo_despesa,
                "valor": round(float(r.valor_liquido), 2),
                "fornecedor": r.nome_fornecedor,
                "data": r.data_documento,
            }
            for r in anomalias.head(10).itertuples()
        ],
    }
    return resultado


def main() -> dict:
    config.garantir_pastas()
    resultado = {
        "clusterizacao": clusterizar(),
        "anomalias": detectar_anomalias(),
    }
    with open(config.DIR_SAIDAS / "resultado_ml.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(">> ML concluído.")
    return resultado


if __name__ == "__main__":
    main()
