@echo off
REM AtaHub Database Restore Script for Windows
REM Restores the PostgreSQL database from a dump file

SET DB_CONTAINER=atahub_db
SET DB_USER=postgres
SET DB_NAME=govcompras

REM Use provided file or default to latest backup
if "%~1"=="" (
    SET BACKUP_FILE=db_backups\atahub_backup_latest.sql
) else (
    SET BACKUP_FILE=%~1
)

REM Check if backup file exists
if not exist "%BACKUP_FILE%" (
    echo ❌ Error: Backup file not found: %BACKUP_FILE%
    echo Usage: restore_db.bat [backup_file]
    echo Example: restore_db.bat db_backups\atahub_backup_latest.sql
    exit /b 1
)

echo 🔄 Starting database restore...
echo Database: %DB_NAME%
echo Container: %DB_CONTAINER%
echo Backup file: %BACKUP_FILE%

REM Warning prompt
set /p confirm="⚠️  This will overwrite the current database. Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ Restore cancelled.
    exit /b 1
)

REM Restore the database
docker exec -i %DB_CONTAINER% psql -U %DB_USER% -d %DB_NAME% < "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Database restored successfully!
    echo ✅ Restore process completed!
) else (
    echo ❌ Restore failed!
    exit /b 1
)
