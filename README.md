
# FinOps AI Integrator
### Automação Financeira, Conciliação e Inteligência Artificial com Python

Projeto demonstrativo de automação financeira que combina uma API REST, banco de dados relacional, auditoria de pagamentos, agente de inteligência artificial e painel executivo interativo.

A aplicação simula a troca de informações entre um sistema financeiro empresarial (ERP) e serviços bancários, permitindo testar processos de conciliação, identificar divergências e consultar dados financeiros utilizando linguagem natural.

## Funcionalidades

### 1. API REST e Webhooks
- Recebimento de eventos simulados de pagamento.
- Atualização de informações financeiras no banco de dados local.
- Controle de idempotência para evitar o reprocessamento de eventos com o mesmo identificador.
- Consulta ao resumo financeiro por meio de endpoints REST.

### 2. Conciliação e Auditoria Financeira
- Comparação entre valores originais e valores recebidos.
- Identificação de pagamentos divergentes.
- Registro de ocorrências em uma tabela de auditoria.
- Simulação de sincronização de informações de contas a pagar (DDA).

### 3. Agente de IA para Consultas Financeiras
- Interpretação de perguntas em linguagem natural.
- Geração de consultas SQL com auxílio de um modelo de linguagem local.
- Execução das consultas sobre uma base financeira SQLite.
- Apresentação dos resultados para análise de controladoria.

O agente utiliza a abordagem Text-to-SQL. As respostas devem ser verificadas, especialmente antes de qualquer utilização em processos financeiros reais.

### 4. Painel Executivo
- Indicadores financeiros de contas a receber e a pagar.
- Visualização de títulos e lançamentos.
- Consulta aos registros de divergências.
- Interface em português desenvolvida com Streamlit.
- Área interativa para perguntas ao agente de IA.

## Tecnologias Utilizadas

- **Linguagem:** Python 3.12
- **API e backend:** FastAPI, Pydantic e Uvicorn
- **Banco de dados:** SQLite
- **Análise de dados:** Pandas
- **Interface:** Streamlit
- **Inteligência Artificial:** Ollama com modelo Qwen3:4b
- **Consultas:** SQL e abordagem Text-to-SQL

## Estrutura do Projeto

- `database.py` — banco de dados e registros financeiros simulados
- `webhook_api.py` — endpoints de integração, conciliação e auditoria
- `ai_controller_agent.py` — agente de IA para consultas financeiras
- `painel_executivo.py` — painel executivo desenvolvido com Streamlit
- `requirements.txt` — dependências Python
- `.gitignore` — exclusão de arquivos locais e temporários
- `screenshots/` — capturas de tela da aplicação

## Como Executar Localmente

Requisitos:
- Python 3.12
- Dependências do projeto instaladas
- Ollama instalado e configurado com o modelo `qwen3:4b`

### 1. Instalar as dependências

No terminal, dentro da pasta do projeto:

`py -3.12 -m pip install -r requirements.txt`

### 2. Inicializar o banco de dados

Caso a base local ainda não tenha sido criada:

`py -3.12 -c "from database import inicializar_banco; inicializar_banco()"`

### 3. Iniciar a API

`py -3.12 -m uvicorn webhook_api:app --reload`

Documentação interativa (Swagger):

http://127.0.0.1:8000/docs

### 4. Executar o painel executivo

Em outro terminal:

`py -3.12 -m streamlit run painel_executivo.py`

Painel:

http://localhost:8501

### 5. Executar o agente de IA

Com o Ollama em funcionamento e o modelo Qwen3:4b disponível:

`py -3.12 ai_controller_agent.py`

## Endpoints Demonstrativos

- `GET /erp/resumo-caixa` — resumo das informações financeiras
- `POST /webhook/itau/baixa-boleto` — simulação de recebimento de evento bancário
- `POST /erp/sincronizar-lote-dda` — simulação de sincronização de informações DDA

A referência ao Itaú no nome de um endpoint faz parte do cenário de teste e não representa integração oficial com o banco.

## Cenários Testados

Durante o desenvolvimento foram realizados testes com dados fictícios, incluindo:

- Recebimento de evento de pagamento.
- Identificação de uma diferença de R$ 300,00 entre valor original e valor recebido.
- Tratamento de evento duplicado por identificador.
- Registro e visualização de divergência financeira.
- Consultas ao banco de dados por meio do agente de IA.
- Visualização dos indicadores no painel Streamlit.

## Limitações do Projeto

Este repositório apresenta uma **prova de conceito (PoC)** desenvolvida para fins de estudo e demonstração técnica.

- Todos os dados financeiros utilizados são fictícios.
- Não existe conexão operacional com bancos ou ERPs reais.
- Não são realizados pagamentos, transferências ou cobranças reais.
- A aplicação foi testada em ambiente local.
- Ainda não foram implementados todos os controles necessários para utilização em produção.

## Melhorias Previstas para Produção

Uma evolução para ambientes empresariais exigiria, entre outras medidas:

- Integração e autenticação com APIs oficiais, incluindo mTLS quando exigido.
- Validação de autenticidade dos webhooks conforme as especificações do provedor.
- Autenticação e controle de acesso de usuários.
- Restrição efetiva de consultas do agente ao banco de dados.
- Uso de tipos numéricos adequados para valores monetários, como Decimal e NUMERIC.
- Mecanismos de filas, reprocessamento e recuperação de falhas.
- Testes de segurança, monitoramento, logs e procedimentos de implantação.
- Adequação aos requisitos de proteção de dados aplicáveis.

Essas melhorias são propostas de evolução e não funcionalidades atualmente implementadas.

## Objetivo

Demonstrar conhecimentos práticos em desenvolvimento Python, APIs REST, SQL, automação de processos financeiros, auditoria e aplicação de modelos de linguagem em consultas a dados estruturados.
