#!/bin/bash

# AtaHub Database Backup Script
# Creates a PostgreSQL dump with UTF-8 encoding

# Configuration
DB_CONTAINER="atahub_db"
DB_USER="postgres"
DB_NAME="govcompras"
BACKUP_DIR="./db_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/atahub_backup_${TIMESTAMP}.sql"
LATEST_BACKUP="${BACKUP_DIR}/atahub_backup_latest.sql"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "🔄 Starting database backup..."
echo "Database: ${DB_NAME}"
echo "Container: ${DB_CONTAINER}"

# Create the dump with UTF-8 encoding
docker exec -t "${DB_CONTAINER}" pg_dump -U "${DB_USER}" \
  --encoding=UTF8 \
  --no-owner \
  --no-acl \
  --clean \
  --if-exists \
  "${DB_NAME}" > "${BACKUP_FILE}"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully: ${BACKUP_FILE}"

    # Create a copy as the latest backup
    cp "${BACKUP_FILE}" "${LATEST_BACKUP}"
    echo "✅ Latest backup updated: ${LATEST_BACKUP}"

    # Display backup size
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "📊 Backup size: ${BACKUP_SIZE}"
else
    echo "❌ Backup failed!"
    exit 1
fi

echo "✅ Backup process completed!"
