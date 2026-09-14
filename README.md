# Order Management System (OMS)

Restaurant order API: Python, FastAPI, MySQL. Same layout as five-circles-backend — routers → services → repositories → MySQL, numbered SQL migrations, and Swagger.

Interactive docs (when `DEBUG=true`):

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## Prerequisites

- **Python 3.9+** (3.12 recommended)
- **MySQL 8.0+** running locally
- **pip**

You do **not** need to create `restaurant_db` yourself. `python scripts/run_migrations.py` creates it if it is missing.

---

## Quick start

### 1. Enter the repo and create a virtualenv

```bash
cd Order-Management-System-Using-Python-
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt   # includes pytest; use requirements.txt for prod-only
```

### 3. Configure environment

A local `.env` is already in the repo root (gitignored). It uses the same MySQL host/user as five-circles-backend, with a separate database name:

| Variable | Local value |
|----------|-------------|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `3306` |
| `DB_NAME` | `restaurant_db` |
| `DB_USERNAME` | `root` |

Config is loaded from `.env` by `app/config.py`. The database user setting is **`DB_USERNAME`** (not `DB_USER`).

If you are setting this up on a new machine:

```bash
cp .env.example .env
# Set DB_PASSWORD to your local MySQL root password
```

See [Environment variables](#environment-variables) for the full list.

### 4. Run migrations

Make sure MySQL is running, then:

```bash
python scripts/run_migrations.py
```

The script is idempotent. It will:

1. Connect to MySQL (no database required yet)
2. **`CREATE DATABASE IF NOT EXISTS restaurant_db`**
3. Apply any `migrations/*.sql` file not yet recorded in `schema_migrations`
4. Seed Burger / Pizza / Coke if those rows are missing

Re-running it is safe. You do not need MySQL Workbench or a manual `CREATE DATABASE`.

| File | Purpose |
|------|---------|
| `migrations/001_initial_schema.sql` | `menu_items`, `orders`, `order_items`, foreign keys, seed menu |

If you previously ran the old one-shot `schema.sql`, this migration upgrades those tables. For a clean slate:

```sql
DROP DATABASE IF EXISTS restaurant_db;
```

then run the script again.

### 5. Run the server

Use `python -m uvicorn` so the virtualenv interpreter is used.

```bash
# Development — watch app/ only (do not watch venv)
python -m uvicorn app.main:app --reload --reload-dir app --port 8000

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On Windows, a bare `--reload` watches the whole folder, including `venv`. Pip or MySQL-connector files then trigger a reload loop (`CancelledError` / `KeyboardInterrupt` in the lifespan). `--reload-dir app` avoids that. Prefer a local disk over OneDrive (`...\OneDrive\Desktop\OMS`).

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

---

## Try an order

In Swagger, open **Orders → POST /api/v1/orders → Try it out**, or send:

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Rahul","items":[{"menu_item_id":1,"quantity":2}]}'
```

Burger × 2 at ₹100 → `total_price: 200`, status `PLACED`, stock `10 → 8`.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Liveness |
| `GET` | `/health` | Pool health (`healthy` / `degraded`) |
| `GET` | `/api/v1/menu` | List catalog |
| `GET` | `/api/v1/menu/{id}` | One menu item |
| `POST` | `/api/v1/orders` | Place an order (`201`) |
| `GET` | `/api/v1/orders` | Paginated order list |
| `GET` | `/api/v1/orders/{id}` | One order + lines |

Errors use a flat body: `{ "detail": "Not enough stock" }`.

---

## Environment variables

See `.env.example` for a copy-paste template. Names must match `app/config.py`.

### Required

| Variable | Description |
|----------|-------------|
| `DB_HOST` | MySQL host |
| `DB_NAME` | Database name (`restaurant_db`) |
| `DB_USERNAME` | Database user |
| `DB_PASSWORD` | Database password |

### Optional (defaults from `app/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PORT` | `3306` | MySQL port |
| `DB_POOL_NAME` | `restaurant_oms_pool` | Pool name |
| `DB_POOL_SIZE` | `5` | Pool size |
| `DB_CONNECTION_TIMEOUT` | `20` | Connect timeout (seconds) |
| `DB_POOL_LOG_CONNECTIONS` | `false` | Log borrow/return |
| `ALLOW_DB_FAILURE` | `false` | Allow process start if DB is down |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8080` | Comma-separated origins |
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `DEBUG` | `true` | Enables `/docs` and `/redoc` |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Tests

```bash
pytest
```

- Layer import guards (`tests/test_architecture.py`)
- Swagger / OpenAPI paths and tags
- `OrderService` with constructor-injected fakes (no MySQL)

---

## Architecture

```
Presentation (app/api/, app/middleware/)
        ↓
Service (app/services/) — business rules, HTTPException
        ↓
Repository (app/repositories/) — parameterized SQL, dicts / None
        ↓
Data (MySQL via connection pool)
```

| Layer | Lives in | Must not do |
|-------|----------|-------------|
| Presentation | `app/api/` | Import repositories or write SQL |
| Service | `app/services/` | Contain SQL |
| Repository | `app/repositories/` | Raise `HTTPException` |

```text
Order-Management-System-Using-Python-/
├── .env.example
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/v1/
│   ├── services/
│   ├── repositories/
│   └── models/
├── migrations/001_initial_schema.sql
├── scripts/run_migrations.py
└── tests/
```

Compared with five-circles-backend: same FastAPI + `.env` + SQL migrations + pool + layered folders. This project does not include JWT, Twilio, or rate limiting.

## Troubleshooting

**`CancelledError` / `KeyboardInterrupt` in the lifespan, plus `WatchFiles detected changes in 'venv\...'`**

The app started fine (`Database pool ... initialized`). Uvicorn `--reload` then watched `venv` and killed the worker on every pip/package file touch. This is common on Windows, and worse if the project lives under OneDrive.

```bash
# Stop the looping server (Ctrl+C), then:
python -m uvicorn app.main:app --reload --reload-dir app --port 8000
```

Or skip reload: `python -m uvicorn app.main:app --port 8000`.

## Author

**Om Gupta** (original OMS). Setup and architecture aligned with five-circles-backend.
