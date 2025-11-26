# Database Migrations

Este diretório contém os scripts de migração do banco de dados para o AtaHub Carona.

## Migrações Disponíveis

### 001_enhanced_schema.sql

**Data:** 2025-01-26
**Descrição:** Reformulação completa do schema para ETL de produção

**Mudanças principais:**
- ✅ Adiciona campos críticos (numero_compra, timestamps ETL, flags de exclusão)
- ✅ Cria tabelas de tracking (etl_executions, etl_errors)
- ✅ Adiciona índices otimizados para queries de produção
- ✅ Implementa soft deletes (ata_excluido, item_excluido)
- ✅ Adiciona full-text search vectors com pesos

## Como Executar Migração

### Pré-Requisitos

1. **BACKUP OBRIGATÓRIO** antes de executar qualquer migração!

```bash
# Backup completo do banco
pg_dump -U postgres -h localhost -p 5433 -d govcompras > backup_antes_da_migracao_$(date +%Y%m%d_%H%M%S).sql

# Ou via Docker
docker exec -t atahub_carona-db-1 pg_dump -U postgres govcompras > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Método 1: Via psql (Local)

```bash
# Conectar ao banco e executar migration
psql -U postgres -h localhost -p 5433 -d govcompras -f migrations/001_enhanced_schema.sql
```

### Método 2: Via Docker

```bash
# Copiar migration para container
docker cp migrations/001_enhanced_schema.sql atahub_carona-db-1:/tmp/

# Executar migration no container
docker exec -it atahub_carona-db-1 psql -U postgres -d govcompras -f /tmp/001_enhanced_schema.sql
```

### Método 3: Via DBeaver/PgAdmin

1. Abrir arquivo `001_enhanced_schema.sql`
2. Conectar ao banco de dados `govcompras`
3. Executar o script completo

## Verificação Pós-Migração

Após executar a migração, verificar se tudo foi criado corretamente:

```sql
-- 1. Verificar estrutura das tabelas
\d+ arps
\d+ itens_arp
\d+ etl_executions
\d+ etl_errors

-- 2. Verificar índices criados
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('arps', 'itens_arp', 'etl_executions', 'etl_errors')
ORDER BY tablename, indexname;

-- 3. Contar índices por tabela
SELECT tablename, COUNT(*) as num_indexes
FROM pg_indexes
WHERE tablename IN ('arps', 'itens_arp', 'etl_executions', 'etl_errors')
GROUP BY tablename;

-- 4. Verificar triggers
SELECT tgname, tgrelid::regclass, tgenabled
FROM pg_trigger
WHERE tgname LIKE 'update%updated_at';

-- 5. Verificar extensões
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'unaccent');

-- 6. Verificar se há dados (deve estar vazio após migração)
SELECT 'arps' as tabela, COUNT(*) as registros FROM arps
UNION ALL
SELECT 'itens_arp', COUNT(*) FROM itens_arp
UNION ALL
SELECT 'etl_executions', COUNT(*) FROM etl_executions
UNION ALL
SELECT 'etl_errors', COUNT(*) FROM etl_errors;
```

## Esperado Após Migração

### Tabelas Criadas

- ✅ `orgaos` - 5 colunas (enhanced)
- ✅ `arps` - 24 colunas (enhanced) + search_vector
- ✅ `itens_arp` - 24 colunas (enhanced) + search_vector
- ✅ `etl_executions` - 18 colunas (nova)
- ✅ `etl_errors` - 12 colunas (nova)

### Índices Criados

- `arps`: ~13 índices (including GIN for search)
- `itens_arp`: ~12 índices (including GIN for search)
- `etl_executions`: ~4 índices
- `etl_errors`: ~5 índices

### Triggers

- `update_orgaos_updated_at`
- `update_arps_updated_at`
- `update_itens_updated_at`

## Rollback (Emergência)

Se algo der errado, restaurar do backup:

```bash
# Via psql
psql -U postgres -h localhost -p 5433 -d govcompras < backup_YYYY-MM-DD_HHMMSS.sql

# Via Docker
docker exec -i atahub_carona-db-1 psql -U postgres govcompras < backup_YYYY-MM-DD_HHMMSS.sql
```

## Próximos Passos

Após migração bem-sucedida:

1. ✅ Atualizar `backend/models.py` com novos campos
2. ✅ Criar `etl/models.py` com models async
3. ✅ Começar implementação do ETL (Fase 2)

## Troubleshooting

### Erro: "relation already exists"

A tabela já existe. Verifique o schema atual:

```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

Se precisa recriar, **faça backup** e depois:

```sql
DROP TABLE IF EXISTS etl_errors CASCADE;
DROP TABLE IF EXISTS etl_executions CASCADE;
DROP TABLE IF EXISTS itens_arp CASCADE;
DROP TABLE IF EXISTS arps CASCADE;
DROP TABLE IF EXISTS orgaos CASCADE;
```

### Erro: "permission denied"

Verifique permissões do usuário postgres:

```sql
GRANT ALL PRIVILEGES ON DATABASE govcompras TO postgres;
```

### Performance lenta após migração

Execute VACUUM ANALYZE (já incluído no script, mas pode executar novamente):

```sql
VACUUM ANALYZE;
```

## Notas Importantes

⚠️ **NUNCA** execute migrations em produção sem backup
⚠️ **SEMPRE** teste migrations em ambiente de desenvolvimento primeiro
⚠️ Esta migration é **idempotente** (pode ser executada múltiplas vezes com `IF NOT EXISTS`)
⚠️ Dados existentes nas tabelas antigas serão **preservados** se as tabelas já existirem
