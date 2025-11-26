# Master Plan: SaaS GovCompras.ai

Este documento serve como a "Verdade Única" para a implementação do SaaS. Siga estritamente a estrutura de pastas e as dependências listadas.

## 1. Visão Geral da Arquitetura

O sistema é um monorepo (ou estrutura unificada) dividido em:
1.  **Database:** PostgreSQL com extensões para busca textual.
2.  **ETL:** Script Python autônomo para ingestão de dados.
3.  **Backend:** API FastAPI (Python) que consome o banco.
4.  **Frontend:** Next.js (App Router) com Tailwind e Shadcn UI.
5.  **Auth:** Clerk (Gerenciado no Frontend e validado no Backend).

## 2. Estrutura de Diretórios Esperada

O agente deve criar a seguinte estrutura:

```text
/govcompras-saas
├── /backend
│   ├── main.py            # Entrypoint da API
│   ├── database.py        # Conexão SQLAlchemy
│   ├── models.py          # Tabelas ORM
│   ├── schemas.py         # Serialização Pydantic
│   ├── auth.py            # Validação do Token Clerk
│   └── requirements.txt
├── /etl
│   ├── ingestor.py        # Script de carga de dados
│   └── requirements.txt
├── /frontend
│   ├── src/app/...        # App Router Next.js
│   ├── src/components/... # Shadcn UI
│   ├── .env.local         # Chaves do Clerk
│   └── middleware.ts      # Proteção de rotas Clerk
├── docker-compose.yml     # Banco de Dados PostgreSQL
└── README.md
```

---

## 3. Fase 1: Infraestrutura (Database)

**Arquivo:** `docker-compose.yml`
**Instrução:** Crie este arquivo na raiz para subir o banco localmente.

```yaml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    container_name: govcompras_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: govcompras
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Arquivo:** `backend/init_db.sql` (Opcional, mas o SQLAlchemy criará as tabelas. As extensões precisam ser ativadas manualmente ou via migration).

**Atenção:** O agente deve garantir que as extensões `uuid-ossp` e `unaccent` estejam ativas no banco.
Comando SQL manual: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; CREATE EXTENSION IF NOT EXISTS "unaccent";`

---

## 4. Fase 2: Backend (FastAPI)

**Dependências:** `backend/requirements.txt`
```text
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic
python-jose[cryptography]
python-multipart
requests
```

