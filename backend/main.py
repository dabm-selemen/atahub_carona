from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, cast, String
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
import models, database
import pandas as pd
import io
from collections import defaultdict

# Inicializar Banco
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AtaHub API", version="2.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3001", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class ItemResponse(BaseModel):
    descricao: str
    valor_unitario: float
    marca: Optional[str]
    quantidade: float
    modelo: Optional[str] = None
    unidade: Optional[str] = None
    fornecedor: Optional[str] = None

class SearchResult(BaseModel):
    id_arp: str
    numero_arp: str
    orgao_nome: str
    uf: Optional[str]
    vigencia_fim: Optional[date]
    vigencia_inicio: Optional[date]
    item: ItemResponse

class PriceStats(BaseModel):
    min_price: float
    max_price: float
    avg_price: float
    median_price: float
    count: int
    savings_potential: float  # max - min

class PriceComparison(BaseModel):
    item_description: str
    stats: PriceStats
    results: List[SearchResult]
    by_state: dict  # UF -> avg_price

class ArpDetailItem(BaseModel):
    id: str
    numero_item: int
    descricao: str
    valor_unitario: float
    valor_total: Optional[float]
    quantidade: float
    unidade: Optional[str]
    marca: Optional[str]
    modelo: Optional[str]
    fornecedor: Optional[str]
    cnpj_fornecedor: Optional[str]

class ArpDetail(BaseModel):
    id: str
    numero_arp: str
    numero_compra: str
    orgao_nome: str
    uf: Optional[str]
    data_inicio_vigencia: Optional[date]
    data_fim_vigencia: Optional[date]
    objeto: str
    valor_total: Optional[float]
    quantidade_itens: int
    situacao: Optional[str]
    modalidade: Optional[str]
    link_ata_pncp: Optional[str]
    itens: List[ArpDetailItem]

class DashboardStats(BaseModel):
    total_arps: int
    active_arps: int
    total_items: int
    total_value: float
    arps_by_state: dict
    recent_arps: List[dict]
    top_suppliers: List[dict]

class Supplier(BaseModel):
    cnpj: str
    nome: str
    total_contracts: int
    total_value: float
    avg_price: float

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

# --- Endpoints ---

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AtaHub API v2.0 - Enhanced Government Procurement Platform",
        "endpoints": {
            "search": "/buscar",
            "compare": "/comparar",
            "arp_detail": "/arp/{id}",
            "stats": "/stats",
            "suppliers": "/fornecedores",
            "export": "/exportar",
            "autocomplete": "/autocomplete"
        }
    }

