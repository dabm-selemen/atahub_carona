"""
Async Database Module

Handles asynchronous database connections, sessions, and bulk operations.
Uses asyncpg for high-performance PostgreSQL access.
"""

import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy import text
from config import config
import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# ENGINE AND SESSION MANAGEMENT
# ============================================================================

class DatabaseManager:
    """
    Manages async database connections and sessions

    Implements singleton pattern for global engine instance.
    """

    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """
        Get or create async database engine

        Returns:
            AsyncEngine instance
        """
        if cls._engine is None:
            # Convert postgresql:// to postgresql+asyncpg://
            db_url = config.DATABASE_URL.replace(
                "postgresql://",
                "postgresql+asyncpg://"
            )

            cls._engine = create_async_engine(
                db_url,
                pool_size=config.DB_POOL_SIZE,
                max_overflow=config.DB_MAX_OVERFLOW,
                pool_recycle=config.DB_POOL_RECYCLE,
                echo=config.DEBUG_MODE,  # Log SQL in debug mode
                future=True
            )

            logger.info(
                "database_engine_created",
                pool_size=config.DB_POOL_SIZE,
                max_overflow=config.DB_MAX_OVERFLOW
            )

        return cls._engine

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker:
        """
        Get or create async session factory

        Returns:
            Session factory
        """
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(
                bind=cls.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )

        return cls._session_factory

    @classmethod
    async def close(cls):
        """Close database engine and cleanup"""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("database_engine_closed")


@asynccontextmanager
async def get_db_session():
    """
    Async context manager for database sessions

    Usage:
        async with get_db_session() as session:
            result = await session.execute(...)

    Yields:
        AsyncSession
    """
    session_factory = DatabaseManager.get_session_factory()
    session = session_factory()

    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("database_session_error", error=str(e))
        raise
    finally:
        await session.close()


# ============================================================================
# BULK OPERATIONS
# ============================================================================

async def bulk_upsert_orgaos(session: AsyncSession, orgaos: List[Dict[str, Any]]) -> int:
    """
    Bulk insert/update organizations (orgaos)

    Args:
        session: Database session
        orgaos: List of orgao dictionaries

    Returns:
        Number of records processed
    """
    if not orgaos:
        return 0

    query = text("""
        INSERT INTO orgaos (uasg, nome, uf, created_at, updated_at)
        VALUES (:uasg, :nome, :uf, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (uasg)
        DO UPDATE SET
            nome = EXCLUDED.nome,
            uf = EXCLUDED.uf,
            updated_at = CURRENT_TIMESTAMP
    """)

    try:
        await session.execute(query, orgaos)
        logger.debug("bulk_upsert_orgaos_success", count=len(orgaos))
        return len(orgaos)
    except Exception as e:
        logger.error("bulk_upsert_orgaos_error", error=str(e), count=len(orgaos))
        raise


async def bulk_upsert_arps(session: AsyncSession, arps: List[Dict[str, Any]]) -> int:
    """
    Bulk insert/update ARPs with UPSERT logic

    Args:
        session: Database session
        arps: List of ARP dictionaries

    Returns:
        Number of records processed
    """
    if not arps:
        return 0

    query = text("""
        INSERT INTO arps (
            id, codigo_arp_api, numero_arp, numero_compra, ano_compra,
            uasg_id, data_inicio_vigencia, data_fim_vigencia, data_assinatura,
            data_atualizacao_pncp, objeto, valor_total, quantidade_itens,
            situacao, modalidade, nome_modalidade, numero_controle_pncp_compra,
            numero_controle_pncp_ata, link_ata_pncp, link_compra_pncp, id_compra,
            codigo_orgao, nome_orgao, ata_excluido, created_at, updated_at, last_synced_at
        )
        VALUES (
            :id, :codigo_arp_api, :numero_arp, :numero_compra, :ano_compra,
            :uasg_id, :data_inicio_vigencia, :data_fim_vigencia, :data_assinatura,
            :data_atualizacao_pncp, :objeto, :valor_total, :quantidade_itens,
            :situacao, :modalidade, :nome_modalidade, :numero_controle_pncp_compra,
            :numero_controle_pncp_ata, :link_ata_pncp, :link_compra_pncp, :id_compra,
            :codigo_orgao, :nome_orgao, :ata_excluido, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (codigo_arp_api)
        DO UPDATE SET
            numero_arp = EXCLUDED.numero_arp,
            numero_compra = EXCLUDED.numero_compra,
            ano_compra = EXCLUDED.ano_compra,
            data_inicio_vigencia = EXCLUDED.data_inicio_vigencia,
            data_fim_vigencia = EXCLUDED.data_fim_vigencia,
            data_assinatura = EXCLUDED.data_assinatura,
            data_atualizacao_pncp = EXCLUDED.data_atualizacao_pncp,
            objeto = EXCLUDED.objeto,
            valor_total = EXCLUDED.valor_total,
            quantidade_itens = EXCLUDED.quantidade_itens,
            situacao = EXCLUDED.situacao,
            modalidade = EXCLUDED.modalidade,
            nome_modalidade = EXCLUDED.nome_modalidade,
            link_ata_pncp = EXCLUDED.link_ata_pncp,
            link_compra_pncp = EXCLUDED.link_compra_pncp,
            ata_excluido = EXCLUDED.ata_excluido,
            updated_at = CURRENT_TIMESTAMP,
            last_synced_at = CURRENT_TIMESTAMP
    """)

    try:
        await session.execute(query, arps)
        logger.debug("bulk_upsert_arps_success", count=len(arps))
        return len(arps)
    except Exception as e:
        logger.error("bulk_upsert_arps_error", error=str(e), count=len(arps))
        raise


