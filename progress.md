# SmartCart — Build Progress

> Updated every session by Claude Code. Read this before writing any code.
> Legend: ✅ Done | 🔄 In Progress | ⏳ Not Started | ❌ Blocked

---

## 🔖 Next Session Starts Here
**Task:** Backend — Auth (POST /v1/auth/send-otp, POST /v1/auth/verify-otp, JWT auth dependency, GET /v1/config)
**Module:** api (Backend — Auth)
**Notes:** Backend — Core is done: app factory, config, database, redis, all models, and the initial
Alembic migration are in place and verified (see Decisions Log for how). `app/core/security.py`,
`app/services/auth_service.py`, and `app/routers/auth.py`/`config.py` still only have empty/typed
stubs — that's this session's work. `app/routers/config.py` needs a real GET /v1/config handler
backed by the `Config` singleton row (id=1) — see api/CLAUDE.md → App Config Endpoint.
Router files already declare `router = APIRouter(prefix=...)` and are mounted in `app/main.py` —
just add the actual path operations, don't re-wire the app factory.
Environment: Python 3.11.9 is now installed locally (see Blockers/Decisions Log, 2026-08-31).
Run everything through `api/.venv` (`.venv/Scripts/python.exe`, `.venv/Scripts/pytest.exe`, etc.) —
Docker is only needed for `docker compose up` itself now, not for running pytest/mypy/ruff.
Never `pip install` into the global Python.
A fixes session (2026-08-31) landed after Core: CORS is now env-driven (`CORS_ORIGINS`),
Receipt/ReceiptLineItem have minimum-viable columns (still R2-empty otherwise), `Base.metadata`
has a naming_convention (all future FK/UQ/CK/PK/IX get deterministic names), `api/Dockerfile`
+ `.dockerignore` exist, and root `.env`/`.gitignore` were fixed. Full details in Decisions Log.

---

## MVP — Month 1 (Build This Now)

### Infrastructure
- ✅ Project scaffold (folders, placeholder files)
- ✅ docker-compose.yml (postgres + redis + api only — no MinIO/Celery in MVP)
- ✅ .env.example with MVP-only variables (see CLAUDE.md §4)
- ✅ GitHub Actions CI: pytest + mypy + ruff on push

### Backend — Core
- ✅ FastAPI app factory (app/main.py, CORS, exception handlers)
- ✅ Pydantic Settings config (app/core/config.py)
- ✅ Async SQLAlchemy engine + session factory (app/core/database.py)
- ✅ Redis connection pool — OTP only (app/core/redis.py)
- ✅ SQLAlchemy models: User, ShoppingSession, SessionItem, Product, StorePrice, Store, Config
- ✅ NOTE: Also create Receipt + ReceiptLineItem models (empty, for R2) — see CLAUDE.md §3
- ✅ Alembic initial migration

### Backend — Auth
- ⏳ POST /v1/auth/send-otp (Twilio Verify, rate limit 3/hour)
- ⏳ POST /v1/auth/verify-otp (lockout after 3 fails, JWT + refresh token)
- ⏳ JWT auth dependency (middleware for protected routes)
- ⏳ GET /v1/config (min_app_version, force_update, maintenance_mode)

### Backend — Products (MVP: Open Food Facts only)
- ⏳ GET /v1/products/{barcode} (DB → Open Food Facts → manual fallback)
- ⏳ Open Food Facts API client (app/services/open_food_facts.py)
- ⏳ Price sanity check validator
- ⏳ POST /v1/products (manual product creation from "not found" flow)

### Backend — Sessions
- ⏳ POST /v1/sessions (store_id nullable, store_name_text for MVP)
- ⏳ GET /v1/sessions/{id}
- ⏳ POST /v1/sessions/{id}/items (optimistic total update)
- ⏳ PATCH /v1/sessions/{id}/items/{item_id} (update qty)
- ⏳ DELETE /v1/sessions/{id}/items/{item_id}
- ⏳ POST /v1/sessions/{id}/finish
- ⏳ GET /v1/history (paginated)

