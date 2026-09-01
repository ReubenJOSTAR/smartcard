# CLAUDE.md — SmartCart Project Brain

> The Offline Shopping Companion. "Know before you checkout."
> This file is loaded at the start of every Claude Code session.
> Keep it authoritative. Update it when architecture decisions change.

---

## 1. Product North Star

SmartCart is a **mobile shopping companion** that lets users scan products in-store,
see a live running bill total, and track it against a budget — before reaching checkout.

**Positioning:** Not a budgeting app, not a calculator, not a delivery app.
Create the category: **Offline Shopping Companion**.

---

## 2. Release Map — What Gets Built When

Each release answers one question. Never build the next release until the current
one has answered its question with real user behaviour.

### 🟢 MVP (Month 1) — "Will people use this at all?"
Core scan loop only. 10–20 beta testers in Bengaluru.
**Success signal:** Testers open it at the supermarket without being reminded.

In scope:
- OTP login (phone + SMS, no other auth)
- Barcode scan → Open Food Facts lookup → manual fallback if not found
- Live running bill + budget indicator (green → amber → red)
- Session history (read only, free-text store name)
- Basic crash recovery (Zustand persist to AsyncStorage)
- Android + iOS beta via EAS (TestFlight + Play internal track)

Explicitly NOT in MVP — do not build:
- Receipt upload or OCR (no S3, no Celery, no Google Vision)
- Store discovery or location (free-text store name is enough)
- Price confidence scoring UI
- Offline SQLite cache (manual fallback is enough)
- Sync queue (too complex for MVP)
- PostHog analytics (console logs only)
- App version / force update
- DPDP account deletion
- Push notifications

MVP stack: FastAPI + PostgreSQL + Redis (OTP only) + Twilio + Open Food Facts.
No Celery, no S3, no MinIO, no workers. Simplest possible backend.

---

### 🔵 Release 2 (Month 2–3) — "Does better price data make it more useful?"
Close the loop between estimated and actual prices.
Start building the Indian product price database via crowdsourcing.
**Success signal:** >40% of sessions end with a receipt upload.

New in R2:
- Receipt upload (camera or gallery)
- Async OCR via Google Vision API (Celery worker)
- Actual vs estimated comparison screen
- Manual correction of OCR mismatches
- Price confidence scoring (user-facing labels, not raw numbers)
- Price crowdsourcing — every receipt improves the DB
- Push notification: "Your receipt is ready"
- DPDP account deletion (`DELETE /v1/account`)
- PostHog analytics (proper event tracking, not console logs)
- Sentry error monitoring

Infrastructure added in R2: Celery, Redis job queue, AWS S3, MinIO (dev),
Google Vision API, `expo-notifications`.

---

### 🔵 Release 3 (Month 4–5) — "Does knowing where to shop change behaviour?"
Turn price data into store intelligence. First feature useful *before* entering a store.
**Success signal:** Users check SmartCart before deciding which store to go to.

New in R3:
- Store discovery (nearby stores via PostGIS + GPS)
- Store selection at session start (replaces free-text)
- Price comparison across stores for the same product
- "Cheapest store for your list" — given past session items, which nearby store is cheapest
- Price confidence decay (Celery Beat nightly job)
- Barcodelookup.com as secondary barcode API (better Indian product coverage)
- Offline SQLite product cache (warm on session start, top 500 products per store)
- Full offline sync queue with idempotency keys

---

### 🟡 Release 4 (Month 6–7) — "Can this become a household tool?"
Expand from personal to family. First network effect.
**Success signal:** >1 phone number active per household. Referral rate increases.

New in R4:
- Shared shopping lists (invite by phone number)
- Collaborative session — two phones, one running total
- Household monthly budget tracking across all sessions
- Budget categories (groceries, personal care, snacks — user-defined)
- Recurring items — "my usual shop" template from past sessions
- Export session as PDF or WhatsApp share

---

### 🟠 Release 5 (Month 8–10) — "Can this make money without charging users?"
Turn usage into revenue via FMCG brands and retailer SaaS.
**Success signal:** First paying retailer or brand partnership signed.

New in R5:
- FMCG brand campaigns — contextual offers shown when scanning competing products
- Retailer dashboard (SaaS) — anonymised shopping patterns, popular products, price data
- SmartCart Pro for retailers — real-time basket data, targeted offers
- Loyalty program integration (Tata Neu, More Rewards)
- Sponsored "you might also need" product suggestions

---

### 🔴 Release 6 (Month 10–12) — "Can this get smarter than any competitor?"
Use the data built across R1–R5 to create intelligence no one can easily replicate.
This is where LangGraph comes in.
**Success signal:** Session frequency increases without marketing — users return because the app is getting smarter about them.

