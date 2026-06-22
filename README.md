# Projeto Integrador — Pipeline de Inteligência em Gastos Públicos

**Aluno:** Carlos Ranyere da Natividade Pereira  
**Curso:** Tecnólogo em Big Data e Inteligência Analítica  
**Disciplina:** Projeto Integrador

Pipeline de dados sobre despesas da **Cota para o Exercício da Atividade Parlamentar (CEAP)** da Câmara dos Deputados: coleta via API, tratamento, armazenamento, análise exploratória, dashboard e Machine Learning.

## API utilizada

**Dados Abertos da Câmara dos Deputados** — `https://dadosabertos.camara.leg.br/api/v2`

Endpoints: `/deputados` e `/deputados/{id}/despesas`.

Justificativa: fonte oficial, pública, documentada e com paginação, permitindo coleta automatizada de despesas parlamentares por categoria, partido, estado e fornecedor.

## Estrutura do projeto

```
projeto-integrador-gastos-publicos/
├── src/
│   ├── coleta.py                 # script de coleta automatizada
│   ├── tratamento.py             # tratamento e carga no banco
│   ├── banco.py                  # modelagem (SQLite)
│   ├── analise_exploratoria.py   # análise exploratória
│   ├── machine_learning.py       # clusterização e detecção de anomalias
│   ├── gerar_der.py              # Diagrama Entidade-Relacionamento
│   ├── gerar_relatorios.py       # relatórios PDF
│   ├── dashboard.py              # dashboard interativo
│   └── pipeline.py               # execução do pipeline completo
├── dados/
│   ├── brutos/                   # dados brutos da API
│   └── gastos_publicos.db        # banco de dados
├── saidas/
│   ├── graficos/                 # gráficos da EDA e ML
│   └── despesas_tratadas.csv     # base tratada
├── docs/
│   ├── der.png
│   └── dicionario_dados.md
├── relatorios/
│   ├── relatorio_parcial_entrega1.pdf
│   ├── relatorio_final_entrega2.pdf
│   └── roteiro_video.md
└── requirements.txt
```

## Como executar

```bash
pip install -r requirements.txt
cd src
python3 pipeline.py              # pipeline completo
python3 pipeline.py --sem-coleta   # sem nova coleta
streamlit run dashboard.py       # dashboard
```

## Acesso público ao dashboard

http://45.39.210.31:8501

## Entregáveis

### Entrega 1
- Script de coleta: `src/coleta.py`
- Base de dados: `dados/gastos_publicos.db`
- DER: `docs/der.png`
- Dicionário de dados: `docs/dicionario_dados.md`
- Relatório parcial: `relatorios/relatorio_parcial_entrega1.pdf`

### Entrega 2
- Relatório final: `relatorios/relatorio_final_entrega2.pdf`
- Dashboard: `src/dashboard.py`
- Código de Machine Learning: `src/machine_learning.py`
- Base tratada: `saidas/despesas_tratadas.csv`
- Roteiro do vídeo: `relatorios/roteiro_video.md`
- Código-fonte completo: pasta `src/`

## Bibliotecas utilizadas

requests, pandas, numpy, scikit-learn, matplotlib, plotly, seaborn, streamlit, reportlab.
