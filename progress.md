# SmartCart — Build Progress

> Updated every session by Claude Code. Read this before writing any code.
> Legend: ✅ Done | 🔄 In Progress | ⏳ Not Started | ❌ Blocked

---

## 🔖 Next Session Starts Here
**Task:** Mobile — Core Screens: `index.tsx` (home: crash recovery resume prompt, recent
sessions), `scan.tsx` (CameraView barcode scanner + live bill + budget bar), `history.tsx`
(paginated past sessions), `session/[id].tsx` (item list, qty controls, finish button +
ConfirmSheet). Auth Screens are done and the login→otp→tabs flow is wired end to end.
**Module:** mobile (Mobile — Core Screens)
**Notes:** Mobile — Auth Screens shipped this session. `app/(auth)/login.tsx` (phone entry, +91
prefix hardcoded, E.164 validation via a 10-digit regex before enabling submit) and
`app/(auth)/otp.tsx` (single 6-digit `TextInput` — not 6 separate boxes, mobile/CLAUDE.md's spec
just says "6-digit input" and doesn't mandate segmented boxes; auto-submits once 6 digits are
typed; 30s resend cooldown timer; locks the input on `OTP_LOCKED_OUT`) are both real now, wired to
a new `services/authService.ts` (`sendOtp`/`verifyOtp` + `getApiErrorCode`/`getApiErrorMessage`
helpers that unwrap the backend's `{error: {code, message, details}}` shape) and to
`useAuthStore.login()`. All four backend OTP error codes from `api/app/services/auth_service.py`
are handled with the exact user-facing copy root CLAUDE.md §10 specifies: `OTP_RATE_LIMITED`,
`OTP_EXPIRED`, `OTP_INVALID`, `OTP_LOCKED_OUT`. Console-logged the root CLAUDE.md §11 Phase-1 auth
analytics events (`otp_requested`, `login_success`, `login_failed` with reason) per mobile/CLAUDE.md's
explicit "PostHog wrapper is R2 — use console.log in MVP" instruction — no `services/analytics.ts`
wrapper file was created, these are plain `console.log` calls inline.
**Real gap found and fixed (not itemized anywhere, but blocking):** `authStore` only ever held
auth state in memory — the JWT itself was correctly persisted to `expo-secure-store` by the
Foundation session, but nothing ever read it back on app relaunch, so every cold start would have
forced a full OTP re-login even with a still-valid stored token. Added `authStore.hydrate()`
(reads the stored access token, decodes it, checks `exp` client-side before trusting it) called
once from `app/_layout.tsx` on mount, plus a redirect effect there that sends the user to `/login`
or `/` once hydration resolves. **There is no `/v1/auth/refresh` endpoint in the backend at all**
(api/CLAUDE.md's auth routes are send-otp/verify-otp only) — an expired 24h access token just means
a full OTP re-login, same fallback path as `api.ts`'s existing 401 interceptor. Not treated as a
gap to fix — there's nothing to refresh against yet.
**Known minor gap, not fixed:** there's a brief flash of whatever route Expo Router picks as
default before the hydration redirect effect fires (SecureStore read + JWT decode, typically well
under 100ms.) Fixing this properly means wiring `expo-splash-screen`'s
`preventAutoHideAsync`/`hideAsync` to hold the native splash until hydration resolves — out of
scope for this session, flagging for whoever next touches `app/_layout.tsx`.
**Verification:** `npx tsc --noEmit` clean, `npx expo export --platform android` bundled all 1698
modules successfully. Still no emulator/device/simulator available in this environment — the
actual login→OTP→home flow has never been run or visually confirmed, only type-checked and
bundled.

---

## Prior Session Notes (Mobile — Foundation, 2026-09-12)
Mobile — Foundation shipped. `mobile/` had no `package.json` at all before
today — the existing `.tsx`/`.ts` files were type-only stubs from the original scaffold session,
not a real Expo project. Node v24.0.1/npm 11.3.0 were already on the machine.
**How the project was actually initialized:** rather than hand-writing `package.json`/config from
memory, `npx create-expo-app@latest` was run once into a throwaway scratchpad dir purely to see
what current (Expo SDK 57 — well past this model's training data) dependency versions and config
actually look like, then `mobile/package.json`/`tsconfig.json`/`babel.config.js`/`metro.config.js`
were hand-written to match, and `npm install` run for real inside `mobile/`. The existing stub file
tree (`app/(auth)/`, `app/(tabs)/`, `app/session/[id].tsx`, etc.) was left untouched — nothing was
scaffolded over it.
**Dependency resolution — expect this graph if touching package.json again:** `nativewind@4.2.6`
peer-requires `tailwindcss` `>3.3.0` but its own runtime (`react-native-css-interop`) only actually
works with Tailwind **v3** (v4 is a different architecture) — pinned `tailwindcss: ^3.4.19`, not
latest. `react-native-css-interop`'s babel preset also unconditionally requires
`react-native-worklets` to exist (even though we don't use Reanimated animations ourselves) — this
cascaded into needing `react-native-reanimated` too (css-interop peer-requires it `>=3.6.2`).
Landed on `react-native-reanimated@4.5.1` + `react-native-worklets@0.10.1` + `react-dom@19.2.3`
(pinned explicitly to stop npm's peer resolution pulling in latest `react-dom@19.3.0`, which
demands `react@^19.3.0` and conflicts with what RN 0.86.3/Expo SDK 57 actually want) — this exact
combination is what `npx expo-doctor` reports as **18/18 checks passed, no issues**, so don't
"fix" these versions upward without re-running `expo-doctor` after. `npx expo install --fix` is
useful for future dependency bumps but doesn't know about nativewind's extra requirements — it
downgraded reanimated/worklets to versions that then failed peer resolution against
`react-native-css-interop`; had to manually re-pin.
**`global.d.ts` (new, committed, not gitignored):** `@types/react@19.x` moved the `JSX` namespace
from a global ambient namespace to `React.JSX`, which broke `JSX.Element` return-type annotations
in literally every existing stub file (`app/**/*.tsx`, `components/**/*.tsx`) — all written before
this namespace change existed. Fixed once, project-wide, via the officially-documented shim
(`declare global { namespace JSX { interface Element extends React.JSX.Element {} ... } }`)
instead of touching every stub file's return type. `npx tsc --noEmit` is clean project-wide as of
this session.
**app.json deviates from root CLAUDE.md §22's literal example** — dropped the `expo-notifications`
plugin and `NSPhotoLibraryUsageDescription` (receipt upload photo access): both are R2 features
(push notifications, receipt upload) that root CLAUDE.md §2 explicitly excludes from MVP, and
§21's rule is "if a future-release feature is tempting to add now... move on" rather than
half-wire it. Also dropped `icon`/`splash`/`adaptiveIcon` image references since no real brand
assets exist yet — whoever picks up "MVP Ship → EAS preview build" will need real icon/splash
files before `eas build` will succeed.
**`utils/semver.ts` was implemented this session** (not left for the separate "Mobile —
Utilities" task) since the app version check task directly needs it — thin wrapper around the
real `semver` npm package, not hand-rolled comparison. `utils/format.ts` (paise → ₹) was left
untouched/stubbed — nothing in Foundation needed it.
**Verification performed:** `npx tsc --noEmit` clean, `npx expo-doctor` 18/18, and
`npx expo export --platform android` successfully bundled all 1696 modules (confirms
babel.config.js + metro.config.js + NativeWind + expo-router + every new store/service file
actually resolve and compile together) — `--platform web` was NOT tested (`react-native-web` isn't
installed; web is not a target platform per root CLAUDE.md's tech stack, Android/iOS via EAS
only). No physical device, emulator, or simulator is available in this environment, so the app was
never actually run/visually verified — only that it type-checks and bundles cleanly.
**Also new this session:** root `.gitignore`'s Node/Expo section got `web-build/`, `expo-env.d.ts`,
`*.tsbuildinfo`, `.metro-health-check*`, `.kotlin/`, `/mobile/ios/`, `/mobile/android/` added —
these didn't exist before because there was no real Expo project to generate them.
`mobile/expo-env.d.ts` exists on disk (needed for `EXPO_PUBLIC_*` env var typing) but is
intentionally gitignored per Expo's own convention (tooling regenerates it) — don't add it to git.
`mobile/.env.local` (gitignored, `EXPO_PUBLIC_API_URL=http://localhost:8000`) was created so
`npx expo start` actually has an API URL to hit — without it every request's `baseURL` is
`undefined`.

---

## Prior Session Notes (Backend — MVP Stubs, 2026-09-11)
Backend — MVP Stubs shipped: `POST /v1/receipts`, `GET /v1/receipts/{id}`,
`PATCH /v1/receipts/{id}/items/{item_id}`, and `DELETE /v1/account` all return a real, auth-gated
501 `NOT_IMPLEMENTED` response now (previously these routers had zero path operations). All were
verified live via `docker compose up --build` + curl (401→403 without a token per FastAPI's
`HTTPBearer` behavior, 501 with a token) and have 6 new integration tests (45/45 total passing).
With this, every MVP-scope backend route from api/CLAUDE.md §All Routes is implemented: Auth,
Config, Products, Sessions, History, and these stubs. The only thing left on the backend side is
`tests/conftest.py`'s still-stubbed `test_user`/`test_store`/`test_product`/`active_session`
fixtures — deliberately left ⏳, since every integration test file so far builds its own data
through the real API instead and that's worked fine across 5 test files now; pick it up only if a
future backend session actually wants shared fixtures, not as a blocking task. `stores.py` is also
still a bare router with no routes at all (not even a 501) — that's R3 scope per api/CLAUDE.md's
stub table (`GET /v1/stores/nearby → 501 (R3)` is tagged separately from the MVP stub set), not
part of MVP, so intentionally untouched.
Environment: Python 3.11.9 is installed locally. Run everything through `api/.venv`
(`.venv/Scripts/python.exe`, `.venv/Scripts/pytest.exe`, etc.) — Docker is only needed for
`docker compose up` itself, not for running pytest/mypy/ruff. Never `pip install` into the global
Python. `api/.env` (localhost DB/Redis URLs, gitignored) exists for host-side venv runs — don't
recreate it. Docker Desktop is not always running at session start; if `docker ps`/`docker compose
up` hangs or fails with a pipe-connect error, launch `C:\Program Files\Docker\Docker\Docker
Desktop.exe` and wait (can take 1-2 min) before retrying — do not run `alembic upgrade head` (or
anything DB-dependent) in the background while a migration file is still being edited, see
Decisions Log 2026-09-10 for why. Running pytest from `api/` needs `PYTHONPATH=.` explicitly set
(`PYTHONPATH=. .venv/Scripts/pytest.exe tests/ -v`) — there's no `tests/__init__.py` and no
`pythonpath` entry in `pyproject.toml`'s pytest config, so plain `pytest` fails with
`ModuleNotFoundError: No module named 'app'`. `docker-compose.yml`'s `postgres` service now has a
named volume (`postgres_data`) — without it, Postgres data lived in an anonymous volume that
`docker compose down` (even without `-v`) was silently wiping every time, forcing a fresh
`alembic upgrade head` after every single `down`/`up` cycle. Confirmed fixed: schema now survives a
`down` → `up` cycle. This doesn't affect CI (fresh container per run either way).

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
- ✅ POST /v1/auth/send-otp (rate limit 3/hour via Redis; dev/mock OTP path — logs the code
  instead of calling Twilio, see Decisions Log — no Twilio account exists yet)
- ✅ POST /v1/auth/verify-otp (lockout after 3 fails/1h, JWT access + refresh token)
- ✅ JWT auth dependency (`get_current_user_id` in `app/core/security.py` — not yet used by
  any route since no MVP route needs auth *yet*, but ready for Sessions/History)
- ✅ GET /v1/config (min_app_version, force_update, maintenance_mode — backed by seeded
  `Config` row id=1, see Decisions Log)
- ✅ Unit tests: OTP hashing/rate-limit/lockout (`tests/unit/test_otp_flow.py`), JWT
  creation/decoding + auth dependency (`tests/unit/test_jwt.py`)
- ✅ Integration tests: full OTP login flow, invalid phone, wrong code, expired code
  (`tests/integration/test_auth.py`), GET /v1/config (`tests/integration/test_config.py`)

### Backend — Products (MVP: Open Food Facts only)
- ✅ GET /v1/products/{barcode} (DB → Open Food Facts → manual fallback; see Decisions Log for
  a deliberate deviation from the literal CLAUDE.md pseudocode — OFF has no price data, so a
  low-confidence local price is kept rather than discarded when OFF only supplies product identity)
- ✅ Open Food Facts API client (app/services/open_food_facts.py) — verified live against the
  real API (Nutella barcode 3017620422003), never called from the automated test suite (always
  mocked/stubbed there to avoid network flakiness)
- ✅ Price sanity check validator (`is_price_sane` in app/services/product_service.py)
- ✅ POST /v1/products (manual product creation from "not found" flow, confidence 0.20, source
  'manual')
- ✅ Unit tests: waterfall priority with a fake OFF client, price sanity boundaries
  (`tests/unit/test_barcode_waterfall.py`)
- ✅ Integration tests: manual create + lookup, price rejection, 404 not-found
  (`tests/integration/test_products.py`)

### Backend — Sessions
- ✅ POST /v1/sessions (store_id nullable/unused in MVP, store_name_text required; enforces the
  one-active-session-per-user invariant with 409 SESSION_ALREADY_ACTIVE)
- ✅ GET /v1/sessions/{id} (ownership-checked — 403 FORBIDDEN if the session belongs to another
  user, 404 SESSION_NOT_FOUND if it doesn't exist)
- ✅ POST /v1/sessions/{id}/items (barcode → full product waterfall via `ProductService.
  find_product_and_price`, computes running `estimated_total_paise`; 409 SESSION_ALREADY_FINISHED
  if the session isn't active, 404 PRODUCT_NOT_FOUND if the barcode resolves to nothing)
- ✅ PATCH /v1/sessions/{id}/items/{item_id} (update qty, recomputes total)
- ✅ DELETE /v1/sessions/{id}/items/{item_id} (returns the updated session, not 204 — mobile can
  just re-render from the response like every other session mutation)
- ✅ POST /v1/sessions/{id}/finish
- ✅ GET /v1/history (paginated, `limit`/`offset` query params, includes item_count +
  estimated_total_paise per session)
- ✅ Integration tests: create/add-item/total math, duplicate-active-session 409, quantity update +
  delete, unknown-barcode 404, finish + reject-further-mutation, history listing, auth-required 403,
  nonexistent-session 404 (`tests/integration/test_sessions.py`, 8 tests, all via the real OTP flow
  like `test_auth.py` — no fixture stubs used, see Decisions Log)

### Backend — MVP Stubs (implement properly in R2)
- ✅ POST /v1/receipts → returns 501 NOT_IMPLEMENTED (auth-gated)
- ✅ GET /v1/receipts/{id} → returns 501 NOT_IMPLEMENTED (auth-gated)
- ✅ PATCH /v1/receipts/{id}/items/{item_id} → returns 501 NOT_IMPLEMENTED (auth-gated; in
  api/CLAUDE.md's stub table but not originally itemized in this list — added for completeness,
  see Decisions Log)
- ✅ DELETE /v1/account → returns 501 NOT_IMPLEMENTED (auth-gated, implement in R2)
- ✅ Integration tests: all four stub routes return 501 + NOT_IMPLEMENTED when authenticated, 403
  when not (`tests/integration/test_receipts.py`, `tests/integration/test_account.py`)

### Backend — Tests
- ⏳ conftest.py fixtures (test_user, test_store, test_product, active_session) — intentionally
  still stubbed; every integration test file builds its data through the real API instead (see
  🔖 Next Session Starts Here for why this is fine to leave as-is)
- ✅ Unit: OTP flow (hashing, expiry, lockout) — `tests/unit/test_otp_flow.py`
- ✅ Unit: barcode waterfall (DB → Open Food Facts → manual) — `tests/unit/test_barcode_waterfall.py`
- ✅ Integration: auth endpoints — `tests/integration/test_auth.py`
- ✅ Integration: session CRUD — `tests/integration/test_sessions.py`
- ✅ Integration: product lookup — `tests/integration/test_products.py`

### Mobile — Foundation
- ✅ Expo project init (EAS managed, TypeScript, NativeWind v4 — SDK 57/RN 0.86.3/React 19.2.3,
  see 🔖 Next Session Starts Here for the exact dependency graph and why)
- ✅ Expo Router v3 layout (auth group, tabs group, session routes — the route structure/stub
  screens already existed from the scaffold session; `app/_layout.tsx` itself is now real)
- ✅ app.json + eas.json (permissions, bundle IDs, build profiles — deviates from root
  CLAUDE.md §22's literal example by dropping expo-notifications/photo-library permission, R2 scope)
- ✅ SafeAreaProvider + StatusBar in root layout
- ✅ services/api.ts (axios, JWT injection, 401 handler → clear tokens + redirect to /login,
  8s timeout, 2x backoff retry on network errors only — never on 4xx/5xx)
- ✅ expo-secure-store JWT storage (services/tokenStorage.ts — new file, not previously named
  in the tree)
- ✅ Zustand: authStore, sessionStore (with AsyncStorage persist via zustand/middleware,
  partialized to just activeSession), uiStore
- ✅ NetInfo offline listener + OfflineBanner component (wired in app/_layout.tsx, rendered
  above the Stack so it's visible on every screen per root CLAUDE.md §7)
- ✅ App version check on launch (GET /v1/config + real semver comparison via utils/semver.ts,
  not string comparison) — maintenance_mode and force_update each block all navigation via an
  early return before the Stack ever mounts

### Mobile — Auth Screens
- ✅ login.tsx (phone input, +91 prefix, E.164 format)
- ✅ otp.tsx (6-digit input, 30s resend cooldown, lockout UI)

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
| 2026-09-10 | send-otp uses a dev/mock OTP path — generates a real 6-digit code, hashes and stores it in Redis exactly like production would, but instead of calling Twilio Verify it `logger.info`s the code, gated to `settings.ENVIRONMENT == "development"` | Reuben has no Twilio account yet; explicitly asked for a dev/mock path this session. Gated to dev-only (not unconditional) because logging an OTP + phone number in plaintext is exactly what root CLAUDE.md's "never log PII in plaintext" rule exists to prevent — real Twilio integration is a TODO(r2) comment in `auth_service.send_otp` |
| 2026-09-10 | Added `logging.basicConfig(...)` in `app/main.py`, level INFO in development / WARNING otherwise | Discovered via manual `docker compose` testing: uvicorn configures its own `uvicorn`/`uvicorn.access` loggers but never touches the root logger, so `logger.info(...)` calls anywhere in app code (the dev-mock OTP log included) were silently dropped and never reached `docker compose logs` — pytest's `caplog` masked this because it attaches its own handler independent of runtime logging config, so tests passed while the feature was actually unusable manually. Fixed and re-verified: the OTP now appears in container logs |
| 2026-09-10 | JWT via `pyjwt==2.9.0` (HS256, `SECRET_KEY`); OTP hashing via stdlib `hmac.new(SECRET_KEY, otp, sha256)` + `hmac.compare_digest` — no new hashing library added | Simplest choice that satisfies api/CLAUDE.md's JWT payload spec exactly; OTP is a short numeric code compared against a fresh 10-minute value, so bcrypt-style slow hashing (passlib) is unnecessary — HMAC with the app secret as pepper is sufficient and needs zero new dependencies |
| 2026-09-10 | Added migration `85d56e67b258` to seed the `Config` singleton row (id=1) with MVP defaults, rather than lazily creating it in application code | api/CLAUDE.md is explicit that Config is "always UPDATE, never INSERT" — GET /v1/config must have a guaranteed row to read from day one. Hit a real bug while building this: the migration was first created empty (`alembic revision`, no `--autogenerate`) and edited a few seconds later, but a slow-starting background `alembic upgrade head` (waiting on Postgres to accept connections) executed it in between — it stamped `alembic_version` at the new revision using the *empty* `upgrade()`/`downgrade()` bodies, so no row was actually inserted despite `alembic current` showing head. Fixed via `alembic downgrade -1` then `alembic upgrade head` again once the file had real content, confirmed by querying the row directly. **Lesson: never run `alembic upgrade head` in the background against a migration file you're still mid-edit on — race the file write to completion first.** |
| 2026-09-10 | Created `api/.env` (gitignored, localhost-based `DATABASE_URL`/`REDIS_URL`) for running `api/.venv` commands (pytest, alembic, uvicorn --reload) directly on the host | It didn't exist yet — Pydantic Settings' `env_file=".env"` is read relative to cwd, and host-side venv commands run from `api/` need `localhost` (Compose port-forwards), not the Docker service names (`postgres`/`redis`) that root `.env` uses for the containerised `api` service. Both files are gitignored dev-only dummies; this doesn't change that pattern, just fills a gap |
| 2026-09-10 | Fixed a Windows-specific async test bug: the module-level `redis_pool`/`engine` singletons bind their pooled connections to whichever asyncio event loop first uses them, and pytest-asyncio's default per-test event loop (confirmed: `asyncio_default_fixture_loop_scope` only affects *fixture* loop scope in pytest-asyncio 0.24, not the per-test loop — there's no ini option to change that in this version) tears the loop down after each test, so test 2's fresh loop crashes on test 1's leftover connection (`RuntimeError: ... attached to a different loop`, surfaced via Windows' ProactorEventLoop). Fixed with an autouse `_reset_shared_connections` fixture in `tests/conftest.py` that calls `redis_pool.aclose()` and `engine.dispose()` after every test, forcing a fresh connection (bound to the next test's loop) on next use, instead of trying to force a shared event loop | A session-scoped `event_loop` fixture override was tried first and didn't work — pytest-asyncio 0.24 doesn't apply the ini-configured fixture loop scope to test items themselves, so fixtures and test bodies ended up on *different* loops, which is worse. Disposing pooled connections per test sidesteps event-loop scoping entirely and is the more portable fix |
| 2026-09-10 | Added `tests/integration/test_auth.py::_cleanup_test_users` (autouse, deletes known test phone numbers after each run) | Local Postgres persists between test runs (unlike CI's fresh container per run), so a user created by an earlier local run made `UserRepository.create()`'s branch look permanently uncovered/untested on reruns — the OTP login flow test's `+91987654322x` numbers would always find an existing user instead of exercising the create path. This only affects local iteration, not CI |
| 2026-09-10 | Replaced `StorePrice`'s single `UniqueConstraint(product_id, store_id)` with two partial unique indexes (`uq_store_price_product_with_store` WHERE store_id IS NOT NULL, `uq_store_price_product_no_store` WHERE store_id IS NULL) — migration `00b88de9abf6` | Postgres treats NULL as distinct from NULL for uniqueness purposes, so the original constraint silently allowed unlimited duplicate `(product_id, NULL)` rows — confirmed by direct testing (inserted the same product+null-store combo twice, got 2 rows, not an upsert). This is the common MVP case since real Store rows don't exist until R3, so it would have broken price upserts for nearly every product. `ProductRepository.upsert_price` now targets the correct partial index (`index_elements=['product_id']` + `index_where=store_id IS NULL`, or `['product_id','store_id']` + `store_id IS NOT NULL`) depending on whether `store_id` is given |
| 2026-09-10 | `ProductRepository.upsert_price`'s `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` includes `.execution_options(populate_existing=True)` | Found via direct testing: if the same `(product_id, store_id)` row was already loaded into the session's SQLAlchemy identity map earlier in the same request (e.g. by a prior `get_price()` call, which `create_manual_product` always does before upserting), the RETURNING clause's fresh data was silently discarded in favor of the stale cached Python object — confirmed the real DB row updated correctly while the returned object still showed the old price. Without `populate_existing=True`, an API response to a price update would show the *old* price. This never surfaces if the object isn't already in-session, which is why it's easy to miss without deliberately testing the get-then-upsert order |
| 2026-09-10 | Deliberately deviated from api/CLAUDE.md's literal `lookup_product` pseudocode: when a barcode is found in Open Food Facts but a lower-confidence local price already exists (e.g. a manual entry sitting at exactly the ">0.20" waterfall threshold, so it doesn't return early), the existing local product+price is kept and OFF's data is only used to create a *new* Product when none exists locally yet | The literal pseudocode calls `product_repo.upsert_price(barcode, store_id, off_result, confidence=0.30)` as if Open Food Facts returns a price — it doesn't; that API is a global food/ingredient database with no pricing data at all. Blindly following the pseudocode would either crash the price sanity check (price ≤ 0 is rejected) or require fabricating a fake price. The chosen behavior also better matches root CLAUDE.md's own confidence-display table (0.20-0.49 → "rough estimate", not silently discarded) |
| 2026-09-10 | Added `tests/unit/test_barcode_waterfall.py::_cleanup_test_products` and the equivalent in `tests/integration/test_products.py` (autouse, delete known test barcodes' Product/StorePrice rows after each run) | Same local-repeatability issue as the Auth session's user cleanup: these tests write Product rows directly (bypassing the service's own get-by-barcode-first idempotency in one case), and local Postgres persists between runs — a second local run hit a real `UniqueViolationError` on `products.barcode` before this was added. CI is unaffected (fresh container per run) |
| 2026-09-11 | **Fixed a latent bug in `app/models/__init__.py`**: it was completely empty, so `Store` (and every other model) was never imported by the running app — only `alembic/env.py` imported all models, for migrations. `ShoppingSession.store_id` has a string `ForeignKey("stores.id")`, which only needs to resolve once something actually queries `ShoppingSession`; nothing did until this session's Sessions endpoints existed, so the bug was invisible until now. Fixed by populating `app/models/__init__.py` with the same import list `alembic/env.py` already uses — since Python always runs a package's `__init__.py` before any of its submodules, this guarantees full mapper/metadata registration regardless of which route imports a model first, not just a workaround for this one FK | Discovered via `pytest`: `sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'shopping_sessions.store_id' could not find table 'stores'`. This would have bitten *any* future feature that queries `ShoppingSession` before something else happens to import `app.models.store` — fixing it at the single source-of-truth import point (per api/CLAUDE.md "`app/models/` — SQLAlchemy ORM models") rather than adding an incidental import to `session_repo.py` |
| 2026-09-11 | `SessionService.add_item` takes a `barcode` (not `product_id`) and internally calls `ProductService.find_product_and_price` — the *same* DB → Open Food Facts waterfall used by `GET /v1/products/{barcode}` — rather than a DB-only lookup. `ProductService.lookup_product` was refactored to extract this as a public method (`find_product_and_price`, returns `(Product, StorePrice \| None)` with the real `Product.id`, vs. the existing method's `ProductResponse` which has no id) | api/CLAUDE.md's own "Example — adding a session item" pseudocode shows `session_service.py` doing lookup + total computation without a separate barcode-resolution step, implying whatever resolves the barcode should be shared, not reimplemented. Reusing the waterfall (rather than a DB-only lookup) also means a user can scan a barcode Open Food Facts knows about and add it straight to their cart without a separate round-trip through `GET /v1/products` first — more resilient, and it's the one existing implementation of "barcode → product" in the codebase. The refactor is behavior-preserving for existing callers: `lookup_product`'s public contract and all of `test_barcode_waterfall.py` were unchanged |
| 2026-09-11 | When `add_item` resolves a product with no price yet (e.g. Open Food Facts confirmed the product's identity but has no pricing data), the item is still added to the session with `estimated_price_paise = 0`, rather than rejected | There's no dedicated "manual price for this item" endpoint in the MVP route list, and rejecting the add entirely would contradict root CLAUDE.md §9's own confidence-display table, which has a defined state for "price unknown — add manually" rather than treating it as a dead end. This is a known rough edge (an unpriced item silently shows ₹0 in the running total) — flagged here rather than solved, since fixing it properly means either a new endpoint or reusing `POST /v1/products`'s manual-price flow, both out of scope for "implement the 6 listed session routes" |
| 2026-09-11 | Session/item routes check `session.user_id == current_user` and raise 403 FORBIDDEN (not just 404) on mismatch, even though this wasn't separately itemized in progress.md | Every session route is behind the JWT `get_current_user_id` dependency specifically so sessions can be scoped to their owner — skipping the ownership check would mean any authenticated user could read or mutate any other user's session by guessing/enumerating UUIDs. `FORBIDDEN` is already a defined standard error code (api/CLAUDE.md → Error Response Format) |
| 2026-09-11 | A missing session-item (wrong `item_id` under a real `session_id`) returns error code `SESSION_NOT_FOUND`, not a new `SESSION_ITEM_NOT_FOUND` code | api/CLAUDE.md's "Standard error codes for Phase 1" list has no item-level not-found code, and inventing one unilaterally would diverge from the documented contract the mobile client is written against. The item lives *inside* a session URL path, so "not found in this session" is a reasonable stretch of the existing code rather than a new one |
| 2026-09-11 | `tests/integration/test_sessions.py` gets its auth token via the real send-otp/verify-otp flow + `caplog` (same pattern as `test_auth.py`), and creates its test product via `POST /v1/products` (same pattern as `test_products.py`) — it does **not** implement the still-stubbed `test_user`/`test_store`/`test_product`/`active_session` fixtures in `conftest.py` | Every existing integration test file already uses this "drive it through the real API" pattern instead of the fixture stubs; matching it keeps the test suite consistent and doesn't block Sessions on a separate, not-yet-scoped fixtures task. The fixture stubs are still tracked as ⏳ under Backend — Tests for whenever that's explicitly picked up |
| 2026-09-11 | `SessionRepository.list_items_with_product`'s return type needed `[(item, product) for item, product in result.all()]` instead of `list(result.all())` | mypy rejected the plain `list(...)` cast: `execute(select(SessionItem, Product))` returns `Sequence[Row[tuple[SessionItem, Product]]]`, and a `Row` isn't structurally a `tuple[SessionItem, Product]` as far as mypy's `list[...]` constructor is concerned, even though it unpacks fine at runtime. A list comprehension that destructures each `Row` sidesteps the type mismatch |
| 2026-09-11 | Added `PATCH /v1/receipts/{id}/items/{item_id}` as a 501 stub alongside the three routes progress.md's task list literally named (`POST /v1/receipts`, `GET /v1/receipts/{id}`, `DELETE /v1/account`) | api/CLAUDE.md's own "Stub as 501 in MVP" code block explicitly lists this route in the same group as the other three (no `(R3)`-style deferral tag, unlike `GET /v1/stores/nearby` which *is* tagged R3 and was left alone). Since the whole point of these stubs is "the mobile client can be written against them from day one," leaving one route out of a table that documents it as in-scope would silently reintroduce the exact retrofit risk root CLAUDE.md §3 is trying to avoid |
| 2026-09-11 | All four MVP stub routes (`POST /v1/receipts`, `GET /v1/receipts/{id}`, `PATCH /v1/receipts/{id}/items/{item_id}`, `DELETE /v1/account`) sit behind the JWT `get_current_user_id` dependency, returning 403 before ever reaching the 501, even though root CLAUDE.md's literal stub pseudocode (§3) shows no auth check | These are all user-scoped resources in their real R2 form (a user's own receipts, a user's own account) — the whole point of writing the mobile client against these routes now is so nothing about the contract changes when R2 ships, and R2's real versions will certainly require auth. Stubbing them open now and adding auth later *would* be the exact kind of client-facing contract change these stubs exist to prevent |
| 2026-09-11 | Used a single error code `NOT_IMPLEMENTED` (not in api/CLAUDE.md's "Standard error codes for Phase 1" list) for all four 501 stub responses | The existing standard-code list has nothing for "this route exists but isn't built yet" — every other code describes a real business-rule failure. `NOT_IMPLEMENTED` follows the same SCREAMING_SNAKE_CASE convention and is unambiguous; flagging here since it's a new addition to the code vocabulary, for whoever implements R2 to replace these usages with real codes |
| 2026-09-11 | Added a named volume (`postgres_data:/var/lib/postgresql/data`) to the `postgres` service in root `docker-compose.yml`, plus a top-level `volumes:` block | Discovered mid-session: `docker-compose.yml` never declared a volume for Postgres, so its data lived in an anonymous volume tied to the container. `docker compose down` (even *without* `-v`) was silently destroying that data every time, meaning every full-stack verification in every session had to start with a fresh `alembic upgrade head` — and worse, this would happen to Reuben's own local data on any ordinary `docker compose down`, not just during Claude Code sessions. Verified the fix: created a session, ran `docker compose down` → `up`, confirmed via `psql \dt` that all 9 application tables + `alembic_version` survived. Root CLAUDE.md's docker-compose.yml example (§4) doesn't show a volume either — this is a deliberate, minimal deviation from the literal example, not an oversight of it |
| 2026-09-12 | `mobile/` initialized on Expo SDK 57 / React Native 0.86.3 / React 19.2.3 — not any version this model was trained on. Package versions were sourced live from the npm registry (`npm view <pkg> version`), and `npx create-expo-app@latest` was run once into a scratch directory purely as a reference for what a working current config looks like, rather than hand-writing config from (stale) memory | Guessing exact compatible versions for a fast-moving native toolchain (Expo/RN/React/Metro all version-locked to each other) from training data this far out of date would very likely have produced a project that fails to install or bundle. Confirmed working via `npx expo-doctor` (18/18) and `npx expo export --platform android` (1696 modules bundled successfully) |
| 2026-09-12 | Pinned exact versions for `tailwindcss` (`^3.4.19`, not the current major v4), `react-native-reanimated` (`4.5.1`), `react-native-worklets` (`0.10.1`), and added an explicit `react-dom` (`19.2.3`) dependency that nothing in mobile/CLAUDE.md ever asked for | `nativewind@4.2.6`'s runtime (`react-native-css-interop`) only works with Tailwind v3's architecture despite its peer range technically allowing v4. Its babel preset also unconditionally `require`s `react-native-worklets/plugin`, and separately peer-requires `react-native-reanimated >=3.6.2` — neither optional, both undocumented in nativewind's own README, discovered only by reading its installed source and iterating through `npm install` ERESOLVE errors. `react-dom` had to be pinned because npm's peer resolution kept trying to satisfy `@expo/ui`'s optional web peer with the *latest* react-dom (19.3.0), which demands `react@^19.3.0` and conflicts with the react version RN 0.86.3/Expo SDK 57 actually expect (19.2.3) |
| 2026-09-12 | Added `mobile/global.d.ts` (committed) with the officially-documented `declare global { namespace JSX { ... } }` shim, rather than changing every existing stub file's `JSX.Element` return type | `@types/react@19.x` moved the `JSX` namespace from a global ambient namespace to `React.JSX`, which broke `JSX.Element` return-type annotations across every single existing `.tsx` stub file (all written before this typing change existed upstream). A one-time global shim fixes every file at once without touching files outside this session's scope (root CLAUDE.md §17's "never rewrite files you haven't read this session" rule) |
| 2026-09-12 | `app.json` omits the `expo-notifications` plugin and `NSPhotoLibraryUsageDescription`, and omits `icon`/`splash`/`adaptiveIcon` image references entirely, despite root CLAUDE.md §22's example config including all of them | Push notifications and receipt upload (the only reason for photo-library access) are both explicitly R2, and root CLAUDE.md §21 says a tempting future-release feature should get a `// TODO(r2)` and be moved past, not half-wired in now. Icon/splash images were skipped because no real brand assets exist yet — inventing placeholder binary image files isn't this session's job. Whoever picks up "MVP Ship → EAS preview build" will need real icon/splash assets before `eas build` succeeds |
| 2026-09-12 | Added `authStore.hydrate()` (reads the stored JWT from `expo-secure-store` on app launch, decodes it, checks `exp` client-side) plus a redirect effect in `app/_layout.tsx`, even though neither was an itemized Auth Screens task | Without it, the Foundation session's JWT persistence would have been dead code — the token was correctly saved to `expo-secure-store` on login, but nothing ever read it back on relaunch, so every cold start would force a full OTP re-login regardless of a still-valid stored session. Discovered while wiring `otp.tsx` to `useAuthStore.login()` and realizing there was no code path that could ever land a returning user anywhere but the login screen |
| 2026-09-12 | No token-refresh flow was built despite the access token expiring in 24h | `api/CLAUDE.md`'s auth routes are `send-otp`/`verify-otp` only — there is no `/v1/auth/refresh` endpoint on the backend to call. An expired access token falls back to a full OTP re-login via the existing `api.ts` 401 interceptor (clear tokens → redirect to `/login`), which is the correct behavior given what the backend actually supports today |

## Blockers Log
| Date | Blocker | Status |
|------|---------|--------|
| 2026-08-30 | No Python (or pip) installed on this machine — `pytest`/`mypy`/`ruff` can't run natively | ✅ Resolved 2026-08-31: Python 3.11.9 installed per-user (see Decisions Log). Verification now runs natively via `api/.venv` instead of Docker containers. |
