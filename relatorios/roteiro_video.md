# Roteiro do Vídeo de Apresentação (até 10 minutos)

**Projeto Integrador — Pipeline de Inteligência em Gastos Públicos**
**Aluno:** Carlos Ranyere da Natividade Pereira
**Curso:** Tecnólogo em Big Data e Inteligência Analítica

> Dica de gravação: deixe abertos, em abas, o VS Code (na pasta `src`), um
> terminal e o dashboard no navegador. Fale com naturalidade, mostrando a tela.
> O objetivo é demonstrar domínio, não ler slides.

---

## 0. Abertura (0:00 – 0:30)
"Olá, professor. Meu nome é Carlos Ranyere e este é o meu Projeto Integrador.
Eu construí um pipeline completo de dados sobre gastos públicos, usando as
despesas da cota parlamentar da Câmara dos Deputados. Vou mostrar desde a coleta
automatizada até a análise com Machine Learning."

## 1. Tema e API escolhida (0:30 – 1:30)
- Tema: análise da CEAP (Cota para o Exercício da Atividade Parlamentar).
- API: Dados Abertos da Câmara dos Deputados (v2).
- Por que essa API: oficial, pública, gratuita, bem documentada, com paginação —
  ideal para exercitar coleta automatizada.
- Perguntas que quis responder: onde o dinheiro é gasto? Quem gasta mais? Há
  despesas fora do padrão?

## 2. Pipeline de dados (1:30 – 2:30)
Mostrar a pasta `src` e explicar a divisão:
- `coleta.py` → busca os dados na API;
- `tratamento.py` → limpa e padroniza;
- `banco.py` → cria o modelo no SQLite;
- `analise_exploratoria.py` → estatísticas e gráficos;
- `machine_learning.py` → clusterização e anomalias;
- `dashboard.py` → painel interativo;
- `pipeline.py` → roda tudo em sequência.

## 3. Demonstração da coleta (2:30 – 4:00)
- Abrir `coleta.py` e mostrar a função `_get` (retentativa/backoff para os
  HTTP 504 da API) e o tratamento de **paginação** pelos links `rel='next'`.
- Destacar o **checkpoint** (JSON Lines), que permite retomar a coleta.
- Rodar no terminal (ou mostrar log) a coleta de um deputado para evidenciar
  que NÃO é download manual.
- Mostrar `dados/brutos/resumo_coleta.json` com o total coletado.

## 4. Banco de dados e modelagem (4:00 – 5:00)
- Abrir o DER (`docs/der.png`): três tabelas — deputados, despesas (fato) e
  fornecedores; explicar PKs e FKs e o relacionamento 1:N.
- Abrir o banco `gastos_publicos.db` (ex.: DB Browser) e mostrar as tabelas
  preenchidas. Citar o dicionário de dados.

## 5. Dashboard (5:00 – 7:00)
- `streamlit run dashboard.py`.
- Mostrar os indicadores do topo reagindo aos **filtros** (UF, partido, categoria).
- Passar por: evolução mensal, categorias, ranking de deputados, gasto por
  estado e concentração de fornecedores.
- Frase-chave: "cada gráfico responde a uma pergunta, não é gráfico por gráfico".

## 6. Machine Learning (7:00 – 9:00)
- **Clusterização (K-Means):** explicar o vetor de perfil de gasto por categoria,
  a escolha de k pela silhueta e o que cada grupo representa.
- **Detecção de anomalias (Isolation Forest):** explicar o z-score por categoria
  e mostrar a tabela de despesas atípicas. Reforçar: anomalia ≠ irregularidade;
  é priorização para auditoria.

## 7. Resultados, dificuldades e melhorias (9:00 – 9:45)
- Resultado: pipeline completo e funcional sobre dados reais.
- Dificuldade principal: instabilidade da API (resolvida com retentativa).
- Melhorias futuras: incluir mais anos para análise de tendência, cruzar com
  dados de outros órgãos e publicar o dashboard na nuvem.

## 8. Encerramento (9:45 – 10:00)
"Esse projeto me mostrou, na prática, o trabalho de um analista de dados:
da origem do dado até a interpretação. Obrigado, professor."

---

### Checklist antes de gravar
- [ ] Coleta executada e `resumo_coleta.json` visível.
- [ ] Banco populado (deputados, despesas, fornecedores).
- [ ] Dashboard abrindo sem erro.
- [ ] Gráficos e relatórios PDF gerados.
- [ ] Áudio claro e tela legível (fonte do editor ampliada).
