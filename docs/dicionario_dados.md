# Dicionário de Dados — Pipeline de Gastos Públicos

**Fonte:** API de Dados Abertos da Câmara dos Deputados (`https://dadosabertos.camara.leg.br/api/v2`)
**Base:** Cota para o Exercício da Atividade Parlamentar (CEAP) — despesas dos deputados federais.
**Armazenamento:** banco relacional SQLite (`dados/gastos_publicos.db`).

O modelo tem três entidades. `despesas` é a tabela-fato; `deputados` e
`fornecedores` são as dimensões. Identificadores (CNPJ/CPF, códigos) são
tratados como **texto/inteiro categórico**, nunca como quantidade.

---

## Tabela `deputados`

| Campo | Tipo | Descrição | Exemplo |
|---|---|---|---|
| id_deputado | Inteiro (PK) | Identificador único do parlamentar na Câmara | 204554 |
| nome | Texto | Nome parlamentar | Erika Kokay |
| sigla_partido | Texto | Sigla do partido atual | PT |
| sigla_uf | Texto | Unidade federativa que representa | DF |
| id_legislatura | Inteiro | Legislatura em exercício | 57 |
| email | Texto | E-mail funcional | dep.fulano@camara.leg.br |
| url_foto | Texto | URL da foto oficial | https://.../204554.jpg |

## Tabela `fornecedores`

| Campo | Tipo | Descrição | Exemplo |
|---|---|---|---|
| cnpj_cpf | Texto (PK) | CNPJ ou CPF do fornecedor/beneficiário | 04.252.011/0001-10 |
| nome | Texto | Razão social ou nome do fornecedor | Cia Aérea XYZ |

## Tabela `despesas` (fato)

| Campo | Tipo | Descrição | Exemplo |
|---|---|---|---|
| id_despesa | Inteiro (PK) | Identificador interno do registro (gerado na carga) | 1 |
| id_deputado | Inteiro (FK → deputados) | Deputado que realizou a despesa | 204554 |
| cnpj_cpf_fornecedor | Texto (FK → fornecedores) | Fornecedor da despesa | 04.252.011/0001-10 |
| ano | Inteiro | Ano de referência da despesa | 2024 |
| mes | Inteiro | Mês de referência (1–12) | 5 |
| tipo_despesa | Texto | Categoria da despesa (CEAP) | PASSAGEM AÉREA |
| tipo_documento | Texto | Tipo do documento fiscal | Nota Fiscal |
| cod_documento | Inteiro | Código do documento na Câmara | 7654321 |
| num_documento | Texto | Número do documento fiscal | 000123456 |
| data_documento | Data (YYYY-MM-DD) | Data do documento fiscal | 2024-05-10 |
| valor_documento | Numérico | Valor bruto do documento | 1420.00 |
| valor_glosa | Numérico | Valor glosado (não ressarcido) | 70.00 |
| valor_liquido | Numérico | Valor efetivamente ressarcido (usado nas análises) | 1350.00 |
| url_documento | Texto | Link para o comprovante | https://.../doc.pdf |

---

### Observações de modelagem
- **Chave primária** de `despesas` é interna (`id_despesa`), pois um mesmo
  `cod_documento` pode se repetir entre deputados; a unicidade real é tratada
  na limpeza pela combinação `id_deputado + cod_documento + num_documento`.
- **Valores financeiros** (`valor_*`) são `REAL`; a análise usa `valor_liquido`,
  que é o valor de fato ressarcido ao parlamentar.
- **Datas** são padronizadas em ISO 8601 (`YYYY-MM-DD`).
- **Campos ausentes**: alguns registros não trazem fornecedor (ex.: reembolso
  de bilhete aéreo emitido pela própria Câmara); por isso `cnpj_cpf_fornecedor`
  aceita nulo e a FK é opcional.
