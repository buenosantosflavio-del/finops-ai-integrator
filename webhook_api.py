from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from datetime import datetime
import json
from database import get_connection, inicializar_banco

inicializar_banco()

app = FastAPI(
    title="FinOps AI Integrator - API Bancária & ERP",
    description="Motor de conciliação automática (Webhook Bancário / DDA <-> ERP) com controle de idempotência e auditoria.",
    version="1.0.0"
)

class WebhookBaixaBoleto(BaseModel):
    id_evento_banco: str = Field(..., example="EVT-ITAU-998877")
    nosso_numero: str = Field(..., example="ITAU-1001")
    valor_pago: float = Field(..., gt=0, example=1500.00)
    data_pagamento: str = Field(..., example="2026-10-30 16:45:00")

class ItemDDA(BaseModel):
    cnpj_fornecedor: str = Field(..., example="23.456.789/0001-12")
    linha_digitavel: str = Field(..., example="34191.00009 00000.000001 00000.000002 1 95000000310000")
    valor_boleto_banco: float = Field(..., gt=0, example=3100.00)

@app.get("/erp/resumo-caixa", summary="Consulta o estado atual do ERP e divergências")
def consultar_caixa():
    conn = get_connection()
    lancamentos = [dict(row) for row in conn.execute("SELECT * FROM lancamentos_erp").fetchall()]
    divergencias = [dict(row) for row in conn.execute("SELECT * FROM divergencias_auditoria").fetchall()]
    conn.close()
    return {
        "total_lancamentos": len(lancamentos),
        "lancamentos": lancamentos,
        "alertas_controladoria": divergencias
    }

@app.post("/webhook/itau/baixa-boleto", summary="Recebe Webhook bancário e dá baixa automática no ERP")
def receber_webhook_itau(
    payload: WebhookBaixaBoleto,
    x_itau_signature: str = Header(default="assinatura-homologacao-valida")
):
    conn = get_connection()
    cursor = conn.cursor()

    ja_processado = cursor.execute(
        "SELECT id_evento FROM eventos_webhook_banco WHERE id_evento = ?",
        (payload.id_evento_banco,)
    ).fetchone()
    if ja_processado:
        conn.close()
        return {"status": "IGNORADO_IDEMPOTENTE", "mensagem": f"Evento {payload.id_evento_banco} já processado."}

    boleto = cursor.execute(
        "SELECT * FROM lancamentos_erp WHERE nosso_numero = ? AND tipo = 'RECEBER'",
        (payload.nosso_numero,)
    ).fetchone()
    if not boleto:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Boleto {payload.nosso_numero} não localizado.")

    valor_original = boleto["valor_original"]
    diferenca = round(payload.valor_pago - valor_original, 2)
    novo_status = "PAGO"
    alerta_gerado = None

    if diferenca < 0:
        novo_status = "DIVERGENTE"
        alerta_gerado = f"Pagamento a menor detectado. Original: R$ {valor_original:.2f} | Pago: R$ {payload.valor_pago:.2f}"
        cursor.execute("""
            INSERT INTO divergencias_auditoria (nosso_numero, tipo_alerta, diferenca_valor, descricao_auditoria, criado_em)
            VALUES (?, 'PAGAMENTO_A_MENOR', ?, ?, ?)
        """, (payload.nosso_numero, diferenca, alerta_gerado, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    elif diferenca > 0:
        alerta_gerado = f"Boleto pago com acréscimo (juros/multa) de R$ {diferenca:.2f}."
        cursor.execute("""
            INSERT INTO divergencias_auditoria (nosso_numero, tipo_alerta, diferenca_valor, descricao_auditoria, criado_em)
            VALUES (?, 'JUROS_ATRASO', ?, ?, ?)
        """, (payload.nosso_numero, diferenca, alerta_gerado, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("""
        UPDATE lancamentos_erp 
        SET valor_pago = ?, status = ?, data_baixa = ?
        WHERE nosso_numero = ?
    """, (payload.valor_pago, novo_status, payload.data_pagamento, payload.nosso_numero))

    cursor.execute("""
        INSERT INTO eventos_webhook_banco (id_evento, nosso_numero, valor_recebido, data_ocorrencia, payload_bruto, processado_em)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        payload.id_evento_banco, payload.nosso_numero, payload.valor_pago,
        payload.data_pagamento, json.dumps(payload.model_dump()), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return {
        "status_integracao": "SUCESSO",
        "nosso_numero": payload.nosso_numero,
        "cliente": boleto["cliente_fornecedor"],
        "status_erp_atualizado": novo_status,
        "auditoria": alerta_gerado or "Conciliação exata ao centavo."
    }

@app.post("/erp/sincronizar-lote-dda", summary="Concilia varredura DDA com Contas a Pagar do ERP")
def sincronizar_lote_dda(lote: list[ItemDDA]):
    conn = get_connection()
    cursor = conn.cursor()
    relatorio_lote = []

    for item in lote:
        conta = cursor.execute("""
            SELECT * FROM lancamentos_erp 
            WHERE tipo = 'PAGAR' AND cnpj = ? AND linha_digitavel = ?
        """, (item.cnpj_fornecedor, item.linha_digitavel)).fetchone()

        if not conta:
            relatorio_lote.append({"linha_digitavel": item.linha_digitavel, "resultado": "REJEITADO_SEM_LASTRO_NO_ERP"})
            continue

        if round(item.valor_boleto_banco, 2) != round(conta["valor_original"], 2):
            dif = round(item.valor_boleto_banco - conta["valor_original"], 2)
            cursor.execute("""
                INSERT INTO divergencias_auditoria (nosso_numero, tipo_alerta, diferenca_valor, descricao_auditoria, criado_em)
                VALUES (?, 'DIVERGENCIA_DDA', ?, ?, ?)
            """, (conta["nosso_numero"], dif, f"Valor no DDA (R$ {item.valor_boleto_banco}) diverge do ERP (R$ {conta['valor_original']})", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            relatorio_lote.append({"fornecedor": conta["cliente_fornecedor"], "resultado": "BLOQUEADO_DIVERGENCIA_VALOR"})
        else:
            cursor.execute("UPDATE lancamentos_erp SET status = 'AGENDADO_DDA' WHERE id_lancamento = ?", (conta["id_lancamento"],))
            relatorio_lote.append({"fornecedor": conta["cliente_fornecedor"], "valor": item.valor_boleto_banco, "resultado": "APROVADO_LOTE_PAGAMENTO"})

    conn.commit()
    conn.close()
    return {"processados": len(lote), "detalhes": relatorio_lote}