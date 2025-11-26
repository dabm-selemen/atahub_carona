# AtaHub Carona

A SaaS application for searching and comparing government procurement registration forms (ARPs - Atas de Registro de Preços) in Brazil.

## Overview

AtaHub Carona helps government agencies and suppliers find the best prices for products and services by searching through registered procurement contracts. The application provides a powerful search engine with full-text search capabilities in Portuguese.

## Features

- 🔍 **Full-text search** for procurement items using PostgreSQL's advanced text search
- 📊 **Price comparison** across different government agencies
- 🏢 **Organization filtering** by state and agency
- 📅 **Validity tracking** to show only active contracts
- 🐳 **Docker-ready** for easy deployment

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL 15** - Database with full-text search extensions
- **SQLAlchemy** - ORM for database operations
- **Uvicorn** - ASGI server

### Frontend
- **Next.js 16** - React framework with Turbopack
- **Tailwind CSS v4** - Utility-first CSS framework
- **TypeScript** - Type-safe JavaScript
- **Shadcn UI** - Component library

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **PostgreSQL Extensions** - uuid-ossp, unaccent for text processing

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/atahub_carona.git
cd atahub_carona
```

2. Start the application with Docker:
```bash
docker-compose up -d
```

3. Access the application:
- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Services

The application consists of three Docker services:

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3002 | Next.js web application |
| Backend | 8000 | FastAPI REST API |
| Database | 5433 | PostgreSQL 15 database |

## Project Structure

```
atahub_carona/
├── backend/              # FastAPI backend
│   ├── main.py          # API endpoints
│   ├── models.py        # Database models
│   ├── database.py      # Database configuration
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile       # Backend container config
├── frontend/            # Next.js frontend
│   ├── src/
│   │   └── app/        # Next.js app directory
│   ├── package.json    # Node dependencies
│   └── Dockerfile      # Frontend container config
├── etl/                # Data ingestion scripts
│   └── ingestor.py     # ETL pipeline for ARP data
├── docker-compose.yml  # Docker orchestration
└── init_extensions.sql # PostgreSQL extensions
```

## API Endpoints

### Search Items
```
GET /buscar?q={search_term}
```

Search for procurement items using full-text search.

**Parameters:**
- `q` (string): Search query in Portuguese

**Response:**
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

### Health Check
```
GET /
```

Returns API status.

## Development

### Running Locally (without Docker)

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

**Database:**
Make sure PostgreSQL is running on port 5433 with the database `govcompras`.

### Environment Variables

**Backend:**
- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://postgres:password@localhost:5433/govcompras`)

**Frontend:**
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Docker Commands

### Start all services
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop all services
```bash
docker-compose down
```

### Rebuild containers
```bash
docker-compose up --build -d
```

### Restart a specific service
```bash
docker-compose restart frontend
docker-compose restart backend
```

## Database Schema

### Tables

- **orgaos** - Government agencies (UASG)
- **arps** - Procurement registration forms
- **itens_arp** - Items in each ARP with full-text search vector

### Key Features

- Full-text search using PostgreSQL's `tsvector` and `tsquery`
- Portuguese language support with `unaccent` extension
- GIN index for fast text search
- UUID primary keys

## Data Ingestion

To populate the database with ARP data, use the ETL ingestor:

```bash
cd etl
python ingestor.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please open an issue on GitHub.

---

**Note:** This application is designed for Brazilian government procurement data. The search functionality uses Portuguese language processing.
