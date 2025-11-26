"""
SQLAlchemy Models for ETL

ORM models matching the enhanced database schema.
Used for type-safe database operations in the ETL process.
"""

from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Boolean, Text,
    ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import expression
from datetime import datetime
import uuid

Base = declarative_base()


# ============================================================================
# MODEL: Orgao
# ============================================================================

class Orgao(Base):
    """
    Government Agency/Organization model

    Represents a UASG (Unidade de Administração de Serviços Gerais)
    """
    __tablename__ = "orgaos"

    uasg = Column(String(10), primary_key=True)
    nome = Column(String(500))
    uf = Column(String(2))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    arps = relationship("Arp", back_populates="orgao")

    def __repr__(self):
        return f"<Orgao(uasg={self.uasg}, nome={self.nome}, uf={self.uf})>"


# ============================================================================
# MODEL: Arp
# ============================================================================

class Arp(Base):
    """
    Price Registration Record (Ata de Registro de Preços)

    Main model for ARPs with comprehensive metadata and tracking.
    """
    __tablename__ = "arps"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_arp_api = Column(String(100), unique=True, nullable=False, index=True)
    numero_arp = Column(String(50))
    numero_compra = Column(String(50), nullable=False, index=True)  # CRITICAL
    ano_compra = Column(Integer)

    # Organization reference
    uasg_id = Column(String(10), ForeignKey("orgaos.uasg"))

    # Dates
    data_inicio_vigencia = Column(Date, index=True)
    data_fim_vigencia = Column(Date, index=True)
    data_assinatura = Column(Date)
    data_atualizacao_pncp = Column(DateTime)

    # Content
    objeto = Column(Text)

    # Financial
    valor_total = Column(Numeric(15, 2))
    quantidade_itens = Column(Integer)

    # Status and classification
    situacao = Column(String(50), index=True)
    modalidade = Column(String(100), index=True)
    nome_modalidade = Column(String(200))

    # PNCP Links and identifiers
    numero_controle_pncp_compra = Column(String(100))
    numero_controle_pncp_ata = Column(String(100))
    link_ata_pncp = Column(Text)
    link_compra_pncp = Column(Text)
    id_compra = Column(String(50))

    # Additional metadata
    codigo_orgao = Column(String(20))
    nome_orgao = Column(String(500))

    # Soft delete flag
    ata_excluido = Column(Boolean, default=False, index=True)

    # ETL tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime, index=True)

    # Full-text search (generated column - managed by database)
    # search_vector = Column(TSVECTOR)  # Commented out as it's auto-generated

    # Relationships
    orgao = relationship("Orgao", back_populates="arps")
    itens = relationship("ItemArp", back_populates="arp", cascade="all, delete-orphan")

    # Composite indexes (defined at table level below)
    __table_args__ = (
        Index('idx_arps_vigencia_range', 'data_inicio_vigencia', 'data_fim_vigencia'),
        Index('idx_arps_uasg_vigencia', 'uasg_id', 'data_fim_vigencia'),
    )

    def __repr__(self):
        return f"<Arp(numero_arp={self.numero_arp}, uasg={self.uasg_id}, vigencia={self.data_fim_vigencia})>"

    @property
    def is_active(self) -> bool:
        """Check if ARP is currently active"""
        if not self.data_fim_vigencia or self.ata_excluido:
            return False
        from datetime import date
        return self.data_fim_vigencia >= date.today()


# ============================================================================
# MODEL: ItemArp
# ============================================================================

