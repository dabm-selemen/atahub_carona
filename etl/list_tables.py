#!/usr/bin/env python3
"""List all tables in database"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5433',
    database='govcompras',
    user='postgres',
    password='password'
)

cur = conn.cursor()

# List all tables
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name
""")
tables = cur.fetchall()

print('=' * 70)
print('TABELAS NO BANCO DE DADOS')
print('=' * 70)
print(f'Banco: govcompras')
print(f'Host: localhost:5433')
print(f'Usuario: postgres')
print()

if tables:
    print(f'Total de tabelas: {len(tables)}\n')
    for schema, table in tables:
        print(f'  {schema}.{table}')

        # Count records
        try:
            cur.execute(f'SELECT COUNT(*) FROM {schema}.{table}')
            count = cur.fetchone()[0]
            print(f'    -> {count:,} registros')
        except Exception as e:
            print(f'    -> Erro ao contar: {str(e)[:50]}')
else:
    print('NENHUMA TABELA ENCONTRADA!')
    print()
    print('Verificando schemas disponiveis...')
    cur.execute("SELECT schema_name FROM information_schema.schemata")
    schemas = cur.fetchall()
    print('Schemas:')
    for s in schemas:
        print(f'  - {s[0]}')

print('=' * 70)

cur.close()
conn.close()
