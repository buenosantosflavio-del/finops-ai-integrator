import sqlite3
import requests
import re
from database import DB_NAME, inicializar_banco

inicializar_banco()

OLLAMA_URL = "http://" + "127.0.0.1:11434/api/generate"
MODELO = "qwen3:4b"

SCHEMA_BANCO = """
Tabelas disponíveis no banco SQLite:
1. lancamentos_erp (
    id_lancamento INTEGER,
    tipo TEXT,                -- 'RECEBER' ou 'PAGAR'
    cliente_fornecedor TEXT,
    cnpj TEXT,
    nosso_numero TEXT,
    linha_digitavel TEXT,
    valor_original REAL,
    valor_pago REAL,
    data_vencimento TEXT,
    status TEXT,              -- 'PENDENTE', 'PAGO', 'ATRASADO', 'DIVERGENTE', 'AGENDADO_DDA'
    data_baixa TEXT
)
2. divergencias_auditoria (
    id_divergencia INTEGER,
    nosso_numero TEXT,
    tipo_alerta TEXT,         -- 'PAGAMENTO_A_MENOR', 'JUROS_ATRASO', 'DIVERGENCIA_DDA'
    diferenca_valor REAL,
    descricao_auditoria TEXT,
    criado_em TEXT
)
"""

def limpar_resposta_llm(texto):
    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
    texto = texto.replace("```sql", "").replace("```", "").strip()
    return texto

def gerar_sql(pergunta_usuario):
    prompt = f"""/no_think
Você é um especialista em SQL SQLite. Converta a pergunta financeira abaixo em UMA ÚNICA query SQL válida.
Retorne APENAS o código SQL puro, sem explicações, começando com SELECT.

{SCHEMA_BANCO}

Pergunta: {pergunta_usuario}
SQL:"""

    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODELO, "prompt": prompt, "stream": False},
        timeout=120
    )
    sql = limpar_resposta_llm(resp.json().get("response", ""))
    match = re.search(r'(SELECT\s+.*?;?)$', sql, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else sql

def executar_sql(query):
    if not query.upper().startswith("SELECT"):
        return "ERRO_SEGURANCA: Apenas consultas SELECT são permitidas."
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return f"ERRO_SQL: {e}"

def perguntar_ao_controller(pergunta):
    print(f"\n[PERGUNTA DO DIRETOR]: {pergunta}")
    sql_gerado = gerar_sql(pergunta)
    print(f"[SQL GERADO PELA IA]: {sql_gerado}")
    
    dados_reais = executar_sql(sql_gerado)
    print(f"[DADOS DO BANCO]: {dados_reais}")

    prompt_parecer = f"""/no_think
Você é um Controller Financeiro Sênior. Responda à pergunta do diretor em Português do Brasil de forma executiva, direta e exata ao centavo, baseando-se EXCLUSIVAMENTE nos dados retornados do banco SQL abaixo. Não invente números.

Pergunta: {pergunta}
Dados oficiais do banco SQLite: {dados_reais}
Parecer Executivo:"""

    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODELO, "prompt": prompt_parecer, "stream": False},
        timeout=120
    )
    parecer = limpar_resposta_llm(resp.json().get("response", ""))
    print(f"[PARECER DO AGENTE]: {parecer}\n" + "-"*70)

if __name__ == "__main__":
    print("=== AGENTE DE CONTROLADORIA IA (TEXT-TO-SQL DETERMINÍSTICO) ===")
    perguntas_teste = [
        "Quais clientes estão com boletos com status ATRASADO e qual o valor_original de cada um?",
        "Qual a soma total (SUM de valor_original) das contas do tipo PAGAR que estão com status PENDENTE?",
        "Liste todas as ocorrências registradas na tabela divergencias_auditoria."
    ]
    for p in perguntas_teste:
        perguntar_ao_controller(p)