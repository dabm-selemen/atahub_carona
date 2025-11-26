#!/usr/bin/env python3
"""
Quick script to run database migration
"""
import psycopg2
from config import config

# Parse connection string
db_url = config.DATABASE_URL
# Extract parts from postgresql://user:password@host:port/database
parts = db_url.replace('postgresql://', '').split('@')
user_pass = parts[0].split(':')
host_port_db = parts[1].split('/')
host_port = host_port_db[0].split(':')

user = user_pass[0]
password = user_pass[1] if len(user_pass) > 1 else ''
host = host_port[0]
port = host_port[1] if len(host_port) > 1 else '5432'
database = host_port_db[1]

print(f"Connecting to: {host}:{port}/{database}")

# Read migration file
with open('../migrations/001_enhanced_schema.sql', 'r', encoding='utf-8') as f:
    migration_sql = f.read()

# Connect and execute
try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    conn.autocommit = True

    cursor = conn.cursor()

    # Drop existing tables first (for clean migration)
    print("Dropping existing tables...")
    drop_sql = """
    DROP TABLE IF EXISTS etl_errors CASCADE;
    DROP TABLE IF EXISTS etl_executions CASCADE;
    DROP TABLE IF EXISTS itens_arp CASCADE;
    DROP TABLE IF EXISTS arps CASCADE;
    DROP TABLE IF EXISTS orgaos CASCADE;
    """
    cursor.execute(drop_sql)
    print("Existing tables dropped.")

    print("Executing migration (without VACUUM)...")

    # Remove VACUUM commands from migration (will execute separately)
    migration_without_vacuum = '\n'.join([
        line for line in migration_sql.split('\n')
        if 'VACUUM' not in line.upper()
    ])

    cursor.execute(migration_without_vacuum)
    conn.commit()
    print("Main migration executed.")

    # Execute VACUUM commands separately (already in autocommit mode)
    print("Executing VACUUM commands...")
    vacuum_commands = [
        "VACUUM ANALYZE orgaos",
        "VACUUM ANALYZE arps",
        "VACUUM ANALYZE itens_arp",
        "VACUUM ANALYZE etl_executions",
        "VACUUM ANALYZE etl_errors"
    ]

    for vcmd in vacuum_commands:
        try:
            cursor.execute(vcmd)
            print(f"  {vcmd}")
        except Exception as e:
            print(f"  Warning: {vcmd} - {str(e)[:100]}")

    print("Migration completed successfully!")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Migration failed: {e}")
    raise
