#!/bin/bash

# AtaHub Database Restore Script
# Restores the PostgreSQL database from a dump file

# Configuration
DB_CONTAINER="atahub_db"
DB_USER="postgres"
DB_NAME="govcompras"
BACKUP_FILE="${1:-./db_backups/atahub_backup_latest.sql}"

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Error: Backup file not found: ${BACKUP_FILE}"
    echo "Usage: ./restore_db.sh [backup_file]"
    echo "Example: ./restore_db.sh ./db_backups/atahub_backup_latest.sql"
    exit 1
fi

echo "🔄 Starting database restore..."
echo "Database: ${DB_NAME}"
echo "Container: ${DB_CONTAINER}"
echo "Backup file: ${BACKUP_FILE}"

# Warning prompt
read -p "⚠️  This will overwrite the current database. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled."
    exit 1
fi

# Restore the database
docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${BACKUP_FILE}"

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully!"
else
    echo "❌ Restore failed!"
    exit 1
fi

echo "✅ Restore process completed!"
