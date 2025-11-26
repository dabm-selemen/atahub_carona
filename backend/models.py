from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class Orgao(Base):
    __tablename__ = "orgaos"
    uasg = Column(String(10), primary_key=True)
    nome = Column(String)
    uf = Column(String(2))

class Arp(Base):
    __tablename__ = "arps"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_arp_api = Column(String, unique=True, index=True)
    numero_arp = Column(String)
    uasg_id = Column(String, ForeignKey("orgaos.uasg"))
    data_inicio_vigencia = Column(Date)
    data_fim_vigencia = Column(Date)
    objeto = Column(Text)

    orgao = relationship("Orgao")
    itens = relationship("ItemArp", back_populates="arp")

class ItemArp(Base):
    __tablename__ = "itens_arp"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arp_id = Column(UUID(as_uuid=True), ForeignKey("arps.id"))
    numero_item = Column(Integer)
    descricao = Column(Text)
    valor_unitario = Column(Numeric(15, 2))
    quantidade = Column(Numeric(15, 2))
    unidade = Column(String)
    marca = Column(String)
    search_vector = Column(TSVECTOR) # Para Full Text Search

    arp = relationship("Arp", back_populates="itens")

    # Índice GIN para busca rápida
    __table_args__ = (
        Index('idx_itens_search_vector', 'search_vector', postgresql_using='gin'),
    )
