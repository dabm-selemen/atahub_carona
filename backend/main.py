from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
import models, database

# Inicializar Banco
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Configurar CORS (Frontend roda na porta 3002 no Docker)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints ---

@app.get("/")
def root():
    return {"status": "ok", "message": "AtaHub API is running"}

class ItemResponse(BaseModel):
    descricao: str
    valor_unitario: float
    marca: Optional[str]
    quantidade: float

class SearchResult(BaseModel):
    id_arp: str
    numero_arp: str
    orgao_nome: str
    uf: Optional[str]
    vigencia_fim: Optional[date]
    item: ItemResponse

# --- Endpoints ---

@app.get("/buscar", response_model=List[SearchResult])
def buscar_itens(
    q: str,
    db: Session = Depends(database.get_db)
):
    # Query nativa para usar a função 'plainto_tsquery' do Postgres e o índice GIN
    sql = text("""
        SELECT
            arps.id as id_arp, arps.numero_arp, arps.data_fim_vigencia,
            orgaos.nome as orgao_nome, orgaos.uf,
            itens.descricao, itens.valor_unitario, itens.marca, itens.quantidade
        FROM itens_arp itens
        JOIN arps ON itens.arp_id = arps.id
        JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE itens.search_vector @@ plainto_tsquery('portuguese', :q)
        AND arps.data_fim_vigencia >= CURRENT_DATE
        LIMIT 50
    """)

    results = db.execute(sql, {"q": q}).fetchall()

    response = []
    for row in results:
        response.append({
            "id_arp": str(row.id_arp),
            "numero_arp": row.numero_arp,
            "orgao_nome": row.orgao_nome,
            "uf": row.uf,
            "vigencia_fim": row.data_fim_vigencia,
            "item": {
                "descricao": row.descricao,
                "valor_unitario": float(row.valor_unitario),
                "marca": row.marca,
                "quantidade": float(row.quantidade)
            }
        })
    return response


# ============================================================================
# ADMIN ETL ENDPOINTS
# ============================================================================

class ETLStatusResponse(BaseModel):
    execution_id: Optional[str]
    status: Optional[str]
    progress: Optional[str]
    arps_processed: Optional[int]
    items_processed: Optional[int]
    errors: Optional[int]
    duration_seconds: Optional[int]
    started_at: Optional[str]

class ETLExecutionSummary(BaseModel):
    id: str
    execution_type: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    arps_processed: int
    items_processed: int
    errors_count: int


@app.get("/admin/etl/status", response_model=ETLStatusResponse)
def get_etl_status(db: Session = Depends(database.get_db)):
    """
    Get current or most recent ETL execution status
    """
    sql = text("""
        SELECT
            id, status, started_at,
            last_ata_page_processed, total_ata_pages,
            arps_inserted + arps_updated as arps_processed,
            items_inserted + items_updated as items_processed,
            errors_count, duration_seconds
        FROM etl_executions
        ORDER BY started_at DESC
        LIMIT 1
    """)

    result = db.execute(sql).fetchone()

    if not result:
        return ETLStatusResponse(
            execution_id=None,
            status="never_run",
            progress=None,
            arps_processed=0,
            items_processed=0,
            errors=0,
            duration_seconds=None,
            started_at=None
        )

    progress = None
    if result.total_ata_pages and result.last_ata_page_processed:
        progress = f"{result.last_ata_page_processed}/{result.total_ata_pages}"

    return ETLStatusResponse(
        execution_id=str(result.id),
        status=result.status,
        progress=progress,
        arps_processed=result.arps_processed or 0,
        items_processed=result.items_processed or 0,
        errors=result.errors_count or 0,
        duration_seconds=result.duration_seconds,
        started_at=str(result.started_at) if result.started_at else None
    )


