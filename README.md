# AtaHub Carona

Uma aplicação SaaS para buscar e comparar Atas de Registro de Preços (ARPs) do governo brasileiro.

## Visão Geral

O AtaHub Carona ajuda órgãos governamentais e fornecedores a encontrar os melhores preços para produtos e serviços através da busca em contratos de compras registrados. A aplicação oferece um poderoso motor de busca com capacidades de busca textual completa em português.

## Funcionalidades

- 🔍 **Busca textual completa** para itens de compras usando busca avançada do PostgreSQL
- 📊 **Comparação de preços** entre diferentes órgãos governamentais
- 🏢 **Filtro por organização** por estado e órgão
- 📅 **Rastreamento de vigência** para mostrar apenas contratos ativos
- 🐳 **Pronto para Docker** para fácil implantação

## Stack Tecnológica

### Backend
- **FastAPI** - Framework web Python moderno
- **PostgreSQL 15** - Banco de dados com extensões de busca textual completa
- **SQLAlchemy** - ORM para operações de banco de dados
- **Uvicorn** - Servidor ASGI

### Frontend
- **Next.js 16** - Framework React com Turbopack
- **Tailwind CSS v4** - Framework CSS utilitário
- **TypeScript** - JavaScript com tipagem segura
- **Shadcn UI** - Biblioteca de componentes

### Infraestrutura
- **Docker & Docker Compose** - Containerização
- **Extensões PostgreSQL** - uuid-ossp, unaccent para processamento de texto

## Começando

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/SEU_USUARIO/atahub_carona.git
cd atahub_carona
```

2. Inicie a aplicação com Docker:
```bash
docker-compose up -d
```

3. Acesse a aplicação:
- **Frontend**: http://localhost:3002
- **API Backend**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs

### Serviços

A aplicação consiste em três serviços Docker:

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Frontend | 3002 | Aplicação web Next.js |
| Backend | 8000 | API REST FastAPI |
| Database | 5433 | Banco de dados PostgreSQL 15 |

## Estrutura do Projeto

```
atahub_carona/
├── backend/              # Backend FastAPI
│   ├── main.py          # Endpoints da API
│   ├── models.py        # Modelos do banco de dados
│   ├── database.py      # Configuração do banco de dados
│   ├── requirements.txt # Dependências Python
│   └── Dockerfile       # Configuração do container backend
├── frontend/            # Frontend Next.js
│   ├── src/
│   │   └── app/        # Diretório app do Next.js
│   ├── package.json    # Dependências Node
│   └── Dockerfile      # Configuração do container frontend
├── etl/                # Scripts de ingestão de dados
│   └── ingestor.py     # Pipeline ETL para dados de ARP
├── docker-compose.yml  # Orquestração Docker
└── init_extensions.sql # Extensões PostgreSQL
```

## Endpoints da API

### Buscar Itens
```
GET /buscar?q={termo_busca}
```

Busca itens de compras usando busca textual completa.

**Parâmetros:**
- `q` (string): Consulta de busca em português

**Resposta:**
```json
[
  {
    "id_arp": "uuid",
    "numero_arp": "string",
    "orgao_nome": "string",
    "uf": "string",
    "vigencia_fim": "date",
    "item": {
      "descricao": "string",
      "valor_unitario": 0.0,
      "marca": "string",
      "quantidade": 0.0
    }
  }
]
```

### Verificação de Saúde
```
GET /
```

Retorna o status da API.

## Desenvolvimento

### Executando Localmente (sem Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Banco de Dados:**
Certifique-se de que o PostgreSQL está rodando na porta 5433 com o banco de dados `govcompras`.

### Variáveis de Ambiente

**Backend:**
- `DATABASE_URL` - String de conexão PostgreSQL (padrão: `postgresql://postgres:password@localhost:5433/govcompras`)

**Frontend:**
- `NEXT_PUBLIC_API_URL` - URL da API backend (padrão: `http://localhost:8000`)

## Comandos Docker

### Iniciar todos os serviços
```bash
docker-compose up -d
```

### Visualizar logs
```bash
docker-compose logs -f
```

### Parar todos os serviços
```bash
docker-compose down
```

### Reconstruir containers
```bash
docker-compose up --build -d
```

### Reiniciar um serviço específico
```bash
docker-compose restart frontend
docker-compose restart backend
```

## Schema do Banco de Dados

### Tabelas

- **orgaos** - Órgãos governamentais (UASG)
- **arps** - Atas de Registro de Preços
- **itens_arp** - Itens em cada ARP com vetor de busca textual completa

### Recursos Principais

- Busca textual completa usando `tsvector` e `tsquery` do PostgreSQL
- Suporte ao idioma português com extensão `unaccent`
- Índice GIN para busca textual rápida
- Chaves primárias UUID

## Ingestão de Dados

Para popular o banco de dados com dados de ARP, use o ingestor ETL:

```bash
cd etl
python ingestor.py
```

## Como Tornar o Repositório Privado

Para tornar este repositório privado no GitHub:

1. Acesse o repositório no GitHub
2. Clique em **Settings** (Configurações)
3. Role até a seção **Danger Zone** (Zona de Perigo) no final da página
4. Clique em **Change visibility** (Alterar visibilidade)
5. Selecione **Make private** (Tornar privado)
6. Confirme digitando o nome do repositório e clique em **I understand, change repository visibility**

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para enviar um Pull Request.

## Licença

Este projeto está licenciado sob a Licença MIT.

## Contato

Para perguntas ou suporte, por favor abra uma issue no GitHub.

---

**Nota:** Esta aplicação foi projetada para dados de compras governamentais brasileiras. A funcionalidade de busca utiliza processamento de linguagem em português.