### Backend — MVP Stubs (implement properly in R2)
- ⏳ POST /v1/receipts → return 501 Not Implemented
- ⏳ GET /v1/receipts/{id} → return 501 Not Implemented
- ⏳ DELETE /v1/account → return 501 Not Implemented (implement in R2)

### Backend — Tests
- ⏳ conftest.py fixtures (test_user, test_store, test_product, active_session)
- ⏳ Unit: OTP flow (hashing, expiry, lockout)
- ⏳ Unit: barcode waterfall (DB → Open Food Facts → manual)
- ⏳ Integration: auth endpoints
- ⏳ Integration: session CRUD
- ⏳ Integration: product lookup

### Mobile — Foundation
- ⏳ Expo project init (EAS managed, TypeScript, NativeWind v4)
- ⏳ Expo Router v3 layout (auth group, tabs group, session routes)
- ⏳ app.json + eas.json (permissions, bundle IDs, build profiles)
- ⏳ SafeAreaProvider + StatusBar in root layout
- ⏳ services/api.ts (axios, JWT injection, 401 handler, 8s timeout)
- ⏳ expo-secure-store JWT storage
- ⏳ Zustand: authStore, sessionStore (with AsyncStorage persist), uiStore
- ⏳ NetInfo offline listener + OfflineBanner component
- ⏳ App version check on launch (GET /v1/config + semver)

### Mobile — Auth Screens
- ⏳ login.tsx (phone input, +91 prefix, E.164 format)
- ⏳ otp.tsx (6-digit input, 30s resend cooldown, lockout UI)

### Mobile — Core Screens
- ⏳ index.tsx (home: crash recovery resume prompt, recent sessions)
- ⏳ scan.tsx (CameraView barcode scanner, live bill, budget bar)
- ⏳ history.tsx (paginated past sessions)
- ⏳ session/[id].tsx (item list, qty controls, finish button + ConfirmSheet)

### Mobile — Components
- ⏳ BudgetBar.tsx (green/amber/red progress bar)
- ⏳ PriceTag.tsx (price display — no confidence label in MVP, just "~₹X")
- ⏳ OfflineBanner.tsx (persistent banner when offline)
- ⏳ SessionItem.tsx (scanned item row with qty controls)
- ⏳ ConfirmSheet.tsx (bottom sheet for "Finish Shopping" confirmation)

### Mobile — Utilities
- ⏳ utils/format.ts (paise → ₹ display)
- ⏳ utils/semver.ts (version comparison)

### MVP Ship
- ⏳ EAS preview build (Android APK + iOS)
- ⏳ TestFlight setup (iOS internal testing)
- ⏳ Play Store internal track (Android)
- ⏳ 10–20 beta testers recruited in Bengaluru

---

## R2 — Month 2–3 (Do Not Start Until MVP Ships)
- ⏳ Celery + Redis job queue setup
- ⏳ MinIO local + AWS S3 production
- ⏳ POST /v1/receipts (real implementation — S3 upload + queue OCR task)
- ⏳ GET /v1/receipts/{id} (OCR status + line items)
- ⏳ PATCH /v1/receipts/{id}/items/{item_id} (manual correction)
- ⏳ Celery worker: receipt_ocr (Google Vision + rapidfuzz)
- ⏳ Celery worker: price_decay (nightly)
- ⏳ DELETE /v1/account (DPDP hard delete)
- ⏳ session/[id]/receipt.tsx (OCR comparison + correction UI)
- ⏳ Push notifications (expo-notifications)
- ⏳ PostHog analytics (replace console logs)
- ⏳ Sentry error monitoring
- ⏳ Price confidence scoring UI (PriceTag labels: "estimated", "rough estimate")
- ⏳ Privacy policy page + Play Store / App Store data safety forms