@app.get("/admin/etl/executions", response_model=List[ETLExecutionSummary])
def list_etl_executions(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(database.get_db)
):
    """
    List recent ETL executions
    """
    sql = text("""
        SELECT
            id, execution_type, status, started_at, completed_at,
            duration_seconds,
            arps_inserted + arps_updated as arps_processed,
            items_inserted + items_updated as items_processed,
            errors_count
        FROM etl_executions
        ORDER BY started_at DESC
        LIMIT :limit
    """)

    results = db.execute(sql, {"limit": limit}).fetchall()

    return [
        ETLExecutionSummary(
            id=str(row.id),
            execution_type=row.execution_type,
            status=row.status,
            started_at=str(row.started_at),
            completed_at=str(row.completed_at) if row.completed_at else None,
            duration_seconds=row.duration_seconds,
            arps_processed=row.arps_processed or 0,
            items_processed=row.items_processed or 0,
            errors_count=row.errors_count or 0
        )
        for row in results
    ]


@app.get("/admin/etl/errors")
def list_etl_errors(
    execution_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(database.get_db)
):
    """
    List ETL errors (dead letter queue)
    """
    if execution_id:
        sql = text("""
            SELECT
                id, execution_id, error_type, error_message,
                entity_type, entity_identifier, created_at, resolved
            FROM etl_errors
            WHERE execution_id = :execution_id
            AND resolved = FALSE
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        results = db.execute(sql, {"execution_id": execution_id, "limit": limit}).fetchall()
    else:
        sql = text("""
            SELECT
                id, execution_id, error_type, error_message,
                entity_type, entity_identifier, created_at, resolved
            FROM etl_errors
            WHERE resolved = FALSE
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        results = db.execute(sql, {"limit": limit}).fetchall()

    return [
        {
            "id": str(row.id),
            "execution_id": str(row.execution_id),
            "error_type": row.error_type,
            "error_message": row.error_message,
            "entity_type": row.entity_type,
            "entity_identifier": row.entity_identifier,
            "created_at": str(row.created_at),
            "resolved": row.resolved
        }
        for row in results
    ]


@app.get("/admin/etl/stats")
def get_etl_stats(db: Session = Depends(database.get_db)):
    """
    Get overall ETL statistics
    """
    stats_sql = text("""
        SELECT
            COUNT(*) as total_arps,
            COUNT(*) FILTER (WHERE ata_excluido = FALSE) as active_arps,
            COUNT(*) FILTER (WHERE data_fim_vigencia >= CURRENT_DATE AND ata_excluido = FALSE) as valid_arps,
            MIN(data_inicio_vigencia) as oldest_arp,
            MAX(data_fim_vigencia) as newest_arp
        FROM arps
    """)

    items_sql = text("""
        SELECT
            COUNT(*) as total_items,
            COUNT(*) FILTER (WHERE item_excluido = FALSE) as active_items
        FROM itens_arp
    """)

    exec_sql = text("""
        SELECT
            COUNT(*) as total_executions,
            COUNT(*) FILTER (WHERE status = 'completed') as completed,
            COUNT(*) FILTER (WHERE status = 'failed') as failed
        FROM etl_executions
    """)

    arps_stats = db.execute(stats_sql).fetchone()
    items_stats = db.execute(items_sql).fetchone()
    exec_stats = db.execute(exec_sql).fetchone()

    return {
        "arps": {
            "total": arps_stats.total_arps or 0,
            "active": arps_stats.active_arps or 0,
            "valid": arps_stats.valid_arps or 0,
            "oldest_date": str(arps_stats.oldest_arp) if arps_stats.oldest_arp else None,
            "newest_date": str(arps_stats.newest_arp) if arps_stats.newest_arp else None
        },
        "items": {
            "total": items_stats.total_items or 0,
            "active": items_stats.active_items or 0
        },
        "executions": {
            "total": exec_stats.total_executions or 0,
            "completed": exec_stats.completed or 0,
            "failed": exec_stats.failed or 0
        }
    }
