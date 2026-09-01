# CLAUDE.md — SmartCart API (Backend Context)

> Load this when working inside /api. Supplements root CLAUDE.md.
> Root CLAUDE.md has the full engineering rules, domain model, error states,
> and confidence scoring logic. Read it first if you haven't.
>
> **Session start checklist:**
> 1. Read `progress.md` (repo root) — confirm the task for this session
> 2. Read root `CLAUDE.md`
> 3. Read this file
> 4. State the task out loud and wait for Reuben to confirm before writing code
> 5. On session end — update `progress.md`, mark done ✅, set next task

---

## Module Focus
FastAPI backend. **Currently building MVP** — see CLAUDE.md §2 for what is
and isn't in scope. R2+ features (OCR, S3, Celery, account deletion) are
stubbed as 501s, not built.

---

## MVP vs R2+ — What to Build Now

### Build in MVP
- Auth (OTP, JWT)
- GET /v1/config
- GET /v1/products/{barcode} (DB → Open Food Facts → manual only — no Barcodelookup.com)
- POST /v1/products (manual creation)
- Full session CRUD
- GET /v1/history

### Stub as 501 in MVP (implement in R2)
```python
# These routes must EXIST but return 501 — mobile client is written against them now
POST /v1/receipts           → 501 Not Implemented
GET  /v1/receipts/{id}      → 501 Not Implemented
PATCH /v1/receipts/{id}/items/{item_id}  → 501 Not Implemented
DELETE /v1/account          → 501 Not Implemented
GET /v1/stores/nearby       → 501 Not Implemented (R3)
```

### Do Not Build in MVP (add in correct release)
- Celery workers (R2)
- S3 / MinIO integration (R2)
- Barcodelookup.com client (R3)
- PostGIS store discovery (R3)
- Price confidence decay job (R3)
- Offline sync queue flush endpoint (R3)

---

## Local Dev Infrastructure — No External Accounts Needed

All services run in Docker Compose locally. Never configure Claude Code to
call real AWS or Upstash during development — always use the local equivalents.

| Service | Local (dev) | Production |
|---|---|---|
| Redis | `redis://localhost:6379` (Docker) | Upstash URL via `REDIS_URL` env var |
| S3 | MinIO at `http://localhost:9000` (Docker) | AWS S3 — remove `AWS_S3_ENDPOINT_URL` from env |
| PostgreSQL | `localhost:5432` (Docker) | RDS or managed Postgres |

### S3 Client Pattern (`app/core/storage.py`)
The same `boto3` client works for both MinIO (dev) and AWS S3 (prod).
Swap is done via environment variables only — zero code changes:

```python
import boto3
from app.core.config import settings

def get_s3_client():
    kwargs = {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION,
    }
    # AWS_S3_ENDPOINT_URL is set in dev only (points to MinIO)
    # In production this key is absent → boto3 hits real AWS automatically
    if settings.AWS_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)
```

### MinIO Notes (Local Dev)
- MinIO web console: `http://localhost:9001` — browse and inspect uploaded receipts
- MinIO credentials in dev: user=`smartcart_local`, password=`smartcart_local`
- Create the bucket on first run: `smartcart-receipts` (do this in console or via boto3 on startup)
- Pre-signed URLs work identically in MinIO and S3 — test them locally with confidence

### Redis Notes
- Local: standard Redis, no auth — `REDIS_URL=redis://localhost:6379`
- Production (Upstash): TLS URL — `REDIS_URL=rediss://:password@host.upstash.io:6380`
- The `rediss://` prefix (double-s) enables TLS — make sure your Redis client respects it
- Celery broker and backend both read from `REDIS_URL` — one variable, no duplication

---

## Key Files — Read Before Touching Anything
- `app/core/config.py` — all env vars via Pydantic Settings. Single source of truth for config.
- `app/core/database.py` — async SQLAlchemy engine + session factory
- `app/core/redis.py` — Redis connection pool (OTP storage, price cache, sync queue)
- `app/core/security.py` — JWT creation/verification, OTP hashing, lockout logic
- `app/models/` — SQLAlchemy ORM models (source of truth for DB schema)
- `app/schemas/` — Pydantic schemas (source of truth for API contract)

