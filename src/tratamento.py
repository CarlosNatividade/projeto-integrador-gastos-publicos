"""
Tratamento dos dados brutos e carga no banco (etapa 7.2 e 7.3 da especificação).

Aqui pego o que veio cru da API (JSON) e deixo pronto para análise:
  * datas viram datas de verdade (ISO);
  * valores financeiros viram número (float), com vírgula/ponto normalizados;
  * identificadores (CNPJ/CPF) ficam como texto — não são quantidade;
  * registros sem identificação de documento e duplicados são tratados;
  * separo as dimensões (deputados, fornecedores) do fato (despesas).

No fim, gravo tudo no SQLite e também exporto um CSV e um Parquet com a base
tratada, para quem quiser abrir fora do banco.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

import banco
import config


def carregar_deputados_brutos() -> pd.DataFrame:
    caminho = config.DIR_BRUTOS / "deputados.json"
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)
    df = df.rename(
        columns={
            "id": "id_deputado",
            "siglaPartido": "sigla_partido",
            "siglaUf": "sigla_uf",
            "idLegislatura": "id_legislatura",
            "urlFoto": "url_foto",
        }
    )
    colunas = ["id_deputado", "nome", "sigla_partido", "sigla_uf",
               "id_legislatura", "email", "url_foto"]
    for c in colunas:
        if c not in df.columns:
            df[c] = None
    return df[colunas].drop_duplicates(subset="id_deputado")


def carregar_despesas_brutas() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for ano in config.ANOS_ANALISE:
        caminho = config.DIR_BRUTOS / f"despesas_{ano}.jsonl"
        if not caminho.exists():
            print(f"   ! Arquivo ausente: {caminho.name} — pulando.")
            continue
        registros = []
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    registros.append(json.loads(linha))
        print(f"   {len(registros)} despesas brutas de {ano}.")
        if registros:
            frames.append(pd.DataFrame(registros))
    if not frames:
        raise FileNotFoundError(
            "Nenhum arquivo de despesas encontrado. Execute a coleta primeiro."
        )
    df = pd.concat(frames, ignore_index=True)
    print(f"   {len(df)} despesas brutas no total ({config.ROTULO_PERIODOS}).")
    return df


def _para_numero(serie: pd.Series) -> pd.Series:
    """Converte valores financeiros para float de forma tolerante."""
    if serie.dtype.kind in "fi":
        return serie.astype(float)
    return (
        serie.astype(str)
        .str.replace(r"[^\d,.-]", "", regex=True)
        .str.replace(".", "", regex=False)   # separador de milhar
        .str.replace(",", ".", regex=False)  # decimal brasileiro
        .replace({"": np.nan})
        .astype(float)
    )


def tratar_despesas(df: pd.DataFrame) -> pd.DataFrame:
    print(">> Tratando despesas...")
    antes = len(df)

    df = df.rename(
        columns={
            "tipoDespesa": "tipo_despesa",
            "tipoDocumento": "tipo_documento",
            "codDocumento": "cod_documento",
            "numDocumento": "num_documento",
            "dataDocumento": "data_documento",
            "valorDocumento": "valor_documento",
            "valorGlosa": "valor_glosa",
            "valorLiquido": "valor_liquido",
            "urlDocumento": "url_documento",
            "cnpjCpfFornecedor": "cnpj_cpf_fornecedor",
            "nomeFornecedor": "nome_fornecedor",
        }
    )

    # Tipos numéricos
    for col in ("valor_documento", "valor_glosa", "valor_liquido"):
        if col in df:
            df[col] = _para_numero(df[col])

    # Inteiros de calendário
    for col in ("ano", "mes"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Datas como datas (a API às vezes manda só a data, às vezes com hora)
    if "data_documento" in df:
        df["data_documento"] = (
            pd.to_datetime(df["data_documento"], errors="coerce")
            .dt.strftime("%Y-%m-%d")
        )

    # Identificadores como texto, normalizando vazios
    df["cnpj_cpf_fornecedor"] = (
        df.get("cnpj_cpf_fornecedor", pd.Series(dtype=str))
        .astype(str).str.strip().replace({"": None, "nan": None, "None": None})
    )
    df["nome_fornecedor"] = (
        df.get("nome_fornecedor", pd.Series(dtype=str))
        .astype(str).str.strip().replace({"": None, "nan": None, "None": None})
    )

    # Remoção de duplicatas exatas de documento por deputado
    chaves = [c for c in ("id_deputado", "cod_documento", "num_documento") if c in df]
    df = df.drop_duplicates(subset=chaves)

    # Descarto linhas sem valor líquido (não servem para análise financeira)
    df = df[df["valor_liquido"].notna()]

    # Valor líquido negativo/zero é raro (estorno); mantenho mas sinalizo no relatório.
    depois = len(df)
    print(f"   {antes} -> {depois} despesas após tratamento "
          f"({antes - depois} removidas).")
    return df


def montar_fornecedores(despesas: pd.DataFrame) -> pd.DataFrame:
    forn = (
        despesas[["cnpj_cpf_fornecedor", "nome_fornecedor"]]
        .dropna(subset=["cnpj_cpf_fornecedor"])
        .drop_duplicates(subset="cnpj_cpf_fornecedor")
        .rename(columns={"cnpj_cpf_fornecedor": "cnpj_cpf", "nome_fornecedor": "nome"})
    )
    return forn


def persistir(deputados: pd.DataFrame, fornecedores: pd.DataFrame,
              despesas: pd.DataFrame) -> None:
    print(">> Gravando no banco SQLite...")
    banco.criar_esquema()
    con = banco.conectar()
    try:
        deputados.to_sql("deputados", con, if_exists="append", index=False)
        fornecedores.to_sql("fornecedores", con, if_exists="append", index=False)

        colunas_despesa = [
            "id_deputado", "cnpj_cpf_fornecedor", "ano", "mes", "tipo_despesa",
            "tipo_documento", "cod_documento", "num_documento", "data_documento",
            "valor_documento", "valor_glosa", "valor_liquido", "url_documento",
        ]
        for c in colunas_despesa:
            if c not in despesas:
                despesas[c] = None
        despesas[colunas_despesa].to_sql("despesas", con, if_exists="append", index=False)
        con.commit()

        for tabela in ("deputados", "fornecedores", "despesas"):
            n = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            print(f"   {tabela}: {n} linhas")
    finally:
        con.close()

    # Cópias analíticas da base tratada
    despesas.to_csv(config.DIR_SAIDAS / "despesas_tratadas.csv", index=False)
    try:
        despesas.to_parquet(config.DIR_SAIDAS / "despesas_tratadas.parquet", index=False)
    except Exception as e:  # parquet exige pyarrow; não é obrigatório
        print(f"   (Parquet não gerado: {e})")


def main() -> None:
    deputados = carregar_deputados_brutos()
    despesas_brutas = carregar_despesas_brutas()
    despesas = tratar_despesas(despesas_brutas)
    fornecedores = montar_fornecedores(despesas)
    persistir(deputados, fornecedores, despesas)
    print(">> Tratamento e carga concluídos.")


if __name__ == "__main__":
    main()
