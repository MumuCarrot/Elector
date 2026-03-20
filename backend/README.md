# Election Backend

FastAPI service for **Elector**: user accounts, JWT authentication (access/refresh), elections and candidates, voting, and integration with the blockchain node for persisting votes. Data layer uses **PostgreSQL** (async SQLAlchemy / asyncpg) and **Redis** (e.g. token blacklist). API base path: **`/api/v1`** (OpenAPI UI: `/docs`).

## Requirements

- **Python** 3.11+ (3.12 recommended; matches the Docker image)
- **PostgreSQL** and **Redis** reachable from the machine running the API
- **pip** (virtual environment recommended)

## Install dependencies

From this directory (`backend/`):

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the sample and edit values (database, Redis, JWT RS256 PEM keys, logging, CORS, blockchain URL):

```powershell
copy .env.sample .env
```

On macOS/Linux: `cp .env.sample .env`

- For **local** runs with Postgres and Redis on the same machine, use `DEPLOY_MODE=LOCAL` (default) so `POSTGRES_HOST_LOCAL` and `REDIS_HOST_LOCAL` are used.
- For **Docker Compose**, set `DEPLOY_MODE=DOCKER` and align hosts with service names from `docker-compose.yaml` (`db`, `redis`).
- Point **`BLOCKCHAIN_HOST`** / **`BLOCKCHAIN_PORT`** at your blockchain node if it is not `http://localhost:5000`.

See `app/core/settings.py` for all options and defaults.

## Database migrations

With PostgreSQL running and credentials matching `.env`:

```bash
alembic upgrade head
```

## Run the API (local)

From `backend/`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or without reload:

```bash
python -m app.main
```

The listen host/port follow `APP_HOST` / `APP_PORT` when using `python -m app.main` (see settings).

## Run with Docker Compose

Ensure `.env` satisfies `docker-compose.yaml` (Postgres, Redis, `APP_PORT`, `DEPLOY_MODE=DOCKER`, JWT keys, etc.):

```bash
docker compose up --build
```

The API container runs `alembic upgrade head` then starts the app via `start.sh`.

## Tests

```bash
pytest
```

## Project layout (overview)

| Path | Role |
| ---- | ---- |
| `app/main.py` | FastAPI app, CORS, routers |
| `app/routers/` | HTTP routes |
| `app/services/` | Business logic |
| `app/repository/` | Data access |
| `migrations/` | Alembic revisions |
| `tests/` | Pytest suite |