async def bulk_upsert_items(session: AsyncSession, items: List[Dict[str, Any]]) -> int:
    """
    Bulk insert/update ARP items

    Args:
        session: Database session
        items: List of item dictionaries

    Returns:
        Number of records processed
    """
    if not items:
        return 0

    # Note: Using a unique constraint on (arp_id, numero_item, codigo_item) would be ideal
    # For now, we'll use id if provided, or generate new UUID
    query = text("""
        INSERT INTO itens_arp (
            id, arp_id, numero_item, codigo_item, descricao, tipo_item,
            valor_unitario, valor_total, quantidade, unidade,
            marca, modelo, classificacao_fornecedor, cnpj_fornecedor, nome_fornecedor,
            situacao_sicaf, codigo_pdm, nome_pdm, quantidade_empenhada,
            percentual_maior_desconto, maximo_adesao, item_excluido,
            created_at, updated_at, last_synced_at
        )
        VALUES (
            :id, :arp_id, :numero_item, :codigo_item, :descricao, :tipo_item,
            :valor_unitario, :valor_total, :quantidade, :unidade,
            :marca, :modelo, :classificacao_fornecedor, :cnpj_fornecedor, :nome_fornecedor,
            :situacao_sicaf, :codigo_pdm, :nome_pdm, :quantidade_empenhada,
            :percentual_maior_desconto, :maximo_adesao, :item_excluido,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (id)
        DO UPDATE SET
            descricao = EXCLUDED.descricao,
            tipo_item = EXCLUDED.tipo_item,
            valor_unitario = EXCLUDED.valor_unitario,
            valor_total = EXCLUDED.valor_total,
            quantidade = EXCLUDED.quantidade,
            unidade = EXCLUDED.unidade,
            marca = EXCLUDED.marca,
            modelo = EXCLUDED.modelo,
            classificacao_fornecedor = EXCLUDED.classificacao_fornecedor,
            cnpj_fornecedor = EXCLUDED.cnpj_fornecedor,
            nome_fornecedor = EXCLUDED.nome_fornecedor,
            situacao_sicaf = EXCLUDED.situacao_sicaf,
            quantidade_empenhada = EXCLUDED.quantidade_empenhada,
            percentual_maior_desconto = EXCLUDED.percentual_maior_desconto,
            item_excluido = EXCLUDED.item_excluido,
            updated_at = CURRENT_TIMESTAMP,
            last_synced_at = CURRENT_TIMESTAMP
    """)

    try:
        await session.execute(query, items)
        logger.debug("bulk_upsert_items_success", count=len(items))
        return len(items)
    except Exception as e:
        logger.error("bulk_upsert_items_error", error=str(e), count=len(items))
        raise


# ============================================================================
# QUERY HELPERS
# ============================================================================

async def get_arp_by_codigo_api(session: AsyncSession, codigo_arp_api: str) -> Optional[Dict[str, Any]]:
    """
    Get ARP by API code

    Args:
        session: Database session
        codigo_arp_api: Unique API identifier

    Returns:
        ARP dictionary or None
    """
    query = text("""
        SELECT * FROM arps
        WHERE codigo_arp_api = :codigo_arp_api
    """)

    result = await session.execute(query, {"codigo_arp_api": codigo_arp_api})
    row = result.fetchone()

    if row:
        return dict(row._mapping)
    return None


async def get_last_successful_execution(session: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Get last successful ETL execution

    Args:
        session: Database session

    Returns:
        Execution dictionary or None
    """
    query = text("""
        SELECT * FROM etl_executions
        WHERE status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 1
    """)

    result = await session.execute(query)
    row = result.fetchone()

    if row:
        return dict(row._mapping)
    return None


async def get_incomplete_execution(session: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Get incomplete/failed ETL execution for resume

    Args:
        session: Database session

    Returns:
        Execution dictionary or None
    """
    query = text("""
        SELECT * FROM etl_executions
        WHERE status IN ('running', 'failed')
        AND last_ata_page_processed IS NOT NULL
        ORDER BY started_at DESC
        LIMIT 1
    """)

    result = await session.execute(query)
    row = result.fetchone()

    if row:
        return dict(row._mapping)
    return None


# ============================================================================
# HEALTH CHECK
# ============================================================================

async def check_database_connection() -> bool:
    """
    Check if database connection is healthy

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("database_health_check_success")
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False


# ============================================================================
# CLEANUP
# ============================================================================

async def cleanup():
    """Close database connections"""
    await DatabaseManager.close()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test database connection
    async def test():
        logger.info("Testing database connection...")

        is_healthy = await check_database_connection()

        if is_healthy:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")

        await cleanup()

    asyncio.run(test())
