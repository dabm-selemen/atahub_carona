#!/usr/bin/env python3
"""Quick script to verify database contents"""
import psycopg2
from config import config

# Parse connection string
db_url = config.DATABASE_URL
parts = db_url.replace('postgresql://', '').split('@')
user_pass = parts[0].split(':')
host_port_db = parts[1].split('/')
host_port = host_port_db[0].split(':')

user = user_pass[0]
password = user_pass[1] if len(user_pass) > 1 else ''
host = host_port[0]
port = host_port[1] if len(host_port) > 1 else '5432'
database = host_port_db[1]

# Connect
conn = psycopg2.connect(
    host=host,
    port=port,
    database=database,
    user=user,
    password=password
)

cur = conn.cursor()

# Query data
cur.execute('SELECT COUNT(*) FROM arps')
total_arps = cur.fetchone()[0]

cur.execute(
    'SELECT COUNT(*) FROM arps WHERE data_atualizacao_pncp >= %s AND data_atualizacao_pncp < %s',
    ('2025-11-01', '2025-12-01')
)
nov_arps = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM orgaos')
total_orgaos = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM itens_arp')
total_itens = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM etl_executions')
executions = cur.fetchone()[0]

cur.execute('''
    SELECT id, execution_type, status, started_at, arps_fetched, arps_inserted, errors_count
    FROM etl_executions
    ORDER BY started_at DESC
    LIMIT 1
''')
last_exec = cur.fetchone()

# Display results
print('=' * 70)
print('BANCO DE DADOS: postgresql://postgres:***@localhost:5433/govcompras')
print('=' * 70)
print(f'\nTabela ARPs:')
print(f'  Total de ARPs no banco: {total_arps:,}')
print(f'  ARPs de Novembro/2025: {nov_arps:,}')
print(f'\nTabela Orgaos:')
print(f'  Total de Orgaos: {total_orgaos:,}')
print(f'\nTabela Itens ARP:')
print(f'  Total de Itens: {total_itens:,}')
print(f'\nTabela ETL Executions:')
print(f'  Total de Execucoes: {executions}')

if last_exec:
    print(f'\nUltima Execucao ETL:')
    print(f'  ID: {last_exec[0]}')
    print(f'  Tipo: {last_exec[1]}')
    print(f'  Status: {last_exec[2]}')
    print(f'  Iniciado em: {last_exec[3]}')
    print(f'  ARPs Buscados: {last_exec[4]:,}')
    print(f'  ARPs Inseridos: {last_exec[5]:,}')
    print(f'  Erros: {last_exec[6]}')

# Sample records
print(f'\nAmostra de ARPs (5 registros):')
cur.execute('''
    SELECT numero_arp, nome_orgao, data_inicio_vigencia, valor_total
    FROM arps
    ORDER BY created_at DESC
    LIMIT 5
''')
for row in cur.fetchall():
    print(f'  - ARP {row[0]}: {row[1][:50]}... | Vigencia: {row[2]} | Valor: R$ {row[3]:,.2f}')

print('=' * 70)

cur.close()
conn.close()