New in R6:
- AI shopping assistant — "I need to make biryani for 6, what will it cost?"
- Smart substitutions — "Tata Salt is ₹8 cheaper than Catch Salt, same quantity"
- Spend pattern insights — "You spend 23% more on weekends. Biggest category: dairy."
- Price alerts — "The oil you usually buy dropped ₹30 at DMart"
- LangGraph multi-step agent: recipe → ingredient list → nearest store → estimated total
- Voice input (ARIA integration)

---

## 3. Three Things to Build Right in MVP (Avoid Retrofit Later)

Even though these features are post-MVP, the data model must support them from day one:

**1. `store_id` on ShoppingSession — nullable in MVP**
MVP uses free-text store name. R3 adds real stores. If `store_id` column doesn't exist
in MVP, you'll need a painful migration. Add it nullable from the start.
```python
# models/shopping_session.py
store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)  # nullable for MVP
store_name_text = Column(String, nullable=True)  # MVP free-text, deprecated in R3
```

**2. `source` field on StorePrice — always populated**
MVP only uses Open Food Facts. R2 adds receipt OCR with higher confidence.
The `source` column must exist from day one so R2 data doesn't break queries.
```python
# models/store_price.py
source = Column(String, nullable=False)  # 'open_food_facts' | 'receipt_ocr' | 'manual'
confidence_score = Column(Float, nullable=False, default=0.30)
```

**3. `POST /v1/receipts` — stub it in MVP, implement in R2**
Return `501 Not Implemented` in MVP. The route exists so the mobile client
can be written against it from day one — no client changes needed when R2 ships.
```python
# routers/receipts.py (MVP stub)
@router.post("/receipts")
async def upload_receipt():
    raise HTTPException(status_code=501, detail="Receipt upload coming in R2")
```

---

---

## 4. Tech Stack

### Mobile App (Primary Surface)
- **Framework:** React Native + TypeScript — **EAS managed workflow** (not bare Expo)
- **Build & Deploy:** EAS Build (cloud `.apk`/`.ipa`) + EAS Update (OTA updates)
- **State:** Zustand (local) + React Query / TanStack Query v5 (server state)
- **Barcode Scanner:** `expo-camera` v14+ (barcode scanning built-in — `expo-barcode-scanner` is deprecated, do NOT use it)
- **Navigation:** Expo Router v3 (file-based)
- **Styling:** NativeWind v4 (Tailwind for RN)
- **OCR / Receipt:** Google Vision API (or AWS Textract fallback)
- **Push Notifications:** `expo-notifications` (managed, no custom native module needed)

### Backend
- **Runtime:** Python 3.11
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.x (async) with Alembic migrations
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Auth:** Phone number + OTP via Twilio Verify
- **Job Queue:** Celery + Redis (receipt OCR processing, async tasks)
- **Storage:** AWS S3 (receipt image uploads)

### Infrastructure — Local Dev vs Production

#### Redis
| Environment | Solution | Notes |
|---|---|---|
| Local dev | Redis 7 in Docker Compose | Zero cost, zero signup — use this for all development |
| Production | Upstash (serverless Redis) | Free tier: 10K req/day. Pay-per-use beyond that. No always-on instance cost. |

Upstash connection is a standard Redis URL — no code changes needed between local and prod.
Swap via environment variable only: `REDIS_URL=redis://localhost:6379` (local) vs `REDIS_URL=rediss://...upstash.io` (prod).

#### AWS S3
| Environment | Solution | Notes |
|---|---|---|
| Local dev | MinIO in Docker Compose | S3-compatible API — identical code, no AWS account needed during development |
| Production | AWS S3 (free tier) | 5GB + 20K requests/month free for 12 months. Pay-as-you-go after. No subscription. |

MinIO connection uses the same `boto3` client as S3 — swap via environment variables only.
No AWS account needed until you're ready to deploy to production.

#### Docker Compose — Local Dev Services

**MVP (current):** Only postgres, redis, and api needed. No Celery, no MinIO.
**R2+:** Add minio and celery services when receipt OCR is being built.

```yaml
# MVP docker-compose.yml — keep it simple
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: smartcart
      POSTGRES_USER: smartcart
      POSTGRES_PASSWORD: smartcart_local
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]   # OTP storage only in MVP

  api:
    build: ./api
    env_file: .env
    depends_on: [postgres, redis]
    ports: ["8000:8000"]

  # ── Add these in R2 when building receipt OCR ──────────────────
  # minio:
  #   image: minio/minio
  #   command: server /data --console-address ":9001"
  #   environment:
  #     MINIO_ROOT_USER: smartcart_local
  #     MINIO_ROOT_PASSWORD: smartcart_local
  #   ports:
  #     - "9000:9000"
  #     - "9001:9001"
  #
  # celery:
  #   build: ./api
  #   command: celery -A app.workers.celery_app worker --loglevel=info
  #   env_file: .env
  #   depends_on: [postgres, redis, minio]
```

#### `.env.example` — Required Variables

