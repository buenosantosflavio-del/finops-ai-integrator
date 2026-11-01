import streamlit as st
import sqlite3
import pandas as pd
import requests
import re
from database import DB_NAME, inicializar_banco
from ai_controller_agent import gerar_sql, executar_sql, limpar_resposta_llm, OLLAMA_URL, MODELO

st.set_page_config(page_title="FinOps AI - Controladoria & Conciliação", layout="wide")
inicializar_banco()

st.title("🏦 FinOps AI Integrator — Painel de Controladoria e Conciliação Bancária")
st.markdown("Monitoramento em tempo real da integração **API Bancária (Itaú Webhook / DDA) ↔ ERP** e Auditoria via Inteligência Artificial.")

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df_erp = pd.read_sql_query("SELECT * FROM lancamentos_erp", conn)
    df_aud = pd.read_sql_query("SELECT * FROM divergencias_auditoria", conn)
    conn.close()
    return df_erp, df_aud

df_erp, df_aud = carregar_dados()

# 1. KPIs Executivos em Português
col1, col2, col3, col4 = st.columns(4)
total_receber = df_erp[df_erp['tipo'] == 'RECEBER']['valor_original'].sum()
total_atrasado = df_erp[df_erp['status'] == 'ATRASADO']['valor_original'].sum()
total_pagar_dda = df_erp[(df_erp['tipo'] == 'PAGAR') & (df_erp['status'] == 'PENDENTE')]['valor_original'].sum()
qtd_alertas = len(df_aud)


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



col1.metric("Total em Boletos Emitidos", formatar_reais(total_receber))
col2.metric("Inadimplência (Boletos Atrasados)", formatar_reais(total_atrasado), delta="-Risco de Caixa", delta_color="inverse")
col3.metric("Contas a Pagar Pendentes (DDA)", formatar_reais(total_pagar_dda))
col4.metric("Alertas de Auditoria (Divergências)", f"{qtd_alertas} ocorrência(s)", delta="Atenção" if qtd_alertas > 0 else "OK", delta_color="inverse")

st.divider()

# 2. Visão de Tabelas (ERP + Alertas de Fraude/Divergência)
aba1, aba2 = st.tabs(["📊 Lançamentos no ERP (Contas a Receber e DDA)", "🚨 Alertas da Auditoria Automática (Webhooks)"])

with aba1:
    st.subheader("Base Sincronizada do ERP")
    st.dataframe(
        df_erp.rename(columns={
            "id_lancamento": "ID",
            "tipo": "Tipo",
            "cliente_fornecedor": "Cliente / Fornecedor",
            "cnpj": "CNPJ",
            "nosso_numero": "Número do Boleto",
            "linha_digitavel": "Linha Digitável",
            "valor_original": "Valor Original (R$)",
            "valor_pago": "Valor Pago (R$)",
            "data_vencimento": "Vencimento",
            "status": "Situação",
            "data_baixa": "Data da Baixa"
        }),
        use_container_width=True,
        hide_index=True
    )


with aba2:
    st.subheader("Divergências Detectadas no Recebimento Bancário")
    if df_aud.empty:
        st.success("Nenhuma divergência financeira detectada até o momento.")
    else:
        st.error("Atenção: Foram detectados pagamentos com valor divergente do título original no ERP!")
        
        df_aud_formatado = df_aud.copy()
        df_aud_formatado["diferenca_valor"] = df_aud_formatado["diferenca_valor"].apply(
            lambda valor: ("-" if valor < 0 else "") + formatar_reais(abs(valor))
        )
        
        df_aud_formatado["descricao_auditoria"] = df_aud_formatado["descricao_auditoria"].apply(
            lambda texto: re.sub(
                r"R\$\s*(\d+\.\d{2})",
                lambda m: formatar_reais(float(m.group(1))),
                texto
            )
        )


        st.dataframe(
            df_aud_formatado.rename(columns={
                "id_divergencia": "ID",
                "nosso_numero": "Número do Boleto",
                "tipo_alerta": "Tipo de Ocorrência",
                "diferenca_valor": "Diferença (R$)",
                "descricao_auditoria": "Descrição da Auditoria",
                "criado_em": "Data do Registro"
            }),
            use_container_width=True,
            hide_index=True
        )

st.divider()

# 3. Agente de IA Interativo para o Diretor Financeiro
st.subheader("🤖 Consultar Agente de IA da Controladoria (Consultas Financeiras com IA)")
pergunta = st.text_input(
    "Faça uma pergunta em português sobre o fluxo de caixa, atrasos ou auditoria:",
    value="Quais clientes estão com boletos atrasados e qual o valor de cada um?"
)

if st.button("Consultar Controladoria IA"):
    with st.spinner("O Agente está gerando a consulta SQL, auditando o banco de dados e redigindo o parecer..."):
        sql_gerado = gerar_sql(pergunta)
        dados_reais = executar_sql(sql_gerado)
        
        prompt_parecer = f"""/no_think
Você é um Controller Financeiro Sênior. Responda à pergunta do diretor em Português do Brasil de forma executiva, direta e exata ao centavo, baseando-se EXCLUSIVAMENTE nos dados retornados do banco SQL abaixo. Não invente números.

Pergunta: {pergunta}
Dados oficiais do banco SQLite: {dados_reais}
Parecer Executivo:"""
        resp = requests.post(OLLAMA_URL, json={"model": MODELO, "prompt": prompt_parecer, "stream": False}, timeout=120)
        parecer = limpar_resposta_llm(resp.json().get("response", ""))
        
        st.markdown("### Parecer Executivo do Agente")
        st.info(parecer)
        with st.expander("Ver auditoria técnica (Query SQL executada e dados brutos)"):
            st.code(sql_gerado, language="sql")
            st.json(dados_reais)