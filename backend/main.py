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