## R3 — Month 4–5 (Do Not Start Until R2 Ships)
- ⏳ Store discovery (PostGIS nearby query + GPS)
- ⏳ Store selection at session start
- ⏳ Price comparison across stores
- ⏳ "Cheapest store for your list" feature
- ⏳ Barcodelookup.com secondary API
- ⏳ expo-sqlite offline product cache
- ⏳ Full offline sync queue with idempotency keys
- ⏳ Price confidence decay (Celery Beat nightly)

## R4 — Month 6–7 (Do Not Start Until R3 Ships)
- ⏳ Shared shopping lists
- ⏳ Collaborative sessions
- ⏳ Household budget tracking
- ⏳ Recurring items / "my usual shop"
- ⏳ Export as PDF / WhatsApp share

## R5 — Month 8–10 (Do Not Start Until R4 Ships)
- ⏳ FMCG brand campaigns
- ⏳ Retailer SaaS dashboard
- ⏳ Loyalty program integration

## R6 — Month 10–12 (Do Not Start Until R5 Ships)
- ⏳ LangGraph AI shopping assistant
- ⏳ Smart substitutions
- ⏳ Spend pattern insights
- ⏳ Price alerts
- ⏳ Voice input / ARIA integration

---

## Decisions Log
| Date | Decision | Reason |
|------|----------|--------|
| 2026-08-30 | Scaffold placeholder files are import + type stubs only (empty classes, `...` bodies, no columns/fields/route logic) | Keeps this session inside "Project scaffold" scope without pre-building work that progress.md tracks as separate tasks (models, config, routes, etc.) |
| 2026-08-30 | api/app/models/receipt.py and receipt_line_item.py created empty now (R2 feature) | Required by CLAUDE.md §3 "Three Things to Build Right in MVP" to avoid a painful retrofit migration later |
| 2026-08-30 | api/app/workers/ has no files yet, only `__init__.py` | Celery workers are explicitly out of scope for MVP (api/CLAUDE.md "Do Not Build in MVP") |
| 2026-08-30 | mobile/services/ has only api.ts (no analytics.ts, localCache.ts, syncQueue.ts) | Those are R2/R3 per mobile/CLAUDE.md "Do Not Build in MVP" |
| 2026-08-30 | Added api/requirements.txt and api/pyproject.toml (pytest/mypy/ruff config) — not an itemized task but required to actually run "pytest + mypy + ruff" | No local Python on this machine at all; verification runs in Docker containers instead |
| 2026-08-30 | All model primary keys are UUID (client-side `uuid.uuid4` default) except `Config`, which keeps `id` as a plain Integer fixed at 1 | Repo/service stubs from the scaffold session already typed session/user ids as `str`, and api/CLAUDE.md says the Config table is a literal single row with `id=1`, always UPDATE never INSERT |
| 2026-08-30 | mypy config: added `plugins = ["pydantic.mypy"]` and `disable_error_code = ["empty-body"]` in api/pyproject.toml | Without the pydantic plugin, mypy doesn't understand `BaseSettings` fields come from env at runtime and flags `Settings()` as missing constructor args. `empty-body` false-positives on every intentionally-stubbed `...` function across the codebase (Auth/session files this session didn't touch) — mypy does NOT exempt these the way .pyi stub files are exempt, contrary to what the scaffold session assumed |
| 2026-08-30 | main.py's global exception handler is registered on `starlette.exceptions.HTTPException`, not `fastapi.HTTPException` | Bug found via a live TestClient check: Starlette's router raises its own base `HTTPException` directly for framework-level errors (404/405), which sits *above* `fastapi.HTTPException` in the MRO — a handler registered on the FastAPI subclass silently misses those and leaks Starlette's default `{"detail": ...}` shape instead of the standard `{"error": {...}}` shape |
| 2026-08-30 | Alembic migration was generated with `alembic revision --autogenerate` against a real throwaway Postgres in Docker (not hand-written), then applied with `alembic upgrade head` to confirm it's correct | Docker was available even though local Python wasn't; autogenerate + upgrade against a live DB is much higher-confidence than hand-writing `op.create_table` calls blind |
| 2026-08-31 | .github/workflows/ci.yml: added an "alembic upgrade head" step between dependency install and pytest | Tests need the schema to actually exist against the Postgres service container — migrations must run first |
| 2026-08-31 | .github/workflows/ci.yml: scoped `on: push` / `on: pull_request` to `branches: [main]` | CI was triggering on every push to every branch; only main pushes and PRs into main should run it |
| 2026-08-31 | Installed Python 3.11.9 per-user via the official python.org installer (`/InstallAllUsers=0`), not Chocolatey | `choco install python311` failed — this machine's Chocolatey install requires admin elevation (writes to `C:\ProgramData\chocolatey\lib`), and there's no way to elevate from this session. The per-user installer needs no admin rights. |
| 2026-08-31 | Added shims at `C:\Users\josep\.local\bin\python3.11` / `pip3.11` (`.cmd` + extensionless script pair) instead of relying on the installer's PATH update | The installer updates the registry `PATH`, but this session's shell processes inherited their environment before that change and won't see it until a full session restart. `.local\bin` was already on the inherited PATH for both PowerShell and Git Bash, so shims there resolve immediately without a restart. **Future sessions: if a fresh shell already has the real PATH, these shims are redundant but harmless; if not, they're what makes `python3.11`/`pip3.11` work.** |
| 2026-08-31 | **Project dependencies live in `api/.venv`, not the global Python 3.11 install** — created via `python3.11 -m venv .venv`, installed via `.venv/Scripts/pip.exe install -r requirements.txt` | Running `pip3.11 install -r requirements.txt` globally (as literally instructed) downgraded `fastapi`/`pydantic-settings`/`httpx` in the pre-existing global Python 3.11 environment (which already had `langchain`/`chromadb`/other tools installed), breaking their dependency resolution. Restored the global packages via `pip3.11 install --upgrade fastapi pydantic-settings httpx pydantic`, then moved SmartCart's deps into an isolated venv so this can't happen again. **Every future backend session must activate/use `api/.venv`, never install into the global Python.** |
| 2026-08-31 | CORS is now env-driven: `Settings.CORS_ORIGINS` (comma-separated, default `http://localhost:8081,http://localhost:19006`), `main.py` reads `settings.cors_origins_list` instead of `allow_origins=["*"]` | `["*"]` is unsafe once real user data is involved; defaults cover local Expo dev (web :8081, Metro :19006) so nothing breaks day-to-day, but production must set real origins via env |
| 2026-08-31 | Receipt/ReceiptLineItem got minimum-viable columns: `Receipt.session_id` (nullable FK), `ocr_status` (default "pending"), `created_at`; `ReceiptLineItem.receipt_id` (FK, indexed), `created_at`. Still no OCR/business fields — those land when R2 is actually built | So the R2 migration adding real columns isn't confusing (a table that already has *some* real shape, not just a bare `id`) — see CLAUDE.md §3 |
| 2026-08-31 | mypy `disable_error_code = ["empty-body"]` in api/pyproject.toml now has an explicit removal note: "Remove this once all stub functions across the codebase are implemented — tracked in progress.md Decisions Log" | This was item 3 of the 2026-08-31 fixes session, skipped when the session paused to plan the Dockerfile/Alembic issues below — completing it now. **Target: revisit in Session 6, once all backend stubs (routers/services/repositories) have real implementations — see progress.md task list for what's still ⏳.** |
| 2026-08-31 | Added `api/Dockerfile` (python:3.11-slim, pip install requirements.txt, `uvicorn app.main:app --host 0.0.0.0 --port 8000`) and `api/.dockerignore` (.venv/, caches, .env, .git/) | `docker-compose.yml`'s `api` service has referenced `build: ./api` since the very first scaffold session, but no Dockerfile ever existed — `docker compose up --build` was silently guaranteed to fail. Discovered while executing the fixes-session's verification step. Not itemized as a task anywhere; added because it's required for the stack to build at all. |
| 2026-08-31 | Created root `.env` (gitignored, dev-only dummy values) using **Compose service names** (`postgres`, `redis`) as hostnames in `DATABASE_URL`/`REDIS_URL`, not `localhost` | `docker-compose.yml`'s `api` service has `env_file: .env`, which Compose requires to exist — without it `docker compose up --build` hard-fails with "env file .env not found". Inside the `api` container, `localhost` resolves to the container itself, not sibling containers, so it must use the Compose network's service-name DNS instead. (This is different from the `localhost`-based `DATABASE_URL`/`REDIS_URL` used for host-side `api/.venv` commands — those two contexts need different values.) |
| 2026-08-31 | Fixed root `.gitignore`: removed a literal `cat > .gitignore << 'EOF'` / `EOF` heredoc wrapper that had been committed as file content instead of executed, and removed `CLAUDE.md`, `progress.md`, `.gitignore`, `.env.example` from the ignore list | The heredoc syntax still "worked" line-by-line as gitignore patterns (harmless but nonsensical), but ignoring `CLAUDE.md`/`progress.md`/`.env.example`/`.gitignore` itself was a real bug — those are meant to be tracked. **Side finding: this bug meant none of those files (root and module `CLAUDE.md`s, `progress.md`, `.env.example`) were ever actually committed** — confirmed via `git status` showing them all as untracked (`??`) once the ignore rule was removed. Not committed by this session — flagging for you to decide when to `git add` them. |
| 2026-08-31 | Added a `naming_convention` dict to `Base.metadata` in `app/models/base.py` (SQLAlchemy's own documented recommended convention: `ix`/`uq`/`ck`/`fk`/`pk` patterns) | Root cause of the Alembic bug below — without it, `ForeignKey(...)` columns get unnamed constraints, so Alembic's autogenerated `downgrade()` (which calls `op.drop_constraint(name, ...)`) has no name to pass. Fixes it for every future migration that adds a FK to an existing table, not just this one. Verified the convention doesn't cause spurious rename-diffs for migration 1's pre-existing indexes (its simple single-column index names already match the convention's output) via a no-op `alembic revision --autogenerate` cross-check. |
| 2026-08-31 | Hand-edited migration `0aa7d9ccca1a` in place (same revision id) to give its two FK constraints explicit names (`fk_receipt_line_items_receipt_id_receipts`, `fk_receipts_session_id_shopping_sessions`) instead of deleting and regenerating with a new revision hash | The migration was already pushed to `origin/main`; regenerating would orphan the old revision id in anyone/anything that already saw it. The schema shape isn't changing — only two `op.create_foreign_key(None, ...)`/`op.drop_constraint(None, ...)` pairs needed real names (the indexes already used `op.f(...)` correctly and didn't need touching). CI is unaffected: it only ever runs `alembic upgrade head` against a fresh ephemeral Postgres per run, never `downgrade`, and the revision/down_revision chain didn't change. |
| 2026-08-31 | Full verification passed after all of the above: `docker compose down -v` → fresh `postgres`/`redis` → `alembic upgrade head` → `alembic downgrade -1` (previously failed, now succeeds) → `alembic upgrade head` (round-trip confirmed) → `alembic revision --autogenerate` no-op cross-check (confirmed naming convention exactly matches hand-picked names, throwaway file deleted) → `pytest`/`mypy`/`ruff` all clean → `docker compose up --build` (all 3 containers `Up`, api logs clean, `GET /docs` → 200, `GET /v1/nonexistent` → standard error shape) → `docker compose down` | Confirms both the Dockerfile and the Alembic fix work end-to-end, not just in isolation |

## Blockers Log
| Date | Blocker | Status |
|------|---------|--------|
| 2026-08-30 | No Python (or pip) installed on this machine — `pytest`/`mypy`/`ruff` can't run natively | ✅ Resolved 2026-08-31: Python 3.11.9 installed per-user (see Decisions Log). Verification now runs natively via `api/.venv` instead of Docker containers. |
