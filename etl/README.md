# AtaHub Carona - ETL System

Sistema completo de ETL (Extract, Transform, Load) para ingestão de dados de Atas de Registro de Preços (ARP) da API de Dados Abertos do Governo Federal.

## 🚀 Características

- ✅ **Processamento Assíncrono** - asyncio/aiohttp para alta performance
- ✅ **Rate Limiting Inteligente** - Token bucket com 3 req/s + exponential backoff
- ✅ **ETL Incremental** - Atualizações diárias com lookback window de 7 dias
- ✅ **Checkpoint/Resume** - Recuperação automática de falhas
- ✅ **Soft Deletes** - Preserva histórico de dados excluídos
- ✅ **Full-Text Search** - Busca eficiente em PostgreSQL com índices GIN
- ✅ **Monitoramento** - Tracking de execuções, erros e estatísticas
- ✅ **Docker Ready** - Containerizado com Docker Compose
- ✅ **Scheduler Integrado** - APScheduler para execução automática diária

## 📋 Pré-Requisitos

- Python 3.11+
- PostgreSQL 15+
- Docker e Docker Compose (opcional)

## 🛠️ Instalação

### 1. Instalar Dependências

```bash
cd etl
pip install -r requirements.txt
```

### 2. Configurar Ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

Edite `.env` com suas configurações:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5433/govcompras
API_BASE_URL=https://dadosabertos.compras.gov.br
REQUESTS_PER_SECOND=3.0
INITIAL_LOAD_START_DATE=2023-01-01
```

### 3. Executar Migration do Banco

**IMPORTANTE:** Faça backup antes!

```bash
# Via psql
psql -U postgres -h localhost -p 5433 -d govcompras -f ../migrations/001_enhanced_schema.sql

# Via Docker
docker cp ../migrations/001_enhanced_schema.sql atahub_db:/tmp/
docker exec -it atahub_db psql -U postgres -d govcompras -f /tmp/001_enhanced_schema.sql
```

Consulte `../migrations/README.md` para mais detalhes.

## 🎯 Uso

### Modo 1: CLI (Linha de Comando)

#### Carga Inicial

Processa dados dos últimos 2-3 anos:

```bash
# Período padrão (configurado no .env)
python run_initial_load.py

# Período personalizado
python run_initial_load.py --start 2023-01-01 --end 2024-12-31

# Modo de teste (páginas limitadas)
python run_initial_load.py --test

# Dry run (não salva no banco)
python run_initial_load.py --dry-run
```

#### Atualização Incremental

Busca mudanças desde a última sincronização:

```bash
python run_incremental.py
```

### Modo 2: Scheduler Automático

Executa atualizações incrementais diariamente às 2 AM:

```bash
python scheduler.py
```

Configuração no `.env`:

```bash
ETL_SCHEDULE_ENABLED=true
ETL_SCHEDULE_HOUR=2
ETL_SCHEDULE_MINUTE=0
ETL_SCHEDULE_TIMEZONE=America/Sao_Paulo
```

### Modo 3: Docker Compose

Inicia todo o stack incluindo ETL scheduler:

```bash
# Subir todos os serviços
docker-compose up -d

# Ver logs do ETL
docker-compose logs -f etl

# Executar carga inicial manualmente
docker-compose exec etl python run_initial_load.py

# Executar incremental manualmente
docker-compose exec etl python run_incremental.py
```

## 📊 Monitoramento

### Endpoints Admin API

O backend FastAPI expõe endpoints para monitoramento:

#### Status Atual

```bash
curl http://localhost:8000/admin/etl/status
```

Resposta:
```json
{
  "execution_id": "uuid",
  "status": "running",
  "progress": "15/282",
  "arps_processed": 7500,
  "items_processed": 45000,
  "errors": 12,
  "duration_seconds": 3600,
  "started_at": "2025-01-26T02:00:00"
}
```

#### Histórico de Execuções

```bash
curl http://localhost:8000/admin/etl/executions?limit=10
```

#### Erros do ETL

```bash
curl http://localhost:8000/admin/etl/errors?limit=50
```

#### Estatísticas Gerais

```bash
curl http://localhost:8000/admin/etl/stats
```

Resposta:
```json
{
  "arps": {
    "total": 140000,
    "active": 138500,
    "valid": 95000
  },
  "items": {
    "total": 1250000,
    "active": 1230000
  },
  "executions": {
    "total": 45,
    "completed": 43,
    "failed": 2
  }
}
```

### Logs

Logs são salvos em `logs/etl.log` (configurável):

```bash
# Ver logs em tempo real
tail -f logs/etl.log

# Buscar erros
grep "error" logs/etl.log
```

### Queries de Monitoramento

```sql
-- Status da última execução
SELECT * FROM etl_executions
ORDER BY started_at DESC LIMIT 1;

