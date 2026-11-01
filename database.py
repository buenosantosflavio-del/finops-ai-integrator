import sqlite3
from datetime import datetime

DB_NAME = "controladoria.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lancamentos_erp (
        id_lancamento INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        cliente_fornecedor TEXT NOT NULL,
        cnpj TEXT NOT NULL,
        nosso_numero TEXT UNIQUE NOT NULL,
        linha_digitavel TEXT NOT NULL,
        valor_original REAL NOT NULL,
        valor_pago REAL DEFAULT 0.0,
        data_vencimento TEXT NOT NULL,
        status TEXT NOT NULL,
        data_baixa TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eventos_webhook_banco (
        id_evento TEXT PRIMARY KEY,
        nosso_numero TEXT NOT NULL,
        valor_recebido REAL NOT NULL,
        data_ocorrencia TEXT NOT NULL,
        payload_bruto TEXT NOT NULL,
        processado_em TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS divergencias_auditoria (
        id_divergencia INTEGER PRIMARY KEY AUTOINCREMENT,
        nosso_numero TEXT NOT NULL,
        tipo_alerta TEXT NOT NULL,
        diferenca_valor REAL NOT NULL,
        descricao_auditoria TEXT NOT NULL,
        criado_em TEXT NOT NULL
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM lancamentos_erp")
    if cursor.fetchone()[0] == 0:
        dados_iniciais = [
            ("RECEBER", "TechCorp Soluções Ltda", "12.345.678/0001-90", "ITAU-1001", "34191.79001 01043.510047 91020.150008 1 95000000150000", 1500.00, 0.0, "2026-10-30", "PENDENTE", None),
            ("RECEBER", "Comércio Varejista Silva", "98.765.432/0001-10", "ITAU-1002", "34191.79001 01043.510047 91020.150008 1 95000000280000", 2800.00, 0.0, "2026-10-15", "ATRASADO", None),
            ("RECEBER", "Consultoria Horizonte S/A", "45.111.222/0001-55", "ITAU-1003", "34191.79001 01043.510047 91020.150008 1 95000000420000", 4200.00, 4200.00, "2026-10-10", "PAGO", "2026-10-10 14:22:00"),
            ("RECEBER", "Logística Rápida MG", "33.444.555/0001-09", "ITAU-1004", "34191.79001 01043.510047 91020.150008 1 95000000095000", 950.00, 0.0, "2026-10-20", "ATRASADO", None),
            ("PAGAR", "AWS Cloud Brasil", "23.456.789/0001-12", "DDA-5001", "34191.00009 00000.000001 00000.000002 1 95000000310000", 3100.00, 0.0, "2026-11-05", "PENDENTE", None),
            ("PAGAR", "Companhia Energética", "11.222.333/0001-44", "DDA-5002", "34191.00009 00000.000001 00000.000003 1 95000000064050", 640.50, 0.0, "2026-11-02", "PENDENTE", None),
        ]
        cursor.executemany("""
        INSERT INTO lancamentos_erp 
        (tipo, cliente_fornecedor, cnpj, nosso_numero, linha_digitavel, valor_original, valor_pago, data_vencimento, status, data_baixa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dados_iniciais)
        conn.commit()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Banco '{DB_NAME}' inicializado com 6 lançamentos.")

    conn.close()

if __name__ == "__main__":
    inicializar_banco()