```bash
# ── MVP (needed from day one) ──────────────────────────────────────

# Database
DATABASE_URL=postgresql+asyncpg://smartcart:smartcart_local@localhost:5432/smartcart

# Redis — OTP storage only in MVP
REDIS_URL=redis://localhost:6379

# Auth
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_VERIFY_SERVICE_SID=

# App
SECRET_KEY=change_this_in_production
ENVIRONMENT=development                     # development | production
MIN_APP_VERSION=1.0.0

# ── R2+ (leave blank until building receipt OCR) ───────────────────

# S3 / MinIO
# AWS_ACCESS_KEY_ID=smartcart_local
# AWS_SECRET_ACCESS_KEY=smartcart_local
# AWS_S3_BUCKET=smartcart-receipts
# AWS_S3_ENDPOINT_URL=http://localhost:9000  # MinIO in dev, remove for prod AWS
# AWS_REGION=ap-south-1

# Google Vision (OCR)
# GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json

# Analytics
# POSTHOG_API_KEY=

# Upstash (production Redis with job queue — R2+)
# REDIS_URL=rediss://:password@host.upstash.io:6380
```

#### S3 Client — Works for Both MinIO and AWS S3
```python
# app/core/storage.py
import boto3
from app.core.config import settings

def get_s3_client():
    kwargs = {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION,
    }
    # endpoint_url is set in dev (MinIO), absent in prod (real AWS)
    if settings.AWS_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)
```

This pattern means zero code differences between local and production.
The only change is environment variables in `.env`.

### AI / Intelligence Layer
- **Barcode → Product lookup:** Open Food Facts API (primary) + Barcodelookup.com (fallback) + manual entry
- **Receipt OCR:** Google Cloud Vision API
- **Price estimation:** Store-specific price table in PostgreSQL, crowd-sourced via receipt uploads
- **Future:** LangChain/LangGraph agents for shopping intelligence (Phase 4+)

### Production Infrastructure (When Ready to Deploy)
- **Containerisation:** Docker + Docker Compose (local), ECS Fargate (prod)
- **CI/CD:** GitHub Actions
- **Reverse Proxy:** Nginx
- **Monitoring:** Sentry (errors) + Prometheus + Grafana (metrics)
- **Redis:** Upstash (serverless, pay-per-use)
- **Storage:** AWS S3 (free tier covers MVP, pay-as-you-go after)
- **Environment:** `.env` files, never hardcoded secrets

---

## 5. Folder Conventions

```
smartcart/
├── CLAUDE.md                  ← you are here
├── docker-compose.yml
├── .env.example
│
├── api/                       ← FastAPI backend
│   ├── CLAUDE.md              ← backend-specific context
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              ← config, db, redis, security
│   │   ├── models/            ← SQLAlchemy ORM models
│   │   ├── schemas/           ← Pydantic request/response schemas
│   │   ├── routers/           ← route handlers (one file per domain)
│   │   ├── services/          ← business logic (never in routers)
│   │   ├── repositories/      ← DB queries (never raw SQL in services)
│   │   └── workers/           ← Celery tasks
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── alembic/               ← DB migrations
│
├── mobile/                    ← React Native (Expo) app
│   ├── CLAUDE.md              ← mobile-specific context
│   ├── app/                   ← Expo Router pages
│   ├── components/            ← reusable UI components
│   ├── stores/                ← Zustand state stores
│   ├── hooks/                 ← custom React hooks
│   ├── services/              ← API client, external services
│   └── utils/
│
└── infra/                     ← Docker, Nginx, CI configs
```

---

## 6. Domain Model (Core Entities)

```
User           → phone_number (PK-like), otp_sessions
ShoppingSession → user_id, store_id, budget, status (active/finished)
SessionItem    → session_id, product_id, quantity, estimated_price
Product        → barcode (UPC/EAN), name, brand, category
StorePrice     → product_id, store_id, price, confidence_score, last_seen
Store          → name, chain, location (PostGIS point), city
Receipt        → session_id, image_s3_key, ocr_status, actual_total
ReceiptLineItem → receipt_id, product_name, actual_price, matched_product_id
```

Key invariants:
- A `ShoppingSession` must have exactly ONE active session per user at a time
- `StorePrice.confidence_score` degrades over time (stale prices are less trusted)
- `Receipt` OCR is always processed async — never block the user for it

---

## 7. Offline Mode Architecture

SmartCart is used inside supermarkets — many have poor basement/mall connectivity.
The core scan → see price loop must work offline. This is non-negotiable.

### Local Storage Stack
- **`expo-sqlite`** — local SQLite DB for offline product cache and pending sync queue
- **`@react-native-community/netinfo`** — detect connectivity state changes in real time
- **Zustand persist middleware** — persist active session to AsyncStorage as crash recovery

