@echo off
REM AtaHub Database Backup Script for Windows
REM Creates a PostgreSQL dump with UTF-8 encoding

SET DB_CONTAINER=atahub_db
SET DB_USER=postgres
SET DB_NAME=govcompras
SET BACKUP_DIR=db_backups
SET TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
SET TIMESTAMP=%TIMESTAMP: =0%
SET BACKUP_FILE=%BACKUP_DIR%\atahub_backup_%TIMESTAMP%.sql
SET LATEST_BACKUP=%BACKUP_DIR%\atahub_backup_latest.sql

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo 🔄 Starting database backup...
echo Database: %DB_NAME%
echo Container: %DB_CONTAINER%

REM Create the dump with UTF-8 encoding
docker exec -t %DB_CONTAINER% pg_dump -U %DB_USER% --encoding=UTF8 --no-owner --no-acl --clean --if-exists %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Backup created successfully: %BACKUP_FILE%

    REM Create a copy as the latest backup
    copy /Y "%BACKUP_FILE%" "%LATEST_BACKUP%" >nul
    echo ✅ Latest backup updated: %LATEST_BACKUP%

    echo ✅ Backup process completed!
) else (
    echo ❌ Backup failed!
    exit /b 1
)
