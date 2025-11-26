from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text, Integer, Index, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime

class Orgao(Base):
    __tablename__ = "orgaos"
    uasg = Column(String(10), primary_key=True)
    nome = Column(String(500))
    uf = Column(String(2))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    arps = relationship("Arp", back_populates="orgao")

class Arp(Base):
    __tablename__ = "arps"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_arp_api = Column(String(100), unique=True, nullable=False, index=True)
    numero_arp = Column(String(50))
    numero_compra = Column(String(50), nullable=False)
    ano_compra = Column(Integer)

    # Organization reference
    uasg_id = Column(String(10), ForeignKey("orgaos.uasg"))

    # Dates
    data_inicio_vigencia = Column(Date)
    data_fim_vigencia = Column(Date)
    data_assinatura = Column(Date)
    data_atualizacao_pncp = Column(TIMESTAMP)

    # Content
    objeto = Column(Text)

    # Financial
    valor_total = Column(Numeric(15, 2))
    quantidade_itens = Column(Integer)

    # Status and classification
    situacao = Column(String(50))
    modalidade = Column(String(100))
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
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(TIMESTAMP)

    # Relationships
    orgao = relationship("Orgao", back_populates="arps")
    itens = relationship("ItemArp", back_populates="arp", cascade="all, delete-orphan")

class ItemArp(Base):
    __tablename__ = "itens_arp"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arp_id = Column(UUID(as_uuid=True), ForeignKey("arps.id", ondelete="CASCADE"))
    numero_item = Column(Integer)
    codigo_item = Column(String(50))

    # Description
    descricao = Column(Text)
    tipo_item = Column(String(50))

    # Pricing and quantity
    valor_unitario = Column(Numeric(15, 4))
    valor_total = Column(Numeric(15, 2))
    quantidade = Column(Numeric(15, 4))
    unidade = Column(String(20))

    # Product details
    marca = Column(String(200))
    modelo = Column(String(200))

    # Supplier information
    classificacao_fornecedor = Column(String(20))
    cnpj_fornecedor = Column(String(20))
    nome_fornecedor = Column(String(500))
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
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(TIMESTAMP)

    # Relationship
    arp = relationship("Arp", back_populates="itens")

    # Índice GIN para busca rápida
    __table_args__ = (
        Index('idx_itens_search_vector', 'search_vector', postgresql_using='gin'),
    )

class ETLExecution(Base):
    __tablename__ = "etl_executions"

    # Identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_type = Column(String(20), nullable=False)  # 'initial' or 'incremental'
    status = Column(String(20), nullable=False)  # 'running', 'completed', 'failed'

    # Timing
    started_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP)
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

    # Pagination tracking
    last_ata_page_processed = Column(Integer)
    total_ata_pages = Column(Integer)

    # Errors
    errors_count = Column(Integer, default=0)
    error_message = Column(Text)

    # Configuration snapshot
    config_snapshot = Column(JSONB)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    errors = relationship("ETLError", back_populates="execution", cascade="all, delete-orphan")

class ETLError(Base):
    __tablename__ = "etl_errors"

    # Identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("etl_executions.id", ondelete="CASCADE"))

    # Error details
    error_type = Column(String(50), nullable=False)
    error_message = Column(Text)
    error_traceback = Column(Text)

    # Context
    entity_type = Column(String(20))  # 'arp' or 'item'
    entity_identifier = Column(String(200))
    api_endpoint = Column(String(200))
    request_params = Column(JSONB)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(TIMESTAMP)
    resolved = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    execution = relationship("ETLExecution", back_populates="errors")
