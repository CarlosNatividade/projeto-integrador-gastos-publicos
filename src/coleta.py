"""
Coleta automatizada de dados da API de Dados Abertos da Câmara dos Deputados.

A ideia é simples de descrever, mas exige cuidado na execução: primeiro pego a
lista de deputados em exercício e, para cada um, percorro a paginação das suas
despesas (CEAP) no ano configurado. Tudo o que volta da API é salvo cru em JSON
na pasta dados/brutos antes de qualquer tratamento — assim, se eu precisar
reprocessar, não preciso bater na API de novo.

Pontos que tratei aqui:
  * paginação por "pagina"/"itens";
  * retentativa com backoff para os 504 que a API solta sob carga;
  * checkpoint: cada deputado coletado é gravado, então uma queda no meio do
    caminho não joga fora o que já foi baixado;
  * registro da quantidade coletada em um pequeno resumo.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime

import requests

import config


def _get(url: str, params: dict | None = None) -> dict | None:
    """Faz um GET resiliente. Devolve o JSON ou None após esgotar as tentativas."""
    for tentativa in range(1, config.MAX_TENTATIVAS + 1):
        try:
            resp = requests.get(
                url, params=params, headers=config.HEADERS, timeout=config.TIMEOUT_SEG
            )
            if resp.status_code == 200:
                return resp.json()
            # 429/5xx → vale a pena tentar de novo; 4xx "definitivo" não.
            if resp.status_code not in (429, 500, 502, 503, 504):
                print(f"  ! HTTP {resp.status_code} em {url} — não vou repetir.")
                return None
            print(f"  . HTTP {resp.status_code} (tentativa {tentativa}/{config.MAX_TENTATIVAS})")
        except requests.RequestException as e:
            print(f"  . Falha de rede: {type(e).__name__} (tentativa {tentativa})")
        time.sleep(config.ESPERA_BASE_SEG * (2 ** (tentativa - 1)))
    return None


def coletar_deputados() -> list[dict]:
    """Baixa a lista de deputados em exercício, tratando a paginação."""
    print(">> Coletando lista de deputados...")
    deputados: list[dict] = []
    pagina = 1
    while True:
        params = {
            "ordem": "ASC",
            "ordenarPor": "nome",
            "itens": config.ITENS_POR_PAGINA,
            "pagina": pagina,
        }
        if config.UFS_INCLUIDAS:
            params["siglaUf"] = ",".join(config.UFS_INCLUIDAS)

        dados = _get(f"{config.API_BASE}/deputados", params)
        if not dados or not dados.get("dados"):
            break

        deputados.extend(dados["dados"])

        # A API informa os links de navegação; se não há "next", acabou.
        tem_proxima = any(l.get("rel") == "next" for l in dados.get("links", []))
        if not tem_proxima:
            break
        pagina += 1

    if config.MAX_DEPUTADOS is not None:
        deputados = deputados[: config.MAX_DEPUTADOS]

    print(f"   {len(deputados)} deputados coletados.")
    with open(config.DIR_BRUTOS / "deputados.json", "w", encoding="utf-8") as f:
        json.dump(deputados, f, ensure_ascii=False, indent=2)
    return deputados


def coletar_despesas_deputado(id_dep: int, ano: int) -> list[dict]:
    """Percorre todas as páginas de despesas de um deputado no ano informado."""
    despesas: list[dict] = []
    pagina = 1
    while True:
        params = {
            "ano": ano,
            "itens": config.ITENS_POR_PAGINA,
            "pagina": pagina,
        }
        dados = None
        # A API às vezes devolve lista vazia com HTTP 200; retento antes de desistir.
        for _ in range(3):
            dados = _get(f"{config.API_BASE}/deputados/{id_dep}/despesas", params)
            if dados and dados.get("dados"):
                break
            time.sleep(config.ESPERA_BASE_SEG)
        if not dados or not dados.get("dados"):
            break
        despesas.extend(dados["dados"])
        tem_proxima = any(l.get("rel") == "next" for l in dados.get("links", []))
        if not tem_proxima:
            break
        pagina += 1
    return despesas


def coletar_todas_despesas(deputados: list[dict], ano: int) -> int:
    """Coleta despesas de cada deputado no ano, com checkpoint por arquivo."""
    print(f">> Coletando despesas de {ano} (CEAP)...")
    arquivo = config.DIR_BRUTOS / f"despesas_{ano}.jsonl"
    total = 0
    # Abro em modo append e gravo uma linha JSON por despesa (JSON Lines):
    # formato amigável para volume grande e para retomar coleta.
    ja_coletados = _ids_ja_coletados(arquivo)
    modo = "a" if ja_coletados else "w"
    with open(arquivo, modo, encoding="utf-8") as f:
        for i, dep in enumerate(deputados, start=1):
            id_dep = dep["id"]
            if id_dep in ja_coletados:
                continue
            despesas = coletar_despesas_deputado(id_dep, ano)
            for d in despesas:
                d["id_deputado"] = id_dep
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
            f.flush()
            total += len(despesas)
            print(f"   [{i}/{len(deputados)}] {dep['nome']:<35} {len(despesas):>4} despesas")
    print(f"   Total de despesas coletadas nesta execução: {total}")
    return total


def _ids_ja_coletados(arquivo) -> set[int]:
    """Lê o arquivo de despesas (se existir) para permitir retomar a coleta."""
    ids: set[int] = set()
    if arquivo.exists():
        with open(arquivo, encoding="utf-8") as f:
            for linha in f:
                try:
                    ids.add(json.loads(linha)["id_deputado"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return ids


def main() -> None:
    config.garantir_pastas()
    inicio = datetime.now()

    deputados = coletar_deputados()
    if not deputados:
        print("Não foi possível coletar deputados. Encerrando.")
        sys.exit(1)

    totais_por_ano: dict[int, int] = {}
    for ano in config.ANOS_ANALISE:
        totais_por_ano[ano] = coletar_todas_despesas(deputados, ano)

    resumo = {
        "executado_em": inicio.isoformat(timespec="seconds"),
        "duracao_segundos": round((datetime.now() - inicio).total_seconds(), 1),
        "anos_analise": config.ANOS_ANALISE,
        "ano_analise": config.ANO_ANALISE,
        "qtd_deputados": len(deputados),
        "qtd_despesas_coletadas": sum(totais_por_ano.values()),
        "qtd_despesas_por_ano": totais_por_ano,
        "endpoints_utilizados": [
            "/deputados",
            "/deputados/{id}/despesas",
        ],
    }
    with open(config.DIR_BRUTOS / "resumo_coleta.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    print(">> Coleta finalizada.")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