### What Is Cached Locally (Written on Session Start)
```
local_products     → barcode, name, price_paise, confidence_score, cached_at
local_session      → full active session state (items, quantities, running total)
local_sync_queue   → failed API calls queued for retry when online
```

### Offline Behaviour Rules
1. On session start (online) → fetch and cache store's top 500 products into `local_products`
2. On barcode scan → check `local_products` first, only hit API if not found locally
3. If API call fails (offline) → use cached price, flag item with `source: 'cache'`
4. All write operations (add item, update qty) → write locally first, queue API sync
5. On connectivity restore → flush `local_sync_queue` in order, resolve conflicts server-side
6. Show persistent "Offline — using cached prices" banner when `NetInfo.isConnected === false`

### Session Crash Recovery
- Active session written to `AsyncStorage` via Zustand persist on every state change
- On app launch: check for persisted session → if found and status is `active`, offer resume
- Resume prompt: "You have an unfinished session at [Store]. Continue?" → Yes / Start new
- Never silently discard a session with items in it

### Offline Forbidden Patterns
| ❌ Never | ✅ Instead |
|---|---|
| Block scan on network error | Use cached price, show cache indicator |
| Show empty screen when offline | Show last known data with offline banner |
| Lose session on app crash | Persist session state on every change |
| Retry failed calls immediately in a loop | Exponential backoff + queue flush on reconnect |

---

## 8. Barcode → Product Lookup Strategy

Open Food Facts has poor coverage of Indian products. Use a waterfall:

```
1. local_products cache (SQLite)          → fastest, works offline
        ↓ not found
2. PostgreSQL StorePrice DB               → crowd-sourced Indian product data
        ↓ not found
3. Open Food Facts API                    → global barcode DB
        ↓ not found
4. Barcodelookup.com API (fallback)       → broader coverage, rate-limited
        ↓ not found
5. "Product not found" flow               → user manually names it
```

### "Product Not Found" Flow — Required UI
Do NOT show a dead end. When all lookups fail:
1. Show: "We don't recognise this product yet"
2. Offer: "Add it manually" → user types product name, optional price
3. Add to session with `confidence_score: 0.0` and `source: 'manual'`
4. After receipt upload → if OCR finds this item, auto-match and store the product
5. This is how the Indian product DB gets built — every unknown is an opportunity

### Product Not Found Anti-Pattern
```
❌ "Barcode not found. Please try again."   → dead end, user frustrated
✅ "We don't know this one yet. Add it manually?" → keeps session going, builds DB
```

---

## 9. Price Confidence Scoring Rules

Every `StorePrice` record has a `confidence_score` (0.0 → 1.0). Rules are fixed:

| Source | Initial Score |
|---|---|
| Receipt OCR match (same store) | 0.95 |
| Receipt OCR match (different store, same city) | 0.70 |
| Manual user entry (with receipt later confirmed) | 0.80 |
| Manual user entry (unconfirmed) | 0.40 |
| Open Food Facts API only | 0.30 |
| Barcodelookup.com fallback | 0.25 |
| Manual entry, no receipt | 0.20 |

### Score Decay (Run as Nightly Celery Task)
```python
# Decay rule — applied to all StorePrice records nightly
days_old = (today - last_seen).days
if days_old > 30:
    new_score = max(0.10, confidence_score - (0.05 * (days_old - 30) / 7))
# Score floor is 0.10 — never fully discard crowd-sourced data
```

### UI Display Rules Based on Score
| Score | What to show user |
|---|---|
| 0.80 – 1.00 | "~₹X" (high confidence, no extra label) |
| 0.50 – 0.79 | "~₹X (estimated)" |
| 0.20 – 0.49 | "~₹X (rough estimate)" |
| < 0.20 | "Price unknown — add manually" |

Never display a raw confidence number to the user. Translate to plain language.

### Price Sanity Check (Prevent Bad Data Poisoning)
Before storing any price from OCR or manual entry, validate:
- Price > ₹0 and < ₹50,000 (reject obvious OCR errors)
- Price within 300% of existing stored price for same product (flag for review if outside)
- Reject prices that are round numbers like ₹1 or ₹9999 — likely OCR misreads

---

## 10. Defined Error States

Every error case must have an explicit UI state. Claude Code must implement all of these — do not leave any as a generic "Something went wrong."

### Barcode Scanner Errors
| Error | UI Response |
|---|---|
| Camera permission denied | Full-screen prompt explaining why camera is needed + Settings deep-link |
| Barcode unreadable (damaged/worn) | "Can't read this barcode — try again or add manually" + manual add button |
| Same barcode scanned within 2s | Silent debounce — no UI, no duplicate add |
| Product lookup fails (all sources) | "Product not found" flow (see Section 6) |

