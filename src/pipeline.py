"""
Orquestrador do pipeline completo.

Roda as etapas na ordem certa. Útil para reproduzir o projeto do zero:

    cd src
    python3 pipeline.py            # roda tudo (coleta + tratamento + análise + ML + relatórios)
    python3 pipeline.py --sem-coleta   # pula a coleta (usa os dados brutos já baixados)

O dashboard é interativo e roda à parte (streamlit run dashboard.py).
"""

from __future__ import annotations

import sys
import time

import coleta
import tratamento
import analise_exploratoria
import machine_learning
import gerar_der
import gerar_relatorios


def main() -> None:
    pular_coleta = "--sem-coleta" in sys.argv
    inicio = time.time()

    if not pular_coleta:
        print("\n===== 1/6 · COLETA =====")
        coleta.main()
    else:
        print("\n===== 1/6 · COLETA (pulada) =====")

    print("\n===== 2/6 · TRATAMENTO E CARGA =====")
    tratamento.main()

    print("\n===== 3/6 · DIAGRAMA ENTIDADE-RELACIONAMENTO =====")
    gerar_der.main()

    print("\n===== 4/6 · ANÁLISE EXPLORATÓRIA =====")
    analise_exploratoria.main()

    print("\n===== 5/6 · MACHINE LEARNING =====")
    machine_learning.main()

    print("\n===== 6/6 · RELATÓRIOS (PDF) =====")
    gerar_relatorios.main()

    print(f"\n>> Pipeline concluído em {time.time() - inicio:.1f}s.")
    print(">> Para abrir o dashboard: streamlit run dashboard.py")


if __name__ == "__main__":
    main()