@app.get("/buscar", response_model=List[SearchResult])
def buscar_itens(
    q: str = Query(default="", description="Search query"),
    ufs: Optional[str] = Query(default=None, description="Comma-separated state codes"),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    vigencia_inicio: Optional[date] = None,
    vigencia_fim: Optional[date] = None,
    orgao: Optional[str] = None,
    fornecedor: Optional[str] = None,
    sort_by: str = Query(default="relevance", regex="^(relevance|price_asc|price_desc|date_asc|date_desc)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(database.get_db)
):
    """Advanced search with multiple filters"""

    # Build WHERE clauses
    where_clauses = ["arps.data_fim_vigencia >= CURRENT_DATE", "arps.ata_excluido = FALSE", "itens.item_excluido = FALSE"]
    params = {}

    # Text search - only if query is provided
    if q and q.strip():
        where_clauses.append("itens.search_vector @@ plainto_tsquery('portuguese', :q)")
        params["q"] = q

    # State filter
    if ufs:
        uf_list = [uf.strip().upper() for uf in ufs.split(",")]
        uf_str = ",".join([f"'{uf}'" for uf in uf_list])
        where_clauses.append(f"orgaos.uf IN ({uf_str})")

    # Price filter
    if min_price is not None:
        where_clauses.append("itens.valor_unitario >= :min_price")
        params["min_price"] = min_price

    if max_price is not None:
        where_clauses.append("itens.valor_unitario <= :max_price")
        params["max_price"] = max_price

    # Date filter
    if vigencia_inicio:
        where_clauses.append("arps.data_inicio_vigencia >= :vigencia_inicio")
        params["vigencia_inicio"] = vigencia_inicio

    if vigencia_fim:
        where_clauses.append("arps.data_fim_vigencia <= :vigencia_fim")
        params["vigencia_fim"] = vigencia_fim

    # Organization filter
    if orgao:
        where_clauses.append("orgaos.nome ILIKE :orgao")
        params["orgao"] = f"%{orgao}%"

    # Supplier filter
    if fornecedor:
        where_clauses.append("itens.nome_fornecedor ILIKE :fornecedor")
        params["fornecedor"] = f"%{fornecedor}%"

    # Sort clause
    if sort_by == "price_asc":
        order_clause = "itens.valor_unitario ASC"
    elif sort_by == "price_desc":
        order_clause = "itens.valor_unitario DESC"
    elif sort_by == "date_asc":
        order_clause = "arps.data_fim_vigencia ASC"
    elif sort_by == "date_desc":
        order_clause = "arps.data_fim_vigencia DESC"
    else:  # relevance (default for text search)
        order_clause = "arps.data_fim_vigencia DESC"

    where_sql = " AND ".join(where_clauses)
    params["limit"] = limit
    params["offset"] = offset

    sql = text(f"""
        SELECT
            arps.id as id_arp, arps.numero_arp, arps.data_fim_vigencia, arps.data_inicio_vigencia,
            orgaos.nome as orgao_nome, orgaos.uf,
            itens.descricao, itens.valor_unitario, itens.marca, itens.quantidade,
            itens.modelo, itens.unidade, itens.nome_fornecedor
        FROM itens_arp itens
        JOIN arps ON itens.arp_id = arps.id
        JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE {where_sql}
        ORDER BY {order_clause}
        LIMIT :limit OFFSET :offset
    """)

    results = db.execute(sql, params).fetchall()

    response = []
    for row in results:
        response.append({
            "id_arp": str(row.id_arp),
            "numero_arp": row.numero_arp,
            "orgao_nome": row.orgao_nome,
            "uf": row.uf,
            "vigencia_fim": row.data_fim_vigencia,
            "vigencia_inicio": row.data_inicio_vigencia,
            "item": {
                "descricao": row.descricao,
                "valor_unitario": float(row.valor_unitario),
                "marca": row.marca,
                "quantidade": float(row.quantidade),
                "modelo": row.modelo,
                "unidade": row.unidade,
                "fornecedor": row.nome_fornecedor
            }
        })
    return response

@app.get("/comparar", response_model=PriceComparison)
def comparar_precos(
    q: str,
    ufs: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Compare prices for similar items across different ARPs"""

    where_clauses = [
        "itens.search_vector @@ plainto_tsquery('portuguese', :q)",
        "arps.data_fim_vigencia >= CURRENT_DATE",
        "arps.ata_excluido = FALSE",
        "itens.item_excluido = FALSE"
    ]
    params = {"q": q}

    if ufs:
        uf_list = [uf.strip().upper() for uf in ufs.split(",")]
        uf_str = ",".join([f"'{uf}'" for uf in uf_list])
        where_clauses.append(f"orgaos.uf IN ({uf_str})")

    where_sql = " AND ".join(where_clauses)

    # Get all matching items with prices
    sql = text(f"""
        SELECT
            arps.id as id_arp, arps.numero_arp, arps.data_fim_vigencia, arps.data_inicio_vigencia,
            orgaos.nome as orgao_nome, orgaos.uf,
            itens.descricao, itens.valor_unitario, itens.marca, itens.quantidade,
            itens.modelo, itens.unidade, itens.nome_fornecedor
        FROM itens_arp itens
        JOIN arps ON itens.arp_id = arps.id
        JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE {where_sql}
        ORDER BY itens.valor_unitario ASC
    """)

    results = db.execute(sql, params).fetchall()

    if not results:
        raise HTTPException(status_code=404, detail="No items found for comparison")

    # Calculate statistics
    prices = [float(row.valor_unitario) for row in results if row.valor_unitario]
    if not prices:
        raise HTTPException(status_code=404, detail="No valid prices found")

    prices.sort()
    median_price = prices[len(prices) // 2] if prices else 0

    stats = PriceStats(
        min_price=min(prices),
        max_price=max(prices),
        avg_price=sum(prices) / len(prices),
        median_price=median_price,
        count=len(prices),
        savings_potential=max(prices) - min(prices)
    )

    # Group by state
    by_state = defaultdict(list)
    for row in results:
        if row.uf and row.valor_unitario:
            by_state[row.uf].append(float(row.valor_unitario))

    state_avg = {uf: sum(prices) / len(prices) for uf, prices in by_state.items()}

    # Format results
    search_results = []
    for row in results:
        search_results.append(SearchResult(
            id_arp=str(row.id_arp),
            numero_arp=row.numero_arp,
            orgao_nome=row.orgao_nome,
            uf=row.uf,
            vigencia_fim=row.data_fim_vigencia,
            vigencia_inicio=row.data_inicio_vigencia,
            item=ItemResponse(
                descricao=row.descricao,
                valor_unitario=float(row.valor_unitario),
                marca=row.marca,
                quantidade=float(row.quantidade),
                modelo=row.modelo,
                unidade=row.unidade,
                fornecedor=row.nome_fornecedor
            )
        ))

    # Use the first item's description as representative
    item_desc = results[0].descricao if results else q

    return PriceComparison(
        item_description=item_desc,
        stats=stats,
        results=search_results,
        by_state=state_avg
    )

@app.get("/arp/{arp_id}", response_model=ArpDetail)
def get_arp_detail(arp_id: str, db: Session = Depends(database.get_db)):
    """Get complete ARP details with all items"""

    # Get ARP info
    arp_sql = text("""
        SELECT
            arps.*,
            orgaos.nome as orgao_nome, orgaos.uf
        FROM arps
        LEFT JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE arps.id = :arp_id
    """)

    arp = db.execute(arp_sql, {"arp_id": arp_id}).fetchone()

    if not arp:
        raise HTTPException(status_code=404, detail="ARP not found")

    # Get all items
    items_sql = text("""
        SELECT
            id, numero_item, descricao, valor_unitario, valor_total,
            quantidade, unidade, marca, modelo,
            nome_fornecedor, cnpj_fornecedor
        FROM itens_arp
        WHERE arp_id = :arp_id AND item_excluido = FALSE
        ORDER BY numero_item
    """)

    items = db.execute(items_sql, {"arp_id": arp_id}).fetchall()

    return ArpDetail(
        id=str(arp.id),
        numero_arp=arp.numero_arp or "",
        numero_compra=arp.numero_compra or "",
        orgao_nome=arp.orgao_nome or "",
        uf=arp.uf,
        data_inicio_vigencia=arp.data_inicio_vigencia,
        data_fim_vigencia=arp.data_fim_vigencia,
        objeto=arp.objeto or "",
        valor_total=float(arp.valor_total) if arp.valor_total else None,
        quantidade_itens=len(items),
        situacao=arp.situacao,
        modalidade=arp.modalidade,
        link_ata_pncp=arp.link_ata_pncp,
        itens=[
            ArpDetailItem(
                id=str(item.id),
                numero_item=item.numero_item or 0,
                descricao=item.descricao or "",
                valor_unitario=float(item.valor_unitario) if item.valor_unitario else 0.0,
                valor_total=float(item.valor_total) if item.valor_total else None,
                quantidade=float(item.quantidade) if item.quantidade else 0.0,
                unidade=item.unidade,
                marca=item.marca,
                modelo=item.modelo,
                fornecedor=item.nome_fornecedor,
                cnpj_fornecedor=item.cnpj_fornecedor
            ) for item in items
        ]
    )

@app.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(database.get_db)):
    """Get dashboard statistics"""

    # Total ARPs and value
    arp_stats_sql = text("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE data_fim_vigencia >= CURRENT_DATE AND ata_excluido = FALSE) as active,
            COALESCE(SUM(valor_total), 0) as total_value
        FROM arps
        WHERE ata_excluido = FALSE
    """)

    arp_stats = db.execute(arp_stats_sql).fetchone()

    # Total items
    items_stats_sql = text("""
        SELECT COUNT(*) as total
        FROM itens_arp
        WHERE item_excluido = FALSE
    """)

    items_stats = db.execute(items_stats_sql).fetchone()

    # ARPs by state
    by_state_sql = text("""
        SELECT orgaos.uf, COUNT(*) as count
        FROM arps
        JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE arps.ata_excluido = FALSE
        AND arps.data_fim_vigencia >= CURRENT_DATE
        GROUP BY orgaos.uf
        ORDER BY count DESC
    """)

    by_state = db.execute(by_state_sql).fetchall()
    arps_by_state = {row.uf: row.count for row in by_state if row.uf}

    # Recent ARPs
    recent_sql = text("""
        SELECT
            arps.id, arps.numero_arp, arps.objeto,
            orgaos.nome as orgao_nome, orgaos.uf,
            arps.data_inicio_vigencia, arps.valor_total
        FROM arps
        JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE arps.ata_excluido = FALSE
        ORDER BY arps.created_at DESC
        LIMIT 10
    """)

    recent = db.execute(recent_sql).fetchall()
    recent_arps = [
        {
            "id": str(row.id),
            "numero_arp": row.numero_arp,
            "objeto": row.objeto[:100] + "..." if row.objeto and len(row.objeto) > 100 else row.objeto,
            "orgao_nome": row.orgao_nome,
            "uf": row.uf,
            "data_inicio": str(row.data_inicio_vigencia) if row.data_inicio_vigencia else None,
            "valor_total": float(row.valor_total) if row.valor_total else None
        }
        for row in recent
    ]

    # Top suppliers
    suppliers_sql = text("""
        SELECT
            nome_fornecedor,
            COUNT(DISTINCT arp_id) as contracts,
            SUM(valor_total) as total_value
        FROM itens_arp
        WHERE item_excluido = FALSE
        AND nome_fornecedor IS NOT NULL
        GROUP BY nome_fornecedor
        ORDER BY contracts DESC
        LIMIT 10
    """)

    suppliers = db.execute(suppliers_sql).fetchall()
    top_suppliers = [
        {
            "nome": row.nome_fornecedor,
            "contracts": row.contracts,
            "total_value": float(row.total_value) if row.total_value else 0.0
        }
        for row in suppliers
    ]

    return DashboardStats(
        total_arps=arp_stats.total or 0,
        active_arps=arp_stats.active or 0,
        total_items=items_stats.total or 0,
        total_value=float(arp_stats.total_value) if arp_stats.total_value else 0.0,
        arps_by_state=arps_by_state,
        recent_arps=recent_arps,
        top_suppliers=top_suppliers
    )

@app.get("/fornecedores")
def search_suppliers(
    q: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(database.get_db)
):
    """Search suppliers"""

    if q:
        sql = text("""
            SELECT
                cnpj_fornecedor,
                nome_fornecedor,
                COUNT(DISTINCT arp_id) as total_contracts,
                SUM(valor_total) as total_value,
                AVG(valor_unitario) as avg_price
            FROM itens_arp
            WHERE item_excluido = FALSE
            AND (nome_fornecedor ILIKE :q OR cnpj_fornecedor LIKE :cnpj)
            GROUP BY cnpj_fornecedor, nome_fornecedor
            ORDER BY total_contracts DESC
            LIMIT :limit
        """)
        results = db.execute(sql, {"q": f"%{q}%", "cnpj": f"%{q}%", "limit": limit}).fetchall()
    else:
        sql = text("""
            SELECT
                cnpj_fornecedor,
                nome_fornecedor,
                COUNT(DISTINCT arp_id) as total_contracts,
                SUM(valor_total) as total_value,
                AVG(valor_unitario) as avg_price
            FROM itens_arp
            WHERE item_excluido = FALSE
            AND nome_fornecedor IS NOT NULL
            GROUP BY cnpj_fornecedor, nome_fornecedor
            ORDER BY total_contracts DESC
            LIMIT :limit
        """)
        results = db.execute(sql, {"limit": limit}).fetchall()

    return [
        {
            "cnpj": row.cnpj_fornecedor or "N/A",
            "nome": row.nome_fornecedor or "N/A",
            "total_contracts": row.total_contracts,
            "total_value": float(row.total_value) if row.total_value else 0.0,
            "avg_price": float(row.avg_price) if row.avg_price else 0.0
        }
        for row in results
    ]

@app.get("/autocomplete")
def autocomplete(
    q: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(database.get_db)
):
    """Get autocomplete suggestions for item descriptions"""

    sql = text("""
        SELECT DISTINCT descricao
        FROM itens_arp
        WHERE item_excluido = FALSE
        AND descricao ILIKE :q
        LIMIT :limit
    """)

    results = db.execute(sql, {"q": f"%{q}%", "limit": limit}).fetchall()

    return [row.descricao for row in results]

@app.get("/exportar")
def export_search(
    q: str = "",
    ufs: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=1000, ge=1, le=5000),
    db: Session = Depends(database.get_db)
):
    """Export search results to CSV"""

    # Build query (similar to /buscar but without pagination)
    where_clauses = ["arps.data_fim_vigencia >= CURRENT_DATE", "arps.ata_excluido = FALSE", "itens.item_excluido = FALSE"]
    params = {"limit": limit}

    if q and q.strip():
        where_clauses.append("itens.search_vector @@ plainto_tsquery('portuguese', :q)")
        params["q"] = q

    if ufs:
        uf_list = [uf.strip().upper() for uf in ufs.split(",")]
        uf_str = ",".join([f"'{uf}'" for uf in uf_list])
        where_clauses.append(f"orgaos.uf IN ({uf_str})")

    if min_price is not None:
        where_clauses.append("itens.valor_unitario >= :min_price")
        params["min_price"] = min_price

    if max_price is not None:
        where_clauses.append("itens.valor_unitario <= :max_price")
        params["max_price"] = max_price

    where_sql = " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            arps.numero_arp,
            orgaos.nome as orgao,
            orgaos.uf,
            itens.descricao,
            itens.valor_unitario as preco,
            itens.quantidade,
            itens.unidade,
            itens.marca,
            itens.modelo,
            itens.nome_fornecedor as fornecedor,
            arps.data_inicio_vigencia,
            arps.data_fim_vigencia
        FROM itens_arp itens
        JOIN arps ON itens.arp_id = arps.id
        JOIN orgaos ON arps.uasg_id = orgaos.uasg
        WHERE {where_sql}
        ORDER BY arps.data_fim_vigencia DESC
        LIMIT :limit
    """)

    results = db.execute(sql, params).fetchall()

    # Convert to DataFrame
    df = pd.DataFrame([dict(row._mapping) for row in results])

    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=atahub_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# ============================================================================
# ADMIN ETL ENDPOINTS
# ============================================================================

@app.get("/admin/etl/status", response_model=ETLStatusResponse)
def get_etl_status(db: Session = Depends(database.get_db)):
    """Get current or most recent ETL execution status"""
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
    """List recent ETL executions"""
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
    """List ETL errors (dead letter queue)"""
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
    """Get overall ETL statistics"""
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