### Network & API Errors
| Error | UI Response |
|---|---|
| Offline on scan | Use cache silently, show offline banner |
| API timeout (>5s) | Use cache if available, else "Taking too long — try again" |
| API 500 error | Sentry log + "Something went wrong, your item wasn't added" + retry button |
| OTP SMS not received | "Didn't get it? Resend" (after 30s cooldown) + "Try WhatsApp OTP" (future) |
| OTP expired | "Code expired — request a new one" |
| OTP wrong (3rd attempt) | "Too many attempts — try again in 1 hour" + lockout |

### Session Errors
| Error | UI Response |
|---|---|
| App crash mid-session | Resume prompt on next launch (see Section 5) |
| Session already finished | "This session is complete — start a new one" |
| Item add fails (server) | Optimistic UI rolled back + toast "Couldn't add item, try again" |
| Budget exceeded | Non-blocking amber/red indicator — never prevent adding items |

### Receipt Upload Errors
| Error | UI Response |
|---|---|
| Upload fails (network) | "Upload failed — we'll try again when you're connected" + auto-retry queue |
| OCR fails completely | "We couldn't read this receipt — you can try uploading again or skip" |
| OCR partial match | "We matched X of Y items" — show matched + unmatched, allow manual correction |
| Image too blurry | "Receipt image is unclear — retake photo?" |

---

## 11. Analytics — PostHog Event Plan

**Library:** PostHog React Native SDK (`posthog-react-native`)
**Self-hosted or PostHog Cloud** — initialise from day one, never retrofit.

### Initialisation
```typescript
// app/_layout.tsx
import PostHog from 'posthog-react-native'
export const posthog = new PostHog('YOUR_POSTHOG_KEY', {
  host: 'https://app.posthog.com',
  disabled: process.env.NODE_ENV === 'development' // no noise in dev
})
```

### Required Events (Phase 1 — Must All Be Implemented)
```typescript
// Auth
posthog.capture('otp_requested', { method: 'sms' })
posthog.capture('login_success')
posthog.capture('login_failed', { reason: 'wrong_otp' | 'expired' | 'locked_out' })

// Session
posthog.capture('session_started', { store_id, budget_paise })
posthog.capture('item_scanned', { barcode, source: 'cache' | 'api' | 'manual', found: boolean })
posthog.capture('item_not_found', { barcode })           // critical to track
posthog.capture('item_added', { confidence_score })
posthog.capture('item_removed')
posthog.capture('session_finished', { item_count, estimated_total_paise, budget_paise })
posthog.capture('session_abandoned')                     // app closed without finishing

// Receipt
posthog.capture('receipt_upload_started')
posthog.capture('receipt_upload_success')
posthog.capture('receipt_upload_skipped')                // key metric — how many skip?
posthog.capture('receipt_ocr_completed', { matched_count, total_count })

// Offline
posthog.capture('offline_session_started')               // shopping while offline
posthog.capture('session_resumed_after_crash')
```

### Key Metrics to Monitor Weekly
- `item_not_found` rate → signals Indian barcode DB gaps
- `receipt_upload_skipped` rate → if >60%, the upload flow has friction
- `session_abandoned` rate → if >30%, core UX has a problem
- `offline_session_started` count → validates the offline investment

---

## 12. App Versioning & Force Update Strategy

### API Versioning
- All routes prefixed `/v1/` from day one: `GET /v1/products/{barcode}`
- Never make breaking changes to `/v1/` — add `/v2/` route alongside
- Deprecation header on old routes: `X-Deprecated: true` + `X-Sunset-Date: YYYY-MM-DD`

### Minimum App Version Check
On every app launch, hit `GET /v1/config` which returns:
```json
{
  "min_app_version": "1.2.0",
  "latest_version": "1.5.0",
  "force_update": false,
  "maintenance_mode": false
}
```

App behaviour:
- `force_update: true` → show full-screen "Please update SmartCart" modal, block all navigation
- `maintenance_mode: true` → show "SmartCart is under maintenance, back soon" screen
- Version behind but no force → show dismissible banner "New version available"

Version comparison must use semver — not string comparison (`"1.10.0" > "1.9.0"` must be true).

### OTA Update Rules (EAS Update)
- JS-only bug fixes → `eas update` (no store resubmission, ships in minutes)
- New native dependencies added → full `eas build` + store resubmission required
- Always test OTA update on a preview build before pushing to production branch

---

## 13. Receipt OCR — Accuracy & Correction Flow

### OCR Processing Pipeline (Celery Worker)
```
1. Download image from S3
2. Submit to Google Vision API (DOCUMENT_TEXT_DETECTION)
3. Parse response → extract line items (product name + price pairs)
4. For each line item: fuzzy-match product name against Product table
5. Store as ReceiptLineItem with matched_product_id (nullable if no match)
6. Compute actual_total from line items
7. Update Receipt.ocr_status = 'completed' | 'partial' | 'failed'
8. Push notification to user: "Your receipt is ready — see how close we were!"
9. Update StorePrice records for matched products (upsert with new confidence scores)
```