---

## Service Layer — Mandatory Flow
```
router → service → repository → DB
```
- Routers: validate input schema, call one service method, return response schema
- Services: all business logic lives here. Call repositories. Never touch DB directly.
- Repositories: all DB queries live here. No business logic. Return ORM objects or None.

Example — adding a session item:
```
POST /v1/sessions/{id}/items
  → routers/sessions.py        validates SessionItemCreate schema
  → services/session_service.py  checks session is active, computes optimistic total
  → repositories/session_repo.py  upserts SessionItem, returns updated session
  → routers/sessions.py        returns SessionResponse schema
```

---

## All Routes Are Versioned `/v1/`

```
# Auth
POST   /v1/auth/send-otp
POST   /v1/auth/verify-otp        → JWT access token + refresh token

# Config (force update, maintenance mode)
GET    /v1/config                  → min_app_version, force_update, maintenance_mode

# Stores
GET    /v1/stores/nearby           → ?lat=&lng=&radius_km=

# Products (barcode lookup waterfall — see root CLAUDE.md §6)
GET    /v1/products/{barcode}      → product + price + confidence_score + source
POST   /v1/products                → manual product creation (from "not found" flow)

# Sessions
POST   /v1/sessions
GET    /v1/sessions/{id}
POST   /v1/sessions/{id}/items
PATCH  /v1/sessions/{id}/items/{item_id}
DELETE /v1/sessions/{id}/items/{item_id}
POST   /v1/sessions/{id}/finish

# Receipts
POST   /v1/receipts                → multipart upload, returns receipt_id immediately
GET    /v1/receipts/{id}           → ocr_status + matched/unmatched line items
PATCH  /v1/receipts/{id}/items/{item_id}  → user manual correction of OCR match

# History
GET    /v1/history                 → paginated past sessions

# Account (DPDP compliance — hard delete everything)
DELETE /v1/account                 → deletes User + all Sessions + Receipts + LineItems
```

---

## Barcode Lookup Waterfall (Implement in `services/product_service.py`)

```python
async def lookup_product(barcode: str, store_id: int) -> ProductLookupResult:
    # 1. PostgreSQL StorePrice — crowd-sourced Indian product data
    result = await product_repo.get_by_barcode_and_store(barcode, store_id)
    if result and result.confidence_score > 0.20:
        return result  # source: 'db'

    # 2. Open Food Facts API
    off_result = await open_food_facts_client.lookup(barcode)
    if off_result:
        await product_repo.upsert_price(barcode, store_id, off_result, confidence=0.30)
        return off_result  # source: 'open_food_facts'

    # 3. Barcodelookup.com (rate-limited fallback)
    bcl_result = await barcodelookup_client.lookup(barcode)
    if bcl_result:
        await product_repo.upsert_price(barcode, store_id, bcl_result, confidence=0.25)
        return bcl_result  # source: 'barcodelookup'

    # 4. Not found — return None, mobile handles "Product not found" flow
    return None
```

Price sanity check before any upsert:
```python
def is_price_sane(price_paise: int, existing_price_paise: int | None) -> bool:
    if price_paise <= 0 or price_paise > 5_000_000:  # > ₹50,000
        return False
    if existing_price_paise and price_paise > existing_price_paise * 3:
        return False  # flag — more than 3× existing price
    return True
```

---

## OTP & Auth Flow

```python
# Send OTP
# 1. Rate check: max 3 OTP requests per phone per hour (Redis counter)
# 2. Twilio Verify → sends SMS
# 3. Store in Redis: key=f"otp:{phone}", value=hashed_otp, TTL=600s

# Verify OTP
# 1. Fetch from Redis — if missing, it's expired → return 401 "Code expired"
# 2. Check attempt counter: if >= 3 → return 429 "Too many attempts, try in 1 hour"
# 3. Compare hashed input to stored hash
# 4. If match: delete Redis key, issue JWT + refresh token, return 200
# 5. If no match: increment attempt counter, return 401 "Incorrect code"

# JWT payload
{"sub": str(user_id), "phone": phone_e164, "exp": now + 24h, "type": "access"}
# Refresh token payload
{"sub": str(user_id), "exp": now + 30d, "type": "refresh"}
```

