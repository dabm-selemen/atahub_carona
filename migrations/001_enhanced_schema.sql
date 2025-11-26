-- AtaHub Carona - Enhanced ARP ETL Schema
-- Migration: 001_enhanced_schema.sql
-- Purpose: Complete reformulation of database schema for production-ready ARP ETL
-- Date: 2025-01-26

-- ============================================================================
-- BACKUP REMINDER
-- ============================================================================
-- CRITICAL: Before running this migration, backup your database!
-- pg_dump -U postgres -d govcompras > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql

-- ============================================================================
-- DROP EXISTING TABLES (Development Only)
-- ============================================================================
-- WARNING: Uncomment only in development environment
-- DROP TABLE IF EXISTS etl_errors CASCADE;
-- DROP TABLE IF EXISTS etl_executions CASCADE;
-- DROP TABLE IF EXISTS itens_arp CASCADE;
-- DROP TABLE IF EXISTS arps CASCADE;
-- DROP TABLE IF EXISTS orgaos CASCADE;

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
-- Ensure required PostgreSQL extensions are enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- ============================================================================
-- TABLE: orgaos (Enhanced)
-- ============================================================================
-- Government agencies/organizations
CREATE TABLE IF NOT EXISTS orgaos (
    uasg VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(500),
    uf VARCHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE orgaos IS 'Government agencies and organizations';
COMMENT ON COLUMN orgaos.uasg IS 'UASG code - Unique government agency identifier';
COMMENT ON COLUMN orgaos.nome IS 'Agency name';
COMMENT ON COLUMN orgaos.uf IS 'Brazilian state code (UF)';

-- ============================================================================
-- TABLE: arps (Enhanced - Price Registration Records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS arps (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_arp_api VARCHAR(100) UNIQUE NOT NULL,
    numero_arp VARCHAR(50),
    numero_compra VARCHAR(50) NOT NULL,  -- CRITICAL: needed for item queries!
    ano_compra INTEGER,

    -- Organization reference
    uasg_id VARCHAR(10) REFERENCES orgaos(uasg),

    -- Dates
    data_inicio_vigencia DATE,
    data_fim_vigencia DATE,
    data_assinatura DATE,
    data_atualizacao_pncp TIMESTAMP,

    -- Content
    objeto TEXT,

    -- Financial
    valor_total NUMERIC(15, 2),
    quantidade_itens INTEGER,

    -- Status and classification
    situacao VARCHAR(50),
    modalidade VARCHAR(100),
    nome_modalidade VARCHAR(200),

    -- PNCP Links and identifiers
    numero_controle_pncp_compra VARCHAR(100),
    numero_controle_pncp_ata VARCHAR(100),
    link_ata_pncp TEXT,
    link_compra_pncp TEXT,
    id_compra VARCHAR(50),

    -- Additional metadata
    codigo_orgao VARCHAR(20),
    nome_orgao VARCHAR(500),

    -- Soft delete flag
    ata_excluido BOOLEAN DEFAULT FALSE,

    -- ETL tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,

    -- Full-text search (generated column)
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('portuguese', coalesce(numero_arp, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(objeto, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(nome_orgao, '')), 'C')
    ) STORED
);

COMMENT ON TABLE arps IS 'Atas de Registro de Preços (Price Registration Records)';
COMMENT ON COLUMN arps.codigo_arp_api IS 'Unique API identifier for ARP (numeroControlePncpAta)';
COMMENT ON COLUMN arps.numero_compra IS 'CRITICAL: Purchase number needed to fetch items from API';
COMMENT ON COLUMN arps.ata_excluido IS 'Soft delete flag - TRUE if ARP was deleted/excluded';
COMMENT ON COLUMN arps.last_synced_at IS 'Timestamp of last sync with API - used for incremental updates';
COMMENT ON COLUMN arps.search_vector IS 'Full-text search vector for efficient Portuguese text search';

-- ============================================================================
-- TABLE: itens_arp (Enhanced - ARP Items)
-- ============================================================================
CREATE TABLE IF NOT EXISTS itens_arp (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arp_id UUID REFERENCES arps(id) ON DELETE CASCADE,
    numero_item INTEGER,
    codigo_item VARCHAR(50),

    -- Description
    descricao TEXT,
    tipo_item VARCHAR(50),

    -- Pricing and quantity
    valor_unitario NUMERIC(15, 4),
    valor_total NUMERIC(15, 2),
    quantidade NUMERIC(15, 4),
    unidade VARCHAR(20),

    -- Product details
    marca VARCHAR(200),
    modelo VARCHAR(200),

    -- Supplier information
    classificacao_fornecedor VARCHAR(20),
    cnpj_fornecedor VARCHAR(20),
    nome_fornecedor VARCHAR(500),
    situacao_sicaf VARCHAR(50),

    -- Classification
    codigo_pdm INTEGER,
    nome_pdm VARCHAR(500),

    -- Additional metrics
    quantidade_empenhada NUMERIC(15, 4),
    percentual_maior_desconto NUMERIC(5, 2),
    maximo_adesao NUMERIC(15, 2),

    -- Soft delete flag
    item_excluido BOOLEAN DEFAULT FALSE,

    -- ETL tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,

    -- Full-text search (generated column)
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('portuguese', coalesce(descricao, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(marca, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(modelo, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(nome_fornecedor, '')), 'C')
    ) STORED
);

COMMENT ON TABLE itens_arp IS 'Items within Price Registration Records';
COMMENT ON COLUMN itens_arp.arp_id IS 'Foreign key to parent ARP';
COMMENT ON COLUMN itens_arp.item_excluido IS 'Soft delete flag - TRUE if item was deleted/excluded';
COMMENT ON COLUMN itens_arp.search_vector IS 'Full-text search vector for item descriptions, brands, and suppliers';

-- ============================================================================
-- TABLE: etl_executions (NEW - ETL Job Tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS etl_executions (
    -- Identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_type VARCHAR(20) NOT NULL,  -- 'initial' or 'incremental'
    status VARCHAR(20) NOT NULL,          -- 'running', 'completed', 'failed'

    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Date range processed
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,

    -- Statistics: ARPs
    arps_fetched INTEGER DEFAULT 0,
    arps_inserted INTEGER DEFAULT 0,
    arps_updated INTEGER DEFAULT 0,
    arps_skipped INTEGER DEFAULT 0,

    -- Statistics: Items
    items_fetched INTEGER DEFAULT 0,
    items_inserted INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_skipped INTEGER DEFAULT 0,

    -- Pagination tracking (for checkpoint/resume)
    last_ata_page_processed INTEGER,
    total_ata_pages INTEGER,

    -- Errors
    errors_count INTEGER DEFAULT 0,
    error_message TEXT,

    -- Configuration snapshot (for reproducibility)
    config_snapshot JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE etl_executions IS 'ETL job execution tracking and statistics';
COMMENT ON COLUMN etl_executions.execution_type IS 'Type of ETL run: initial (full load) or incremental (updates)';
COMMENT ON COLUMN etl_executions.last_ata_page_processed IS 'Checkpoint: last page processed (for resume after crash)';
COMMENT ON COLUMN etl_executions.config_snapshot IS 'JSON snapshot of configuration used for this execution';

-- ============================================================================
-- TABLE: etl_errors (NEW - Dead Letter Queue)
-- ============================================================================
CREATE TABLE IF NOT EXISTS etl_errors (
    -- Identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES etl_executions(id) ON DELETE CASCADE,

    -- Error details
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT,
    error_traceback TEXT,

    -- Context
    entity_type VARCHAR(20),        -- 'arp' or 'item'
    entity_identifier VARCHAR(200), -- codigo_arp_api or item identifier
    api_endpoint VARCHAR(200),
    request_params JSONB,

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE etl_errors IS 'Dead letter queue for failed ETL operations - enables retry and monitoring';
COMMENT ON COLUMN etl_errors.entity_type IS 'Type of entity that failed: arp or item';
COMMENT ON COLUMN etl_errors.resolved IS 'TRUE if error was successfully resolved/retried';

-- ============================================================================
-- INDEXES: orgaos
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_orgaos_uf ON orgaos(uf);
CREATE INDEX IF NOT EXISTS idx_orgaos_nome_gin ON orgaos USING gin(to_tsvector('portuguese', nome));

-- ============================================================================
-- INDEXES: arps
-- ============================================================================
-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_arps_codigo_api ON arps(codigo_arp_api);
CREATE INDEX IF NOT EXISTS idx_arps_numero_compra ON arps(numero_compra);
CREATE INDEX IF NOT EXISTS idx_arps_uasg ON arps(uasg_id);

-- Date range indexes (common query pattern)
CREATE INDEX IF NOT EXISTS idx_arps_vigencia_inicio ON arps(data_inicio_vigencia);
CREATE INDEX IF NOT EXISTS idx_arps_vigencia_fim ON arps(data_fim_vigencia);
CREATE INDEX IF NOT EXISTS idx_arps_vigencia_range ON arps(data_inicio_vigencia, data_fim_vigencia);

-- Status and filtering
CREATE INDEX IF NOT EXISTS idx_arps_situacao ON arps(situacao);
CREATE INDEX IF NOT EXISTS idx_arps_modalidade ON arps(modalidade);

-- Soft delete optimization (partial index - only non-deleted records)
CREATE INDEX IF NOT EXISTS idx_arps_not_excluido ON arps(ata_excluido) WHERE ata_excluido = FALSE;

-- ETL tracking
CREATE INDEX IF NOT EXISTS idx_arps_last_synced ON arps(last_synced_at DESC);
CREATE INDEX IF NOT EXISTS idx_arps_created_at ON arps(created_at DESC);

-- Full-text search (GIN index)
CREATE INDEX IF NOT EXISTS idx_arps_search_vector ON arps USING gin(search_vector);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_arps_uasg_vigencia ON arps(uasg_id, data_fim_vigencia) WHERE ata_excluido = FALSE;

-- ============================================================================
-- INDEXES: itens_arp
-- ============================================================================
-- Foreign key and relationship
CREATE INDEX IF NOT EXISTS idx_itens_arp_id ON itens_arp(arp_id);

-- Item identification
CREATE INDEX IF NOT EXISTS idx_itens_numero ON itens_arp(numero_item);
CREATE INDEX IF NOT EXISTS idx_itens_codigo ON itens_arp(codigo_item);

-- Supplier queries
CREATE INDEX IF NOT EXISTS idx_itens_fornecedor_cnpj ON itens_arp(cnpj_fornecedor);
CREATE INDEX IF NOT EXISTS idx_itens_fornecedor_nome ON itens_arp(nome_fornecedor);

-- Value-based queries
CREATE INDEX IF NOT EXISTS idx_itens_valor_unitario ON itens_arp(valor_unitario);
CREATE INDEX IF NOT EXISTS idx_itens_valor_total ON itens_arp(valor_total);

-- Product attributes
CREATE INDEX IF NOT EXISTS idx_itens_marca ON itens_arp(marca);
CREATE INDEX IF NOT EXISTS idx_itens_tipo ON itens_arp(tipo_item);

-- Soft delete optimization
CREATE INDEX IF NOT EXISTS idx_itens_not_excluido ON itens_arp(item_excluido) WHERE item_excluido = FALSE;

-- Full-text search (GIN index)
CREATE INDEX IF NOT EXISTS idx_itens_search_vector ON itens_arp USING gin(search_vector);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_itens_arp_valor ON itens_arp(arp_id, valor_unitario);
CREATE INDEX IF NOT EXISTS idx_itens_arp_fornecedor ON itens_arp(arp_id, cnpj_fornecedor) WHERE item_excluido = FALSE;

-- ============================================================================
-- INDEXES: etl_executions
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_etl_executions_status ON etl_executions(status);
CREATE INDEX IF NOT EXISTS idx_etl_executions_started ON etl_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_etl_executions_type ON etl_executions(execution_type);
CREATE INDEX IF NOT EXISTS idx_etl_executions_type_status ON etl_executions(execution_type, status, started_at DESC);

-- ============================================================================
-- INDEXES: etl_errors
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_etl_errors_execution ON etl_errors(execution_id);
CREATE INDEX IF NOT EXISTS idx_etl_errors_resolved ON etl_errors(resolved) WHERE resolved = FALSE;
CREATE INDEX IF NOT EXISTS idx_etl_errors_type ON etl_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_etl_errors_created ON etl_errors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_etl_errors_entity ON etl_errors(entity_type, entity_identifier);

-- ============================================================================
-- TRIGGERS: Auto-update timestamps
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to orgaos
DROP TRIGGER IF EXISTS update_orgaos_updated_at ON orgaos;
CREATE TRIGGER update_orgaos_updated_at
    BEFORE UPDATE ON orgaos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to arps
DROP TRIGGER IF EXISTS update_arps_updated_at ON arps;
CREATE TRIGGER update_arps_updated_at
    BEFORE UPDATE ON arps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to itens_arp
DROP TRIGGER IF EXISTS update_itens_updated_at ON itens_arp;
CREATE TRIGGER update_itens_updated_at
    BEFORE UPDATE ON itens_arp
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VACUUM AND ANALYZE
-- ============================================================================
-- Optimize table statistics for query planning
VACUUM ANALYZE orgaos;
VACUUM ANALYZE arps;
VACUUM ANALYZE itens_arp;
VACUUM ANALYZE etl_executions;
VACUUM ANALYZE etl_errors;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- After running this migration, execute these queries to verify:

-- 1. Check table structures
-- \d+ arps
-- \d+ itens_arp
-- \d+ etl_executions
-- \d+ etl_errors

-- 2. Verify indexes
-- SELECT tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('arps', 'itens_arp', 'etl_executions', 'etl_errors')
-- ORDER BY tablename, indexname;

-- 3. Check triggers
-- SELECT tgname, tgrelid::regclass, tgenabled
-- FROM pg_trigger
-- WHERE tgname LIKE 'update%updated_at';

-- 4. Verify extensions
-- SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'unaccent');

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Migration 001_enhanced_schema.sql completed successfully.
--
-- Next steps:
-- 1. Run verification queries above
-- 2. Update application models (backend/models.py, etl/models.py)
-- 3. Begin ETL implementation (Phase 2)