### Matching Strategy for Indian Receipts
Indian receipts use abbreviated SKU names ("PRLE-G ORIG 100G" for Parle-G Original 100g).
- Use `rapidfuzz` (Python) for fuzzy string matching — threshold 80% similarity
- Strip common receipt abbreviations before matching: "MRP", "GST", "CGST", "SGST", "QTY"
- Match on brand name first, then product name — brand is more reliable on Indian receipts
- Store unmatched line items as `ReceiptLineItem(matched_product_id=None)` — don't discard them

### User Correction Flow (UI)
After OCR completes, show comparison screen:
- Green rows: matched items (estimated vs actual price shown side by side)
- Amber rows: items we found on receipt but couldn't match to a scanned product
- Red rows: scanned items not found on receipt (possible scan error or item removed)
- User can tap any row to manually correct the match
- "Confirm" saves corrections → feeds back into StorePrice and product matching model

---

## 14. Privacy & Compliance

### DPDP Act 2023 (India) — Required
- Collect only what is needed: phone number (auth), location (store discovery), receipt images (price data)
- Receipt images: delete from S3 after OCR processing completes (retain extracted data, not the image) — or give user explicit choice to retain
- Users must be able to: view all their data, delete their account + all associated data
- `DELETE /v1/account` must hard-delete: User, all Sessions, all Receipts, all ReceiptLineItems
- Privacy policy URL required before Play Store / App Store submission

### Data Retention Rules
| Data | Retention |
|---|---|
| Receipt images (S3) | Delete after OCR complete (within 24h) |
| ReceiptLineItems | Retain indefinitely (anonymised price training data) |
| ShoppingSession | Retain for user history (deletable on account delete) |
| OTP records (Redis) | Auto-expire TTL 10 minutes |
| JWT tokens | Expire 24h, no server-side storage |

---



```
POST   /auth/send-otp
POST   /auth/verify-otp          → returns JWT

GET    /stores/nearby             → ?lat=&lng=&radius_km=
GET    /products/{barcode}        → product + estimated price for store

POST   /sessions                  → create shopping session
GET    /sessions/{id}             → session state
POST   /sessions/{id}/items       → add item
PATCH  /sessions/{id}/items/{item_id} → update quantity
DELETE /sessions/{id}/items/{item_id}
POST   /sessions/{id}/finish      → mark session done

POST   /receipts                  → upload receipt image (multipart)
GET    /receipts/{id}             → OCR status + comparison result

GET    /history                   → user's past sessions
```

---

## 15. Engineering Rules — NON-NEGOTIABLE

### Architecture
- **Services layer is mandatory.** Routers call services. Services call repositories. Repositories call the DB.
  Never put DB queries directly in routers. Never put business logic in repositories.
- **Pydantic schemas are the API contract.** Every request body and response must have an explicit schema.
  Never return SQLAlchemy model objects directly from routes.
- **Async all the way.** All FastAPI routes and DB operations must be `async`. No sync DB calls.
- **Repository pattern.** All queries live in `repositories/`. No raw SQL strings — use SQLAlchemy ORM.

### Type Safety
- TypeScript: `strict: true` in `tsconfig.json`. No `any` types. No `@ts-ignore`.
- Python: Full type annotations on all functions. Run `mypy` in CI.
- Pydantic models must have explicit field types. No `Dict[str, Any]` as response types.

### Security
- JWT tokens expire in 24h. Refresh token pattern for mobile.
- OTP codes expire in 10 minutes. Max 3 attempts before lockout.
- All S3 URLs for receipts must be pre-signed (never public bucket).
- Rate limit: `/auth/send-otp` → max 3 requests per phone number per hour.
- Never log PII (phone numbers, receipt contents) in plaintext.

### Error Handling
- No bare `except:` blocks. Always catch specific exceptions.
- FastAPI exception handlers must return structured `{"error": {"code": ..., "message": ...}}` responses.
- All Celery tasks must have retry logic with exponential backoff (max 3 retries).

### Database
- All schema changes go through Alembic migrations. Never `Base.metadata.create_all()` in production.
- Add DB indexes on: `product.barcode`, `store_price.(product_id, store_id)`, `session.user_id`, `store.location` (PostGIS).
- `StorePrice` updates must be upserts, never blind inserts.

### Mobile
- No API calls in components. All network calls go through `services/api.ts`.
- Zustand stores manage global state. React Query manages server cache.
- Barcode scanner must release camera on screen blur.
- All monetary values stored and computed as integers (paise, not rupees) to avoid float errors.

---

## 16. Forbidden Anti-Patterns

