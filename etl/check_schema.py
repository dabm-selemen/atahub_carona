import psycopg2
from config import config

def check_schema():
    conn = psycopg2.connect(config.DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'itens_arp'
    """)

    columns = cur.fetchall()
    print("Columns in itens_arp:")
    for col in columns:
        print(f"  {col[0]}: {col[1]}")

    conn.close()

if __name__ == "__main__":
    check_schema()
