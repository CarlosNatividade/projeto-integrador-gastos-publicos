"""
Gera o Diagrama Entidade-Relacionamento (DER) como imagem.

Desenho as três entidades (deputados, despesas, fornecedores) com seus campos,
marcando chaves primárias (PK) e estrangeiras (FK), e as cardinalidades
(1:N) entre elas. Uso só matplotlib para não depender do Graphviz.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import config

AZUL = "#1e3a5f"
AZUL_CLARO = "#dce6f2"
OURO = "#c9a227"


def _tabela(ax, x, y, titulo, campos, largura=3.4):
    altura_linha = 0.32
    altura = altura_linha * (len(campos) + 1)
    # Cabeçalho
    ax.add_patch(FancyBboxPatch(
        (x, y - altura_linha), largura, altura_linha,
        boxstyle="round,pad=0.0,rounding_size=0.02",
        linewidth=1.2, edgecolor=AZUL, facecolor=AZUL))
    ax.text(x + largura / 2, y - altura_linha / 2, titulo,
            ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    # Corpo
    ax.add_patch(FancyBboxPatch(
        (x, y - altura), largura, altura - altura_linha,
        boxstyle="square,pad=0.0",
        linewidth=1.2, edgecolor=AZUL, facecolor="white"))
    for i, (campo, marca) in enumerate(campos):
        yy = y - altura_linha * (i + 1) - altura_linha / 2
        cor = OURO if marca in ("PK", "FK") else "#222222"
        peso = "bold" if marca == "PK" else "normal"
        texto = f"{campo}"
        if marca:
            texto += f"  [{marca}]"
        ax.text(x + 0.12, yy, texto, ha="left", va="center",
                fontsize=8, color=cor, fontweight=peso)
    return (x, y, largura, altura)


def main() -> None:
    config.garantir_pastas()
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    dep = _tabela(ax, 0.5, 7.5, "deputados", [
        ("id_deputado", "PK"), ("nome", ""), ("sigla_partido", ""),
        ("sigla_uf", ""), ("id_legislatura", ""), ("email", ""), ("url_foto", ""),
    ])

    desp = _tabela(ax, 5.2, 7.8, "despesas", [
        ("id_despesa", "PK"), ("id_deputado", "FK"), ("cnpj_cpf_fornecedor", "FK"),
        ("ano", ""), ("mes", ""), ("tipo_despesa", ""), ("tipo_documento", ""),
        ("cod_documento", ""), ("num_documento", ""), ("data_documento", ""),
        ("valor_documento", ""), ("valor_glosa", ""), ("valor_liquido", ""),
        ("url_documento", ""),
    ])

    forn = _tabela(ax, 10.1, 7.0, "fornecedores", [
        ("cnpj_cpf", "PK"), ("nome", ""),
    ])

    # Relações 1:N
    ax.annotate("", xy=(5.2, 6.0), xytext=(3.9, 6.0),
                arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=1.6))
    ax.text(4.05, 6.18, "1", color=AZUL, fontsize=10, fontweight="bold")
    ax.text(4.95, 6.18, "N", color=AZUL, fontsize=10, fontweight="bold")

    ax.annotate("", xy=(10.1, 6.0), xytext=(8.6, 6.0),
                arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=1.6))
    ax.text(8.7, 6.18, "N", color=AZUL, fontsize=10, fontweight="bold")
    ax.text(9.9, 6.18, "1", color=AZUL, fontsize=10, fontweight="bold")

    ax.set_title("Diagrama Entidade-Relacionamento — Pipeline de Gastos Públicos",
                 fontsize=12, fontweight="bold", color=AZUL, pad=14)
    ax.text(7, 0.4,
            "PK = chave primária · FK = chave estrangeira · "
            "deputados (1) ──< despesas >── (1) fornecedores",
            ha="center", fontsize=9, color="#555555")

    fig.tight_layout()
    caminho = config.DIR_DOCS / "der.png"
    fig.savefig(caminho, bbox_inches="tight", dpi=130)
    plt.close(fig)
    print(f">> DER salvo em {caminho}")


if __name__ == "__main__":
    main()