| ❌ Never do this | ✅ Do this instead |
|---|---|
| Raw SQL strings in Python | SQLAlchemy ORM / parameterized queries |
| Business logic in FastAPI routers | Move to `services/` layer |
| `any` type in TypeScript | Explicit types or generics |
| Storing prices as floats | Store as integers (paise) |
| Blocking receipt OCR inline | Celery async task |
| Returning ORM models from routes | Pydantic response schemas |
| Public S3 bucket for receipts | Pre-signed URLs only |
| Hardcoded API keys or secrets | `.env` + `core/config.py` with Pydantic Settings |
| `print()` for debugging | `logging` module with structured logs |
| God components in React Native | Split: screen / container / presentational |

---

## 17. Session Management & Progress Tracking

### The Golden Rule for Every Session
SmartCart is built across many short Claude Code sessions on a limited token budget.
Every session must start by reading `progress.md` and end by updating it.
**Never assume you know what's done. Always read `progress.md` first.**

### Session Start Protocol (Do This Before Anything Else)
```
1. Read CLAUDE.md (root)
2. Read progress.md
3. Read the relevant /api/CLAUDE.md or /mobile/CLAUDE.md for the module you're in
4. State out loud: "I am working on [TASK] from progress.md"
5. Ask Reuben to confirm before writing any code
```

### Session End Protocol (Do This Before Closing)
```
1. Update progress.md — mark completed tasks ✅
2. Add any new discoveries, blockers, or decisions made this session
3. Write the exact next task under "Next Session Starts Here"
4. Run the verification loop (Section 16) — never end on broken code
```

### `progress.md` — File Location & Rules
- Lives at repo root: `smartcart/progress.md`
- Claude Code owns this file — update it every single session without being asked
- Keep it concise — one line per task, not paragraphs
- Never delete completed tasks — mark them ✅ so history is preserved
- If a task is partially done, mark it 🔄 with a note on what remains

### `progress.md` — Initial Template (Create This on First Session)

```markdown
# SmartCart — Build Progress

> Updated every session by Claude Code. Read this before writing any code.
> Legend: ✅ Done | 🔄 In Progress | ⏳ Not Started | ❌ Blocked

---

## 🔖 Next Session Starts Here
**Task:** Project scaffold — folder structure + placeholder files
**Module:** Root
**Notes:** First session. Scaffold per CLAUDE.md §5, then stop.
MVP only — no Celery, no MinIO, no S3, no workers.

---

## MVP — Month 1 (Build This Now)

### Infrastructure
- ⏳ Project scaffold (folders, placeholder files)
- ⏳ docker-compose.yml (postgres + redis + api only — no MinIO/Celery in MVP)
- ⏳ .env.example with MVP-only variables (see CLAUDE.md §4)
- ⏳ GitHub Actions CI: pytest + mypy + ruff on push

### Backend — Core
- ⏳ FastAPI app factory (app/main.py, CORS, exception handlers)
- ⏳ Pydantic Settings config (app/core/config.py)
- ⏳ Async SQLAlchemy engine + session factory (app/core/database.py)
- ⏳ Redis connection pool — OTP only (app/core/redis.py)
- ⏳ SQLAlchemy models: User, ShoppingSession, SessionItem, Product, StorePrice, Store, Config
- ⏳ NOTE: Also create Receipt + ReceiptLineItem models (empty, for R2) — see CLAUDE.md §3
- ⏳ Alembic initial migration

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

## Blockers Log
| Date | Blocker | Status |
|------|---------|--------|
```

### Token Budget Rules for Claude Code
- **One module per session** — never jump between /api and /mobile in the same session
- **One feature area per session** — e.g. "Backend Auth" is one session, not "Backend Auth + Products"
- **Stop when the task in progress.md is done** — do not start the next task unsolicited
- **If context is getting long** — finish the current function, update progress.md, stop cleanly
- **Never rewrite files you haven't read this session** — always read before editing

---

## 18. Before Writing Any Code — Mandatory Checklist

1. **Read the relevant module's `CLAUDE.md`** (`/api/CLAUDE.md` or `/mobile/CLAUDE.md`)
2. **Write the failing test first** (pytest for backend, Vitest for mobile)
3. **Check if a repository method already exists** before creating a new DB query
4. **Confirm the Pydantic schema** exists for the request/response before writing the route
5. **Run the verification loop** before declaring done (see below)

---

## 19. Verification Loop (Run Before Every "Done")

```bash
# Backend
cd api
pytest tests/ -v --cov=app --cov-report=term-missing
mypy app/
ruff check app/

# Mobile
cd mobile
npx tsc --noEmit
npm run test
npx expo-doctor

# Full stack
docker compose up --build   # must start clean with no errors
```

---

## 20. Build Commands

```bash
# Local development
docker compose up                        # start all services
docker compose up api                    # backend only

# Database
alembic upgrade head                     # apply migrations
alembic revision --autogenerate -m "..."  # generate new migration

# Backend standalone
uvicorn app.main:app --reload --port 8000

# Mobile
cd mobile && npx expo start
cd mobile && npx expo start --android
cd mobile && npx expo start --ios

# Tests
pytest tests/unit/
pytest tests/integration/
pytest --cov=app

# Celery worker (local)
celery -A app.workers.celery_app worker --loglevel=info
```