-- Erros não resolvidos
SELECT * FROM etl_errors
WHERE resolved = FALSE;

-- Estatísticas de ARPs
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE ata_excluido = FALSE) as ativas,
    COUNT(*) FILTER (WHERE data_fim_vigencia >= CURRENT_DATE) as vigentes
FROM arps;
```

## 🏗️ Arquitetura

```
etl/
├── config.py              # Configuração centralizada (Pydantic)
├── database.py            # Database async (asyncpg + SQLAlchemy)
├── models.py              # ORM models
├── api_client.py          # Cliente HTTP async com rate limiting
├── orchestrator.py        # Coordenador principal do ETL
│
├── processors/            # Processadores de dados
│   ├── transformers.py    # Mapeamento API → DB
│   ├── arp_processor.py   # Processador de ARPs
│   └── item_processor.py  # Processador de itens
│
├── utils/                 # Utilitários
│   ├── retry_utils.py     # Retry com backoff
│   └── date_utils.py      # Manipulação de datas
│
├── run_initial_load.py    # CLI: carga inicial
├── run_incremental.py     # CLI: incremental
├── scheduler.py           # Scheduler (APScheduler)
└── Dockerfile             # Container ETL
```

## ⚙️ Configurações Importantes

### Rate Limiting

```bash
REQUESTS_PER_SECOND=3.0  # Conservador para API governamental
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2.0
```

### Batch Sizes

```bash
PAGE_SIZE=500                    # Máximo permitido pela API
BATCH_SIZE_ARPS=100             # ARPs por transação
BATCH_SIZE_ITEMS=500            # Itens por bulk insert
MAX_CONCURRENT_ITEM_REQUESTS=5  # Requests simultâneos
```

### Datas

```bash
INITIAL_LOAD_START_DATE=2023-01-01
INCREMENTAL_LOOKBACK_DAYS=7  # Captura atualizações tardias
```

## 📈 Performance

### Estimativas (2-3 anos de dados)

- **ARPs:** ~140.000 registros
- **Itens:** ~1-3 milhões (10-20 itens/ARP)
- **Tempo Carga Inicial:** 24-48 horas
- **Tempo Incremental Diário:** 5-30 minutos
- **Espaço em Disco:** ~50-100 GB

### Otimizações

- Processamento assíncrono (~70% mais rápido que síncrono)
- Bulk inserts (100x mais rápido que individual)
- Índices GIN para full-text search
- Connection pooling (5 conexões + 10 overflow)
- Checkpoint a cada 10 páginas

## 🐛 Troubleshooting

### Erro: "permission denied"

```bash
# Verificar permissões no PostgreSQL
psql -U postgres -d govcompras -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;"
```

### Erro: "rate limited" (429)

Aguarde ou reduza `REQUESTS_PER_SECOND` no `.env`:

```bash
REQUESTS_PER_SECOND=2.0  # Mais conservador
```

### ETL travou/crashou

O sistema possui checkpoint/resume automático. Basta reiniciar:

```bash
python run_incremental.py
```

### Banco de dados lento após carga

Execute VACUUM ANALYZE:

```sql
VACUUM ANALYZE arps;
VACUUM ANALYZE itens_arp;
```

### Ver progresso em tempo real

```bash
# Terminal 1: Logs
tail -f logs/etl.log

# Terminal 2: Status via API
watch -n 5 'curl -s http://localhost:8000/admin/etl/status | jq'

# Terminal 3: Contagem no banco
watch -n 10 'psql -U postgres -d govcompras -c "SELECT COUNT(*) FROM arps;"'
```

## 🔒 Segurança

- **Rate Limiting:** Protege contra sobrecarga da API governamental
- **Soft Deletes:** Preserva histórico, não permite perda de dados
- **Validação de Dados:** Valida antes de inserir no banco
- **Transações Atômicas:** Rollback automático em erros
- **Error Tracking:** Dead letter queue para retry posterior

## 📝 Manutenção

### Rotinas Recomendadas

**Semanal:**
- Verificar erros não resolvidos
- Revisar logs para anomalias

**Mensal:**
- VACUUM ANALYZE nas tabelas grandes
- Revisar performance de queries
- Limpar logs antigos

**Trimestral:**
- Analisar query plans
- Ajustar índices se necessário
- Revisar configurações de rate limiting

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto faz parte do AtaHub Carona.

## 🆘 Suporte

Para problemas ou dúvidas:

1. Verifique os logs: `logs/etl.log`
2. Consulte o troubleshooting acima
3. Verifique status via API: `/admin/etl/status`
4. Abra uma issue no repositório

---

**Desenvolvido com ❤️ para facilitar o acesso a dados de compras governamentais**