---

## App Config Endpoint (Force Update + Maintenance)

```python
# GET /v1/config — no auth required
# Returns:
{
    "min_app_version": "1.0.0",   # semver — app blocks if below this
    "latest_version": "1.0.0",
    "force_update": False,
    "maintenance_mode": False,
    "maintenance_message": None
}
# Store these values in a Config table (single row) — editable without redeployment
```

---

## Celery Workers

### `workers/receipt_ocr.py`
```
Task: process_receipt(receipt_id)
1. Fetch Receipt from DB, download image from S3
2. Submit to Google Vision API (DOCUMENT_TEXT_DETECTION)
3. Parse line items using rapidfuzz fuzzy matching (threshold: 80%)
4. Strip Indian receipt abbreviations: MRP, GST, CGST, SGST, QTY, PCS, KG
5. For each line item: fuzzy match → Product table → store ReceiptLineItem
6. Update Receipt.ocr_status = 'completed' | 'partial' | 'failed'
7. Upsert StorePrice for all matched products (confidence 0.95 same store)
8. Delete S3 image (DPDP compliance — retain extracted data, not the image)
9. Send push notification: "Your receipt is ready!"
Retry: max_retries=3, countdown=[5, 25, 125] seconds
```

### `workers/price_decay.py`
```
Task: decay_stale_prices()  — runs nightly via Celery Beat
For all StorePrice where last_seen > 30 days ago:
    new_score = max(0.10, confidence_score - (0.05 * (days_old - 30) / 7))
Batch update in chunks of 1000 rows — never a single massive UPDATE
```

### `workers/sync_queue.py`
```
Task: flush_offline_sync_queue(user_id)
Called when mobile app reports connectivity restored
Processes queued offline writes in order (FIFO)
Idempotent — safe to run multiple times (use client-generated idempotency keys)
```

---

## Error Response Format — Always This Shape

```python
# All errors must use this structure — no exceptions
{
    "error": {
        "code": "OTP_EXPIRED",          # machine-readable, SCREAMING_SNAKE_CASE
        "message": "Code expired — request a new one",  # human-readable
        "details": {}                   # optional extra context
    }
}

# Standard error codes for Phase 1:
OTP_EXPIRED | OTP_INVALID | OTP_LOCKED_OUT | OTP_RATE_LIMITED
SESSION_NOT_FOUND | SESSION_ALREADY_FINISHED | SESSION_ALREADY_ACTIVE
PRODUCT_NOT_FOUND | PRICE_REJECTED (sanity check failed)
RECEIPT_OCR_FAILED | RECEIPT_NOT_FOUND
ACCOUNT_NOT_FOUND | UNAUTHORIZED | FORBIDDEN
MAINTENANCE_MODE
```

---

## Database Rules

- All schema changes via Alembic — never `Base.metadata.create_all()` in production
- Required indexes:
  - `product.barcode` (unique)
  - `store_price.(product_id, store_id)` (composite unique)
  - `shopping_session.user_id`
  - `shopping_session.status` (for active session lookup)
  - `store.location` (PostGIS GIST index)
  - `receipt.session_id`
- `StorePrice` updates are always upserts — never blind inserts
- Config table has a single row with `id=1` — always UPDATE, never INSERT

---

## Test Structure

```
tests/
├── conftest.py          — async DB session, auth headers, test client, fixtures
├── unit/
│   ├── test_price_confidence.py   — decay formula, sanity checks
│   ├── test_otp_flow.py           — hashing, expiry, lockout logic
│   ├── test_barcode_waterfall.py  — lookup priority with mocked clients
│   └── test_receipt_matching.py   — fuzzy matching, Indian abbreviations
└── integration/
    ├── test_auth.py               — full OTP flow via httpx AsyncClient
    ├── test_sessions.py           — create, add items, finish
    ├── test_products.py           — barcode lookup, manual create
    └── test_receipts.py           — upload, OCR status polling
```

Fixtures to always have in `conftest.py`:
- `test_user` — a verified user with valid JWT
- `test_store` — a Bengaluru store with location
- `test_product` — a product with barcode + StorePrice
- `active_session` — an open ShoppingSession for test_user at test_store
