# AtaHub Database Scripts

Este diretório contém scripts para backup e restauração do banco de dados PostgreSQL do AtaHub.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Container `atahub_db` em execução

## 🔧 Scripts Disponíveis

### Backup do Banco de Dados

Cria um dump completo do banco de dados com codificação UTF-8.

**Linux/Mac:**
```bash
chmod +x scripts/backup_db.sh
./scripts/backup_db.sh
```

**Windows:**
```cmd
scripts\backup_db.bat
```

O backup será salvo em:
- `db_backups/atahub_backup_YYYYMMDD_HHMMSS.sql` (com timestamp)
- `db_backups/atahub_backup_latest.sql` (sempre o backup mais recente)

### Restauração do Banco de Dados

Restaura o banco de dados a partir de um arquivo de dump.

**Linux/Mac:**
```bash
chmod +x scripts/restore_db.sh

# Restaurar do backup mais recente
./scripts/restore_db.sh

# Restaurar de um backup específico
./scripts/restore_db.sh ./db_backups/atahub_backup_20251126_152300.sql
```

**Windows:**
```cmd
# Restaurar do backup mais recente
scripts\restore_db.bat

# Restaurar de um backup específico
scripts\restore_db.bat db_backups\atahub_backup_20251126_152300.sql
```

⚠️ **Atenção:** A restauração irá sobrescrever todos os dados existentes no banco de dados!

## 📝 Workflow Recomendado

### Ao trabalhar em uma nova máquina:

1. Clone o repositório
   ```bash
   git clone <repository-url>
   cd atahub_carona
   ```

2. Inicie os containers Docker
   ```bash
   docker-compose up -d
   ```

3. Aguarde o banco de dados estar pronto (cerca de 10 segundos)

4. Restaure o banco de dados
   ```bash
   # Linux/Mac
   ./scripts/restore_db.sh

   # Windows
   scripts\restore_db.bat
   ```

### Antes de commitar alterações no banco:

1. Crie um backup atualizado
   ```bash
   # Linux/Mac
   ./scripts/backup_db.sh

   # Windows
   scripts\backup_db.bat
   ```

2. Adicione o backup ao Git (apenas o latest)
   ```bash
   git add db_backups/atahub_backup_latest.sql
   git commit -m "chore: update database backup"
   git push
   ```

## 📂 Estrutura de Arquivos

```
scripts/
├── backup_db.sh       # Script de backup para Linux/Mac
├── backup_db.bat      # Script de backup para Windows
├── restore_db.sh      # Script de restauração para Linux/Mac
├── restore_db.bat     # Script de restauração para Windows
└── README.md          # Esta documentação

db_backups/
├── atahub_backup_latest.sql           # Backup mais recente (commitado no Git)
└── atahub_backup_YYYYMMDD_HHMMSS.sql  # Backups com timestamp (não commitados)
```

## 🔐 Segurança

- Os backups NÃO contêm senhas de usuários do PostgreSQL (`--no-acl`)
- Os backups NÃO contêm informações de ownership (`--no-owner`)
- Certifique-se de não commitar dados sensíveis ao Git
- O arquivo `.gitignore` está configurado para ignorar backups timestampados

## 🛠️ Opções Avançadas

### Criar backup manual com pg_dump

```bash
docker exec -t atahub_db pg_dump -U postgres \
  --encoding=UTF8 \
  --no-owner \
  --no-acl \
  --clean \
  --if-exists \
  govcompras > custom_backup.sql
```

### Restaurar backup manual

```bash
docker exec -i atahub_db psql -U postgres -d govcompras < custom_backup.sql
```

## ❓ Troubleshooting

### Erro: "Container not found"
Certifique-se de que os containers estão em execução:
```bash
docker-compose up -d
docker ps
```

### Erro: "Permission denied"
No Linux/Mac, dê permissão de execução aos scripts:
```bash
chmod +x scripts/*.sh
```

### Erro durante a restauração
1. Verifique se o arquivo de backup existe
2. Certifique-se de que o banco de dados está rodando
3. Verifique os logs: `docker logs atahub_db`
