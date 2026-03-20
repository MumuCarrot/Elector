# Blockchain node tests

API and service tests for the FastAPI blockchain node (`node` package).

## Setup

```bash
cd blockchain
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# .venv/bin/pip install -r requirements.txt     # Unix
```

## Run

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

## Design

- **Database:** in-memory SQLite (`StaticPool`) per test; `async_session_maker` is patched in `node.db.database`, `node.dependencies`, and `node.services.node`.
- **Lifespan:** `router.lifespan_context(app)` wraps the client so `Node.initialize()` runs (genesis block) and the mining task is cancelled immediately after init.
- **Outbound HTTP:** `requests.get` / `requests.post` in `node.services.node` are stubbed to avoid real network calls during gossip/sync.

PostgreSQL and a running node are **not** required.