**Arquivo:** `backend/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexão (ajustar senha conforme docker-compose)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5433/govcompras"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Arquivo:** `backend/models.py`
```python
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
```

**Arquivo:** `backend/auth.py`
```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Valida o token JWT vindo do Clerk.
    Para ambiente DEV, extraímos o 'sub' (User ID) sem verificar assinatura RS256 complexa.
    Em PROD, deve-se usar as chaves JWKS do Clerk.
    """
    token = credentials.credentials
    try:
        payload = jwt.get_unverified_claims(token)
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
```

**Arquivo:** `backend/main.py`
```python
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
import models, database, auth

# Inicializar Banco
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Configurar CORS (Frontend roda na porta 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas (Pydantic) ---
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
    user_id: str = Depends(auth.get_current_user), # Rota Protegida
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
```

---

## 5. Fase 3: ETL (Ingestão de Dados)

**Dependências:** `etl/requirements.txt`
```text
requests
psycopg2-binary
```

**Arquivo:** `etl/ingestor.py`
**Instrução:** Este script deve rodar periodicamente.

```python
import requests
import psycopg2
from datetime import datetime

# Conexão DB (Hardcoded para dev, usar env vars em prod)
DB_CONN = "postgresql://postgres:password@localhost:5433/govcompras"

def run_etl():
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()

    # 1. Configurar Busca na API do Governo
    url = "https://dadosabertos.compras.gov.br/modulo-arp/11_consultar_arp"
    params = {
        "data_inicio_vigencia": "2024-01-01",
        "data_fim_vigencia": "2024-12-31",
        "pagina": 1
    }

    print("Buscando dados...")
    resp = requests.get(url, params=params)
    data = resp.json().get('resultado', [])

    for row in data:
        # Salvar Órgão
        orgao = row.get('orgaoGerenciador', {})
        cur.execute("""
            INSERT INTO orgaos (uasg, nome, uf) VALUES (%s, %s, %s)
            ON CONFLICT (uasg) DO UPDATE SET nome = EXCLUDED.nome
        """, (str(orgao.get('codigo')), orgao.get('nome'), orgao.get('siglaUf')))

        # Salvar ARP
        cur.execute("""
            INSERT INTO arps (codigo_arp_api, numero_arp, uasg_id, data_inicio_vigencia, data_fim_vigencia, objeto)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo_arp_api) DO NOTHING
            RETURNING id
        """, (
            str(row.get('codigoArp')), row.get('numeroArp'), str(orgao.get('codigo')),
            row.get('dataInicioVigencia'), row.get('dataFimVigencia'), row.get('objeto')
        ))

        arp_id = cur.fetchone()

        # Se arp_id é None, a ARP já existia e não retornou ID.
        # Em produção, faríamos um SELECT para pegar o ID.
        if arp_id:
            # Busca Itens (Nested Request)
            arp_uuid = arp_id[0]
            print(f"Processando itens da ARP {row.get('numeroArp')}...")

            try:
                itens_resp = requests.get(
                    "https://dadosabertos.compras.gov.br/modulo-arp/11_consultar_itens_arp",
                    params={"codigo_arp": row.get('codigoArp')}
                )
                itens = itens_resp.json().get('resultado', [])

                for item in itens:
                    # Preparar vetor de busca (descrição + marca)
                    # Nota: O Postgres preenche o TSVECTOR via Trigger ou Update,
                    # mas aqui inserimos os dados brutos.
                    cur.execute("""
                        INSERT INTO itens_arp (arp_id, numero_item, descricao, valor_unitario, quantidade, unidade, marca, search_vector)
                        VALUES (%s, %s, %s, %s, %s, %s, %s,
                        setweight(to_tsvector('portuguese', %s), 'A') || setweight(to_tsvector('portuguese', %s), 'B'))
                    """, (
                        arp_uuid, item.get('numeroItem'), item.get('descricaoItem'),
                        item.get('valorUnitarioHomologado'), item.get('quantidadeHomologada'),
                        item.get('unidadeMedida'), item.get('marca'),
                        item.get('descricaoItem'), item.get('marca') or ''
                    ))
            except Exception as e:
                print(f"Erro nos itens: {e}")

        conn.commit()

    conn.close()
    print("ETL Finalizado.")

if __name__ == "__main__":
    run_etl()
```

---

## 6. Fase 4: Frontend (Next.js + Clerk)

**Setup:**
1.  `npx create-next-app@latest frontend --typescript --tailwind --eslint`
2.  `cd frontend`
3.  `npm install @clerk/nextjs lucide-react`
4.  `npx shadcn-ui@latest init` (Default settings)
5.  `npx shadcn-ui@latest add button input card badge skeleton`

**Arquivo:** `frontend/.env.local`
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_SUA_CHAVE_AQUI
CLERK_SECRET_KEY=sk_test_SUA_CHAVE_AQUI
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
```

**Arquivo:** `frontend/src/middleware.ts`
```typescript
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  '/busca(.*)',
  '/dashboard(.*)'
]);

export default clerkMiddleware((auth, req) => {
  if (isProtectedRoute(req)) auth().protect();
});

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
};
```

**Arquivo:** `frontend/src/app/layout.tsx` (Adicionar Provider)
```tsx
import { ClerkProvider } from '@clerk/nextjs'
// ... imports padrão

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="pt-BR">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}
```

**Arquivo:** `frontend/src/app/busca/page.tsx`
```tsx
'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Tipagem
interface SearchResult {
  id_arp: string;
  numero_arp: string;
  orgao_nome: string;
  uf: string;
  vigencia_fim: string;
  item: {
    descricao: string;
    valor_unitario: number;
    marca: string;
  }
}

export default function BuscaPage() {
  const { getToken } = useAuth()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if(!query) return;
    setLoading(true);
    try {
      const token = await getToken();
      const res = await fetch(`http://localhost:8000/buscar?q=${query}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if(res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch(err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Busca de Atas (Carona)</h1>

      <div className="flex gap-4 mb-8">
        <Input
          placeholder="Ex: Notebook i7, Cadeira Giratória..."
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? "Buscando..." : "Buscar"}
        </Button>
      </div>

      <div className="grid gap-4">
        {results.map((res) => (
          <Card key={`${res.id_arp}-${res.item.descricao}`} className="hover:shadow-md transition">
            <CardHeader className="pb-2">
              <div className="flex justify-between">
                <Badge variant="outline">{res.uf}</Badge>
                <span className="text-xs text-muted-foreground">Vence em: {res.vigencia_fim}</span>
              </div>
              <CardTitle className="text-lg leading-tight">{res.item.descricao}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-end mt-2">
                <div>
                  <p className="text-sm text-muted-foreground">{res.orgao_nome}</p>
                  <p className="text-sm font-medium">Marca: {res.item.marca || "N/A"}</p>
                </div>
                <div className="text-xl font-bold text-green-700">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(res.item.valor_unitario)}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

**Arquivo:** `frontend/src/app/page.tsx` (Landing Page com Login)
**Instrução:** Substitua o conteúdo padrão por este, que gerencia o estado de autenticação.

```tsx
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs"
import { ArrowRight, ShieldCheck } from "lucide-react"

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="px-6 h-16 flex items-center border-b justify-between">
        <div className="font-bold text-xl flex items-center gap-2">
          <ShieldCheck className="text-blue-600" />
          GovCompras.ai
        </div>
        <nav>
          <SignedOut>
            <SignInButton mode="modal">
              <Button>Entrar</Button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <div className="flex items-center gap-4">
              <Link href="/busca">
                <Button variant="ghost">Ir para Busca</Button>
              </Link>
              <UserButton />
            </div>
          </SignedIn>
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-slate-50">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6">
          Encontre Oportunidades de <br/>
          <span className="text-blue-600">Carona em Atas</span>
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mb-8">
          Monitore Diários Oficiais, compare preços e encontre Atas de Registro de Preços
          vigentes para vender mais ou comprar melhor.
        </p>

        <div className="flex gap-4">
          <SignedOut>
            <SignInButton mode="modal">
              <Button size="lg" className="gap-2">
                Criar Conta Grátis <ArrowRight size={16} />
              </Button>
            </SignInButton>
          </SignedOut>

          <SignedIn>
            <Link href="/busca">
              <Button size="lg" className="gap-2">
                Acessar Painel <ArrowRight size={16} />
              </Button>
            </Link>
          </SignedIn>
        </div>
      </main>
    </div>
  )
}
```

---

## 7. Instruções de Execução (Runbook para o Agente)

O Agente deve seguir esta ordem exata para garantir que o sistema funcione:

1.  **Infraestrutura:**
    *   Executar `docker-compose up -d` na raiz.
    *   Verificar se o Postgres está rodando na porta 5432.

2.  **ETL (Carga de Dados):**
    *   Criar ambiente virtual: `python -m venv venv`.
    *   Instalar dependências: `pip install -r etl/requirements.txt`.
    *   Executar `python etl/ingestor.py`.
    *   *Esperar o script finalizar e confirmar que há dados no banco.*

3.  **Backend:**
    *   Instalar dependências: `pip install -r backend/requirements.txt`.
    *   Executar na pasta backend: `uvicorn main:app --reload --port 8000`.
    *   Testar acesso em: `http://localhost:8000/docs`.

4.  **Frontend:**
    *   Garantir que o arquivo `.env.local` esteja preenchido com as chaves do Clerk.
    *   Instalar pacotes: `npm install`.
    *   Executar: `npm run dev -- -p 3001`.
    *   Acessar: `http://localhost:3001`.

## 8. Definição de Pronto (Done)

O projeto será considerado concluído quando:
1.  O usuário conseguir logar via Clerk na Home.
2.  Ao acessar `/busca`, visualizar a barra de pesquisa.
3.  Ao digitar um termo (ex: "cafe" ou "cadeira") e buscar, o Frontend apresentar cards com dados vindos do banco PostgreSQL.
4.  O Backend validar o Token JWT enviado pelo Frontend.