---

## 21. Phase Roadmap (Do Not Build Ahead)

| Release | Timeline | Focus | Success Signal |
|---|---|---|---|
| **MVP** | Month 1 | Core scan loop, beta testers | Testers use it unprompted |
| **R2** | Month 2–3 | Receipt OCR, real prices, public launch | >40% sessions upload receipt |
| **R3** | Month 4–5 | Store discovery, price comparison | Users plan which store to visit |
| **R4** | Month 6–7 | Shared lists, household budgeting | >1 phone per household |
| **R5** | Month 8–10 | FMCG campaigns, retailer SaaS | First paying partner |
| **R6** | Month 10–12 | AI assistant, LangGraph agents | Session frequency grows organically |

**Rule: Do not implement the next release until the current one has answered its question.**
If a future-release feature is tempting to add now, add a `// TODO(r2):` comment and move on.

---

## 22. EAS Build Configuration

### `eas.json` — Build Profiles
```json
{
  "cli": { "version": ">= 7.0.0" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "android": { "buildType": "apk" },
      "ios": { "simulator": false }
    },
    "preview": {
      "distribution": "internal",
      "android": { "buildType": "apk" },
      "ios": { "simulator": false }
    },
    "production": {
      "android": { "buildType": "app-bundle" },
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {
      "android": { "serviceAccountKeyPath": "./google-service-account.json", "track": "internal" },
      "ios": { "appleId": "YOUR_APPLE_ID", "ascAppId": "YOUR_APP_ID", "appleTeamId": "YOUR_TEAM_ID" }
    }
  }
}
```

### `app.json` — Required Permissions & Config
```json
{
  "expo": {
    "name": "SmartCart",
    "slug": "smartcart",
    "version": "1.0.0",
    "orientation": "portrait",
    "plugins": [
      ["expo-camera", { "cameraPermission": "SmartCart uses your camera to scan product barcodes." }],
      ["expo-secure-store"],
      ["expo-notifications"]
    ],
    "ios": {
      "bundleIdentifier": "com.smartcart.app",
      "supportsTablet": false,
      "infoPlist": {
        "NSCameraUsageDescription": "SmartCart uses your camera to scan product barcodes.",
        "NSPhotoLibraryUsageDescription": "SmartCart accesses your photos to upload receipts."
      }
    },
    "android": {
      "package": "com.smartcart.app",
      "permissions": [
        "android.permission.CAMERA",
        "android.permission.READ_EXTERNAL_STORAGE"
      ],
      "googleServicesFile": "./google-services.json"
    }
  }
}
```

### EAS Build Commands (Quick Reference)
```bash
# Dev build — install on physical device for camera testing
eas build --platform android --profile development
eas build --platform ios --profile development

# Preview — internal beta (TestFlight / Play internal track)
eas build --platform all --profile preview

# Production
eas build --platform all --profile production

# OTA update (JS-only change, no store resubmission needed)
eas update --branch production --message "Fix: price display rounding"

# Submit to stores after production build
eas submit --platform android
eas submit --platform ios
```

### JWT / Sensitive Storage Rule
- **Always** use `expo-secure-store` for JWT tokens. Never `AsyncStorage` for anything sensitive.
- `AsyncStorage` is plaintext on disk — only use it for non-sensitive UI preferences (e.g. onboarding seen flag).

```typescript
// Correct
import * as SecureStore from 'expo-secure-store'
await SecureStore.setItemAsync('jwt_token', token)

// Never — plaintext storage
await AsyncStorage.setItem('jwt_token', token)
```

### Platform-Specific UI Rules
- Always wrap root layout with `SafeAreaProvider` + `SafeAreaView` — handles iOS notch and Android status bar
- Use `Platform.OS === 'ios'` sparingly — prefer cross-platform solutions first
- Test safe area on: iPhone SE (small), iPhone 15 Pro (Dynamic Island), Samsung mid-range (Android)
- `StatusBar` style must be explicitly set per screen — don't rely on defaults

---

## 23. Key Product Decisions (Locked)

- **Free for consumers always.** No paywalls on core scanning/budgeting features.
- **Crowd-sourced pricing.** Price accuracy improves as more users upload receipts. Design for this flywheel.
- **Confidence scores on prices.** Never show a price as definitive — always "estimated". UI must reflect uncertainty.
- **Receipt OCR is async.** Never make the user wait for it. Show "Processing..." and update when done.
- **India-first.** Currency in ₹ (paise internally). Store locations biased to Bengaluru for MVP.
- **OTP login only.** No email, no social login, no passwords in Phase 1.

---

*Last updated: 2026-08-28 v2 | Author: Reuben Joseph | Stack: FastAPI + React Native + PostgreSQL*
