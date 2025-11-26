import psycopg2

DB_CONN = "postgresql://postgres:password@localhost:5433/govcompras"

def verify():
    try:
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM arps")
        arps_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM itens_arp")
        items_count = cur.fetchone()[0]

        print(f"ARPs count: {arps_count}")
        print(f"Items count: {items_count}")

        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
