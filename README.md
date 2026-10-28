# MacroPulse Intelligence Platform

Real-time macroeconomic intelligence terminal and risk scoring engine designed to unify multi-asset market data, yield curves, news sentiment, and physical activity indicators into a single decision layer.

---

## 1. Problema de Negócio e Contexto

A tomada de decisão em alocação de ativos e avaliação de risco macroeconômico sofre criticamente com a fragmentação temporal e estrutural das fontes públicas e financeiras:

1. **Heterogeneidade de Frequência e Formato:** Cotações de mercado (ações, commodities, moedas) operam em tempo real; curvas de juros e indicadores de política monetária atualizam diariamente; métricas de atividade física e logística possuem periodicidade irregular; e fluxos de notícias demandam extração semântica contínua.
2. **Latência Analítica e Falta de Padronização:** Profissionais e analistas de risco despendem a maior parte do tempo conciliando dezenas de fontes heterogêneas, atrasando a identificação de mudanças estruturais de regime de mercado e o diagnóstico de risco sistêmico.

O MacroPulse foi projetado como um motor de inteligência analítica centralizado para:
- Ingerir dados de múltiplas fontes públicas e de mercado de forma assíncrona.
- Normalizar séries temporais díspares em métricas de risco padronizadas.
- Detectar dinamicamente o regime macroeconômico vigente e recalibrar a ponderação de fatores de estresse.
- Expor uma API REST assíncrona de baixa latência e relatórios determinísticos para suporte à decisão.

---

## 2. Processo e Racional das Escolhas Técnicas

### 2.1. Classificador de Regime e Alocação Dinâmica de Pesos
- **Classificação em 5 Regimes:** O motor classifica o ambiente macro em cinco estados discretos (*Expansion*, *Recovery*, *Overheating*, *Stagflation*, *Recession*) utilizando uma matriz de dois fatores fundamentais: momentum do índice de referência (S&P 500) e nível absoluto do índice de volatilidade (VIX).
- **Dynamic Weight Engine vs. Modelos Estáticos:** Em cenários de expansão, indicadores de atividade física e sentimento lideram o ciclo. Em contrapartida, durante crises de liquidez e recessão, a curva de juros (spread 10Y-2Y) e o VIX concentram 85% do risco sistêmico. A adoção de pesos dinâmicos por regime elimina a distorção comum de modelos estáticos de pontuação que subestimam choques repentinos de volatilidade.

### 2.2. Arquitetura Backend e I/O Assíncrono (FastAPI)
- **FastAPI vs. Flask Síncrono:** A extração contínua de cotações, curvas de juros do tesouro e feeds de notícias depende massivamente de operações de rede com alta latência de I/O externo. A escolha de FastAPI com `asyncio` e `httpx` viabilizou coletas paralelas sem bloqueio de threads, reduzindo drasticamente o tempo total do ciclo de ingestão.
- **Validação com Schemas Pydantic:** Todas as entradas e respostas da API são rigorosamente tipadas via Pydantic v2, garantindo integridade de contratos de dados e documentação OpenAPI nativa.

### 2.3. Motor de Tese Heurística e Prontidão para IA
- **Geração Determinística de Teses:** A geração de diagnósticos macroeconômicos foi estruturada inicialmente sobre regras heurísticas determinísticas auditáveis. Isso garante que cada conclusão emitida pela plataforma possa ser rastreada matematicamente até o indicador numérico subjacente, eliminando alucinações.
- **Interface Desacoplada para LLMs:** O módulo `macro_intelligence.py` foi desenhado com uma interface agnóstica de síntese, permitindo plugar modelos de linguagem locais (como Ollama) ou em nuvem sem alterar o pipeline de cálculo quantitativo.

---

## 3. Resultados Atingidos e Métricas de Validação

### 3.1. Eficiência do Pipeline
- **Latência de Ingestão e Processamento:** Consolidação paralela de múltiplos ativos e cálculo do Composite Risk Score em tempo de execução sub-segundo.
- **Métricas do Composite Risk Score:** Normalização min-max e Z-Score de séries históricas gerando um índice sintético de estresse financeiro escalonado de 0 (estabilidade máxima) a 100 (estresse sistêmico severo).

### 3.2. Módulos Analíticos Validados
- **Yield Curve Monitor:** Rastreamento do spread entre taxas de juros de 10 anos e 2 anos com alertas automáticos para inversão de curva (sinalizador antecipador de recessões).
- **Cross-Asset Correlation Engine:** Matriz de correlação móvel calculada dinamicamente entre commodities, títulos soberanos e índices acionários.
- **Backtest Engine:** Módulo de validação histórica para avaliar a precisão preditiva dos sinais gerados pelo indicador de regime frente a crises financeiras passadas.

---

## 4. Arquitetura da Solução e Estrutura

```text
macropulse/
├── backend/
│   ├── api/                    # Rotas FastAPI e validação de schemas Pydantic
│   ├── db/                     # Camada de persistência relacional
│   ├── etl/                    # Pipeline assíncrono de extração e transformação
│   │   ├── extract.py          # Conectores de APIs de mercado
│   │   ├── transform.py        # Normalização e cálculo de indicadores
│   │   ├── load.py             # Carga em banco de dados
│   │   ├── news_engine.py      # Extração e scoring de sentimento de notícias
│   │   └── activity_tracking.py# Indicadores de atividade real e mobilidade
│   ├── services/               # Motores centrais de inteligência
│   │   ├── macro_intelligence.py # Detecção de regime e pesos dinâmicos
│   │   ├── alert_engine.py     # Monitoramento de limiares de estresse
│   │   ├── backtest_engine.py  # Avaliação histórica de performance
│   │   └── correlation.py      # Cálculo de matriz de correlação contínua
│   └── workers/                # Tarefas agendadas em segundo plano
├── frontend/                   # Interface web do terminal analítico
├── docs/                       # Documentação de arquitetura e diagramas
├── tests/                      # Bateria de testes automatizados com pytest
├── requirements.txt            # Dependências com versões pinadas
└── run_local.ps1               # Script de inicialização em ambiente Windows/PowerShell
```

---

## 5. Como Executar

### 5.1. Pré-requisitos
- Python 3.11 ou superior
- Git

### 5.2. Instalação e Execução Local

1. Clone o repositório:
```bash
git clone https://github.com/RicsonRamos/macropulse.git
cd macropulse
```

2. Crie e ative um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env  # configure as chaves de API necessárias se houver
```

5. Inicialize a API assíncrona:
```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```
A documentação interativa da API estará disponível em `http://localhost:8000/docs`.

### 5.3. Execução dos Testes Automatizados

Para rodar a suíte de testes de validação matemática e de rotas:
```bash
pytest tests/ -v
```
