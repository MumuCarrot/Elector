# Blockchain node

FastAPI service that implements a **proof-of-work blockchain** for storing **votes** (election, voter, candidate). Nodes keep a **PostgreSQL**-backed chain, share **mempool** transactions and **peer lists** over HTTP, and **mine** blocks on the app’s asyncio loop. Optional REST routes expose chain inspection, gossip, and read-only vote queries (`/api/...`).

## Requirements

- **Python** 3.11+ (3.12+ recommended)
- **PostgreSQL** reachable from the machine running the node
- **pip** (virtual environment recommended)

## Install dependencies

From this directory (`blockchain/`), create a venv and install packages:

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Settings are read from **environment variables** and from an optional **`node/.env`** file (paths are relative to the current working directory when you start the app—use `blockchain/` as cwd).

Copy the example to `node/.env` for **local** runs (settings load `node/.env` relative to the `blockchain/` working directory):

```bash
copy .env.example node\.env
```

On macOS/Linux: `cp .env.example node/.env`

For **Docker Compose**, create a `.env` file in the **`blockchain/`** project root (same folder as `docker-compose.yaml`). Compose injects those variables into the node container and uses them for the bundled PostgreSQL service. Set database credentials and `APP_PORT` there; the compose file sets **`DEPLOY_MODE=DOCKER`** and **`POSTGRES_HOST_PROD=db`** for the node so it reaches the `db` service.

Important variables:

| Variable | Purpose |
| -------- | ------- |
| `APP_HOST` / `APP_PORT` | API bind address and port |
| `MAIN_NODE_HOST` / `MAIN_NODE_PORT` | Seed node for peer registration |
| `PROOF_OF_WORK_DIFFICULTY` | Hash prefix difficulty (e.g. `0000`) |
| `POSTGRES_*` / `DEPLOY_MODE` | Database connection (`LOCAL` vs `DOCKER` host) |

See `node/core/settings.py` for the full list and defaults.

## Database migrations

With PostgreSQL running and credentials matching your config, apply schema from the **`blockchain/`** root:

```bash
alembic upgrade head
```

## Run the API server

Always run commands from the **`blockchain/`** directory so imports resolve (`node` package).

**Option A — Uvicorn (fixed port):**

```bash
uvicorn node.main:app --host 0.0.0.0 --port 5000
```

**Option B — Development script (auto free port + reload):**

```bash
python node/run.py
```

The app exposes routers under prefixes such as `/health`, `/blockchain`, `/api`, `/nodes`, and `/gossip` (see `node/main.py`).

## Run with Docker Compose

From **`blockchain/`**, add a root **`.env`** (see `.env.example`) with at least `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `APP_PORT` (optional; default `5000`). Then:

```bash
docker compose up --build
```

This starts:

- **`node`** — the blockchain API; runs `alembic upgrade head` then **Uvicorn**. The service receives **`DEPLOY_MODE=DOCKER`** and **`POSTGRES_HOST_PROD=db`** from the compose file (in addition to variables from `.env`).
- **`db`** — **PostgreSQL 15** with a dedicated volume (`blockchain_pg_data`) for this node’s chain data.

To run a **second** node with its own database, use a separate compose project or copy the folder and change the project name, ports, and volume name so containers and data do not clash.

## Run tests

```bash
pytest
```

For a single run without watch mode (CI-style):

```bash
pytest -q
```

Tests use **httpx** against the ASGI app and **SQLite** in memory (see `tests/conftest.py`); they do not require PostgreSQL.

## Project layout (overview)

| Path | Role |
| ---- | ---- |
| `node/main.py` | FastAPI app and lifespan (node + mining task) |
| `node/run.py` | Dev entrypoint with port discovery |
| `node/services/node.py` | Chain logic, mining, sync/gossip |
| `node/repositories/` | SQLAlchemy data access |
| `migrations/` | Alembic revisions |
| `tests/` | Pytest suite |
| `Dockerfile` / `docker-compose.yaml` / `start.sh` | Container image and one-node + PostgreSQL stack |
