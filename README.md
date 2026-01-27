# IGA Platform

Identity Governance & Administration Platform

## Quick Start with Docker

### Prerequisites
- Docker & Docker Compose installed

### Run with One Command

```bash
# Clone the repo
git clone https://github.com/jainilpatel147/IGA.git
cd IGA

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d
```

### Access
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Login
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | IGA Admin |
| user | user123 | Standard User |

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

---

## Development Setup (Without Docker)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Database
Requires PostgreSQL running locally on port 5432.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      IGA Platform                           │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────────┐    │
│  │ Frontend │──▶│ Backend  │──▶│      PostgreSQL      │    │
│  │  (React) │   │ (FastAPI)│   │                      │    │
│  │  :80     │   │  :8000   │   │       :5432          │    │
│  └──────────┘   └──────────┘   └──────────────────────┘    │
│                                                             │
│  Roles: admin, user                                         │
│  GRC: Registered as application with entitlements           │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| POSTGRES_USER | iga | Database user |
| POSTGRES_PASSWORD | iga_password | Database password |
| POSTGRES_DB | iga_db | Database name |
| JWT_SECRET | (set in .env) | JWT signing key |
| DEBUG | false | Enable debug mode |
