"""
Configurações centrais do pipeline de gastos públicos.

Reúno aqui tudo que pode mudar entre uma execução e outra (ano analisado,
caminhos de saída, parâmetros da API) para não espalhar "números mágicos"
pelo código. Assim fica fácil reapontar o projeto para outro ano ou outro
recorte de estados sem mexer na lógica de coleta.
"""

from pathlib import Path

# Raiz do projeto (a pasta que contém src/, dados/, etc.)
RAIZ = Path(__file__).resolve().parent.parent

# Pastas de trabalho
DIR_DADOS = RAIZ / "dados"
DIR_BRUTOS = DIR_DADOS / "brutos"
DIR_SAIDAS = RAIZ / "saidas"
DIR_GRAFICOS = DIR_SAIDAS / "graficos"
DIR_RELATORIOS = RAIZ / "relatorios"
DIR_DOCS = RAIZ / "docs"

# Banco de dados (SQLite — não exige servidor, é portátil e cabe no repositório)
BANCO = DIR_DADOS / "gastos_publicos.db"

# ---------------------------------------------------------------------------
# Parâmetros da API de Dados Abertos da Câmara dos Deputados
# Documentação: https://dadosabertos.camara.leg.br/swagger/api.html
# ---------------------------------------------------------------------------
API_BASE = "https://dadosabertos.camara.leg.br/api/v2"

# Anos da análise das despesas (Cota para o Exercício da Atividade Parlamentar).
ANOS_ANALISE = [2024, 2025]

# Ano mais recente (compatibilidade com scripts que usam um único ano).
ANO_ANALISE = max(ANOS_ANALISE)

# Rótulo para dashboard e relatórios.
ROTULO_PERIODOS = (
    str(ANOS_ANALISE[0])
    if len(ANOS_ANALISE) == 1
    else f"{min(ANOS_ANALISE)}–{max(ANOS_ANALISE)}"
)

# Itens por página (a API aceita até 100).
ITENS_POR_PAGINA = 100

# Política de retentativa: a API costuma devolver 504 esporádico sob carga.
MAX_TENTATIVAS = 6
ESPERA_BASE_SEG = 2.0   # backoff exponencial: 2, 4, 8, ...
TIMEOUT_SEG = 35

# Recorte de coleta.
#   - Se UFS_INCLUIDAS estiver vazio, considera todos os estados.
#   - MAX_DEPUTADOS limita o volume para execuções de demonstração; use None
#     para coletar todos os parlamentares da legislatura corrente.
UFS_INCLUIDAS: list[str] = []        # ex.: ["DF", "GO", "SP"]
MAX_DEPUTADOS: int | None = None

# K-Means: mínimo de grupos (evita k=2 pouco informativo) e teto da busca.
K_MEANS_MIN = 5
K_MEANS_MAX = 8

# Cabeçalho padrão das requisições.
HEADERS = {"Accept": "application/json", "User-Agent": "projeto-integrador-bigdata/1.0"}


def garantir_pastas() -> None:
    """Cria as pastas de trabalho caso ainda não existam."""
    for pasta in (DIR_BRUTOS, DIR_GRAFICOS, DIR_RELATORIOS, DIR_DOCS):
        pasta.mkdir(parents=True, exist_ok=True)
