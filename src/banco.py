"""
Definição do modelo de dados e criação do banco SQLite.

Optei por SQLite porque o projeto precisa de um banco relacional de verdade
(com chaves primárias e estrangeiras), mas sem a complicação de subir um
servidor. O arquivo .db fica junto do projeto e pode ser aberto em qualquer
ferramenta (DBeaver, DB Browser for SQLite) para inspeção.

Modelo (3 entidades):

    deputados (1) ----< despesas >---- (1) fornecedores

  - Um deputado tem muitas despesas.
  - Um fornecedor aparece em muitas despesas.
  - A tabela 'despesas' é o fato central; 'deputados' e 'fornecedores' são as
    dimensões.
"""

from __future__ import annotations

import sqlite3

import config

DDL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS despesas;
DROP TABLE IF EXISTS deputados;
DROP TABLE IF EXISTS fornecedores;

-- Dimensão: parlamentares em exercício
CREATE TABLE deputados (
    id_deputado     INTEGER PRIMARY KEY,
    nome            TEXT    NOT NULL,
    sigla_partido   TEXT,
    sigla_uf        TEXT,
    id_legislatura  INTEGER,
    email           TEXT,
    url_foto        TEXT
);

-- Dimensão: fornecedores/beneficiários das despesas
CREATE TABLE fornecedores (
    cnpj_cpf        TEXT PRIMARY KEY,   -- identificador, tratado como TEXTO
    nome            TEXT
);

-- Fato: despesas da Cota para o Exercício da Atividade Parlamentar (CEAP)
CREATE TABLE despesas (
    id_despesa          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_deputado         INTEGER NOT NULL,
    cnpj_cpf_fornecedor TEXT,
    ano                 INTEGER,
    mes                 INTEGER,
    tipo_despesa        TEXT,
    tipo_documento      TEXT,
    cod_documento       INTEGER,
    num_documento       TEXT,
    data_documento      TEXT,            -- ISO 'YYYY-MM-DD'
    valor_documento     REAL,
    valor_glosa         REAL,
    valor_liquido       REAL,
    url_documento       TEXT,
    FOREIGN KEY (id_deputado)         REFERENCES deputados (id_deputado),
    FOREIGN KEY (cnpj_cpf_fornecedor) REFERENCES fornecedores (cnpj_cpf)
);

-- Índices para acelerar as consultas analíticas mais frequentes
CREATE INDEX idx_despesas_deputado   ON despesas (id_deputado);
CREATE INDEX idx_despesas_fornecedor ON despesas (cnpj_cpf_fornecedor);
CREATE INDEX idx_despesas_tipo       ON despesas (tipo_despesa);
CREATE INDEX idx_despesas_mes        ON despesas (mes);
"""


def conectar() -> sqlite3.Connection:
    """Abre conexão com o banco, garantindo a pasta de dados."""
    config.garantir_pastas()
    con = sqlite3.connect(config.BANCO)
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def criar_esquema() -> None:
    """(Re)cria as tabelas a partir do DDL."""
    con = conectar()
    try:
        con.executescript(DDL)
        con.commit()
        print(f">> Esquema criado em {config.BANCO}")
    finally:
        con.close()


if __name__ == "__main__":
    criar_esquema()
