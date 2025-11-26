import psycopg2
from config import config

def verify_data_quality():
    conn = psycopg2.connect(config.DATABASE_URL)
    cur = conn.cursor()

    # Count total items
    cur.execute("SELECT COUNT(*) FROM itens_arp")
    total = cur.fetchone()[0]
    print(f"Total items: {total}")

    # Check for NULL values in important fields
    fields_to_check = [
        'codigo_item', 'tipo_item', 'valor_unitario', 'valor_total',
        'quantidade', 'classificacao_fornecedor', 'cnpj_fornecedor',
        'nome_fornecedor', 'situacao_sicaf', 'codigo_pdm', 'nome_pdm',
        'quantidade_empenhada', 'percentual_maior_desconto', 'maximo_adesao'
    ]

    print("\nNULL value counts:")
    for field in fields_to_check:
        cur.execute(f"SELECT COUNT(*) FROM itens_arp WHERE {field} IS NULL")
        null_count = cur.fetchone()[0]
        percentage = (null_count / total * 100) if total > 0 else 0
        print(f"  {field}: {null_count} ({percentage:.1f}%)")

    # Sample records
    print("\nSample records (first 3):")
    cur.execute("""
        SELECT numero_item, codigo_item, tipo_item, valor_unitario, valor_total,
               quantidade, nome_fornecedor, codigo_pdm, nome_pdm
        FROM itens_arp
        LIMIT 3
    """)

    for row in cur.fetchall():
        print(f"\n  Item {row[0]}:")
        print(f"    codigo_item: {row[1]}")
        print(f"    tipo_item: {row[2]}")
        print(f"    valor_unitario: {row[3]}")
        print(f"    valor_total: {row[4]}")
        print(f"    quantidade: {row[5]}")
        print(f"    nome_fornecedor: {row[6]}")
        print(f"    codigo_pdm: {row[7]}")
        print(f"    nome_pdm: {row[8]}")

    conn.close()

if __name__ == "__main__":
    verify_data_quality()