class ItemArp(Base):
    """
    ARP Item model

    Represents individual items within a Price Registration Record.
    """
    __tablename__ = "itens_arp"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arp_id = Column(UUID(as_uuid=True), ForeignKey("arps.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_item = Column(Integer, index=True)
    codigo_item = Column(String(50), index=True)

    # Description
    descricao = Column(Text)
    tipo_item = Column(String(50), index=True)

    # Pricing and quantity
    valor_unitario = Column(Numeric(15, 4), index=True)
    valor_total = Column(Numeric(15, 2), index=True)
    quantidade = Column(Numeric(15, 4))
    unidade = Column(String(20))

    # Product details
    marca = Column(String(200), index=True)
    modelo = Column(String(200))

    # Supplier information
    classificacao_fornecedor = Column(String(20))
    cnpj_fornecedor = Column(String(20), index=True)
    nome_fornecedor = Column(String(500), index=True)
    situacao_sicaf = Column(String(50))

    # Classification
    codigo_pdm = Column(Integer)
    nome_pdm = Column(String(500))

    # Additional metrics
    quantidade_empenhada = Column(Numeric(15, 4))
    percentual_maior_desconto = Column(Numeric(5, 2))
    maximo_adesao = Column(Numeric(15, 2))

    # Soft delete flag
    item_excluido = Column(Boolean, default=False, index=True)

    # ETL tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime)

    # Full-text search (generated column - managed by database)
    # search_vector = Column(TSVECTOR)  # Commented out as it's auto-generated

    # Relationships
    arp = relationship("Arp", back_populates="itens")

    # Composite indexes
    __table_args__ = (
        Index('idx_itens_arp_valor', 'arp_id', 'valor_unitario'),
        Index('idx_itens_arp_fornecedor', 'arp_id', 'cnpj_fornecedor'),
    )

    def __repr__(self):
        return f"<ItemArp(id={self.id}, numero_item={self.numero_item}, descricao={self.descricao[:50]})>"

    @property
    def is_active(self) -> bool:
        """Check if item is active (not excluded)"""
        return not self.item_excluido


# ============================================================================
# MODEL: EtlExecution
# ============================================================================

class EtlExecution(Base):
    """
    ETL Execution Tracking model

    Tracks each ETL job execution with statistics and status.
    """
    __tablename__ = "etl_executions"

    # Identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_type = Column(String(20), nullable=False, index=True)  # 'initial' or 'incremental'
    status = Column(String(20), nullable=False, index=True)  # 'running', 'completed', 'failed'

    # Timing
    started_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Date range processed
    date_range_start = Column(Date, nullable=False)
    date_range_end = Column(Date, nullable=False)

    # Statistics: ARPs
    arps_fetched = Column(Integer, default=0)
    arps_inserted = Column(Integer, default=0)
    arps_updated = Column(Integer, default=0)
    arps_skipped = Column(Integer, default=0)

    # Statistics: Items
    items_fetched = Column(Integer, default=0)
    items_inserted = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_skipped = Column(Integer, default=0)

    # Pagination tracking (for checkpoint/resume)
    last_ata_page_processed = Column(Integer)
    total_ata_pages = Column(Integer)

    # Errors
    errors_count = Column(Integer, default=0)
    error_message = Column(Text)

    # Configuration snapshot (for reproducibility)
    config_snapshot = Column(JSONB)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    errors = relationship("EtlError", back_populates="execution", cascade="all, delete-orphan")

    # Composite index
    __table_args__ = (
        Index('idx_etl_executions_type_status', 'execution_type', 'status', 'started_at'),
    )

    def __repr__(self):
        return f"<EtlExecution(id={self.id}, type={self.execution_type}, status={self.status})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if not self.total_ata_pages or self.total_ata_pages == 0:
            return 0.0
        return (self.last_ata_page_processed or 0) / self.total_ata_pages * 100

    @property
    def total_arps_processed(self) -> int:
        """Total ARPs processed (inserted + updated)"""
        return (self.arps_inserted or 0) + (self.arps_updated or 0)

    @property
    def total_items_processed(self) -> int:
        """Total items processed (inserted + updated)"""
        return (self.items_inserted or 0) + (self.items_updated or 0)

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        total = self.arps_fetched or 0
        if total == 0:
            return 0.0
        return (self.errors_count or 0) / total * 100


# ============================================================================
# MODEL: EtlError
# ============================================================================

class EtlError(Base):
    """
    ETL Error Tracking model (Dead Letter Queue)

    Stores failed operations for retry and monitoring.
    """
    __tablename__ = "etl_errors"

    # Identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("etl_executions.id", ondelete="CASCADE"), index=True)

    # Error details
    error_type = Column(String(50), nullable=False, index=True)
    error_message = Column(Text)
    error_traceback = Column(Text)

    # Context
    entity_type = Column(String(20), index=True)  # 'arp' or 'item'
    entity_identifier = Column(String(200))
    api_endpoint = Column(String(200))
    request_params = Column(JSONB)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime)
    resolved = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    execution = relationship("EtlExecution", back_populates="errors")

    # Composite index
    __table_args__ = (
        Index('idx_etl_errors_entity', 'entity_type', 'entity_identifier'),
    )

    def __repr__(self):
        return f"<EtlError(id={self.id}, type={self.error_type}, entity={self.entity_type})>"

    @property
    def can_retry(self) -> bool:
        """Check if error can be retried"""
        from config import config
        return not self.resolved and self.retry_count < config.MAX_RETRIES


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_base():
    """Get declarative base"""
    return Base


async def create_all_tables(engine):
    """
    Create all tables (development only)

    Args:
        engine: SQLAlchemy engine
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables(engine):
    """
    Drop all tables (development only - USE WITH CAUTION)

    Args:
        engine: SQLAlchemy engine
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Print model information
    print("=== ETL Models ===\n")

    models = [Orgao, Arp, ItemArp, EtlExecution, EtlError]

    for model in models:
        print(f"{model.__name__}:")
        print(f"  Table: {model.__tablename__}")
        print(f"  Columns: {len(model.__table__.columns)}")
        print(f"  Indexes: {len(model.__table__.indexes)}")
        print()

    print(f"Total models: {len(models)}")
