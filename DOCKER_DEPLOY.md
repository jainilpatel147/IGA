# IGA Platform - Docker Deployment Guide

## Prerequisites

- Docker Desktop installed (Windows/Mac) or Docker Engine (Linux)
- Git (to clone the repository)
- 4GB+ RAM available for containers

---

## Quick Start (5 Steps)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/IGA.git
cd IGA
```

### 2. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your production values (IMPORTANT for security!)
# At minimum, change these:
#   - POSTGRES_PASSWORD=<strong-password>
#   - JWT_SECRET=<random-64-char-secret>
```

### 3. Build & Start Containers

```bash
# Build and start all services
docker-compose up -d --build

# Watch the logs (optional)
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# iga-postgres   running (healthy)
# iga-backend    running (healthy)
# iga-frontend   running (healthy)
```

### 5. Access the Application

| Service      | URL                          |
|--------------|------------------------------|
| **Frontend** | http://localhost:9011        |
| **Backend**  | http://localhost:8000        |
| **API Docs** | http://localhost:8000/docs   |

---

## What Happens Automatically

When you run `docker-compose up`, the backend container:

1. ✅ Waits for PostgreSQL to be ready
2. ✅ Runs all Alembic database migrations
3. ✅ Seeds sample data (Applications, Tenants, Identities)
4. ✅ Starts the FastAPI server

**No manual database setup required!**

---

## Environment Variables

| Variable            | Default         | Description                      |
|---------------------|-----------------|----------------------------------|
| `POSTGRES_USER`     | `iga`           | PostgreSQL username              |
| `POSTGRES_PASSWORD` | `iga_password`  | PostgreSQL password (CHANGE!)    |
| `POSTGRES_DB`       | `iga_db`        | Database name                    |
| `JWT_SECRET`        | `your-super...` | JWT signing key (CHANGE!)        |
| `DEBUG`             | `false`         | Enable debug logging             |

---

## Common Commands

```bash
# Stop all containers
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Enter container shell
docker-compose exec backend bash
docker-compose exec postgres psql -U iga -d iga_db

# Run migrations manually (if needed)
docker-compose exec backend alembic upgrade head

# Reseed data
docker-compose exec backend python -c "from app.seed_data import seed_multitenancy_data; seed_multitenancy_data()"
```

---

## Production Checklist

Before deploying to production:

- [ ] Change `POSTGRES_PASSWORD` to a strong password
- [ ] Change `JWT_SECRET` to a random 64+ character string
- [ ] Set `DEBUG=false`
- [ ] Configure proper SSL/TLS termination (nginx/traefik)
- [ ] Set up regular database backups
- [ ] Configure monitoring and alerting

---

## Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker-compose logs backend

# Common issues:
# - Port already in use → stop other services or change ports
# - Database connection failed → wait for postgres to be healthy
```

### Database connection errors
```bash
# Verify postgres is running
docker-compose ps postgres

# Check connectivity
docker-compose exec backend nc -zv postgres 5432
```

### Fresh start (reset everything)
```bash
docker-compose down -v
docker-compose up -d --build
```

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend      │     │   PostgreSQL    │
│   (React/Vite)  │────▶│   (FastAPI)     │────▶│   (Database)    │
│   Port: 9011    │     │   Port: 8000    │     │   Port: 5432    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
        └───── Docker Network: iga-network ─────────────┘
```
