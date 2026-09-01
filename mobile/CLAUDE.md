# CLAUDE.md — SmartCart Mobile (React Native Context)

> Load this when working inside /mobile. Supplements root CLAUDE.md.
> Root CLAUDE.md has the full engineering rules, error states, offline
> architecture, analytics events, and confidence scoring display rules.
> Read it first if you haven't.
>
> **Session start checklist:**
> 1. Read `progress.md` (repo root) — confirm the task for this session
> 2. Read root `CLAUDE.md`
> 3. Read this file
> 4. State the task out loud and wait for Reuben to confirm before writing code
> 5. On session end — update `progress.md`, mark done ✅, set next task

---

## Module Focus
Expo (React Native + TypeScript) app — EAS managed workflow.
**Currently building MVP** — see CLAUDE.md §2 for full release map.
MVP scope: auth, scanner, live bill, session history, crash recovery.
Receipt upload, PostHog, confidence labels, and offline SQLite are R2/R3.

---

## MVP vs Post-MVP — What to Build Now

### Build in MVP
- Auth screens (login, OTP)
- Home screen (crash recovery prompt, recent sessions)
- Scanner screen (CameraView, live bill, budget bar)
- Session detail screen (item list, finish button)
- History screen (paginated sessions)
- All core components (BudgetBar, SessionItem, OfflineBanner, ConfirmSheet)
- PriceTag — simple `~₹X` display only, no confidence labels yet
- Crash recovery (Zustand AsyncStorage persist)
- Offline banner (NetInfo) + manual fallback on scan failure
- App version check (GET /v1/config)

### Do Not Build in MVP (add in correct release)
- `session/[id]/receipt.tsx` — OCR comparison screen (R2)
- `account/delete.tsx` — DPDP deletion screen (R2)
- PostHog analytics wrapper (R2 — use console.log in MVP)
- PriceTag confidence labels: "estimated", "rough estimate" (R2)
- expo-sqlite product cache (R3)
- Sync queue with idempotency keys (R3)
- Store discovery / GPS (R3)
- Shared lists, household features (R4)

---

## Screen Map

### MVP Screens (Build Now)
```
app/
├── _layout.tsx                    — root layout, SafeAreaProvider,
│                                    NetInfo listener, app version check
├── (auth)/
│   ├── _layout.tsx
│   ├── login.tsx                  — phone number entry (+91 prefix, E.164)
│   └── otp.tsx                    — 6-digit OTP, 30s resend cooldown, lockout UI
├── (tabs)/
│   ├── _layout.tsx
│   ├── index.tsx                  — home: crash recovery prompt, recent sessions
│   ├── scan.tsx                   — barcode scanner + live bill + budget bar
│   └── history.tsx                — paginated past sessions
└── session/
    └── [id].tsx                   — item list, qty controls, finish button
```

### Post-MVP Screens (Do Not Build Yet)
```
app/
├── session/[id]/receipt.tsx       — R2: OCR actual vs estimated comparison
└── account/delete.tsx             — R2: DPDP account deletion confirmation
```

---

## State Architecture

### Zustand Stores (global, persisted where noted)
```typescript
// stores/authStore.ts
{
  user: { id, phone } | null
  isAuthenticated: boolean
  // JWT stored in expo-secure-store — NOT in Zustand state
  login: (phone, token, refreshToken) => void
  logout: () => void
}

// stores/sessionStore.ts  ← persisted to AsyncStorage (crash recovery)
{
  activeSession: {
    id: string
    storeId: number
    storeName: string
    budgetPaise: number
    items: SessionItem[]   // { id, barcode, name, qty, pricePaise, confidence, source }
    runningTotalPaise: number
    status: 'active' | 'finished'
    lastUpdatedAt: string
  } | null
  isOffline: boolean
  syncQueue: SyncQueueItem[]   // pending API writes when offline
  resumeSession: (session) => void
  addItem: (item) => void      // optimistic — writes locally first
  updateQty: (itemId, qty) => void
  removeItem: (itemId) => void
  clearSession: () => void
}

// stores/uiStore.ts  ← NOT persisted
{
  offlineBannerVisible: boolean
  forceUpdateRequired: boolean
  maintenanceMode: boolean
}
```

### React Query (TanStack Query v5) — server cache
- `useProduct(barcode, storeId)` — barcode lookup, 30min stale time
- `useSession(sessionId)` — current session from server, poll every 10s when receipt pending
- `useHistory()` — paginated sessions, infinite query
- `useNearbyStores(lat, lng)` — store list, 5min stale time
- `useReceiptStatus(receiptId)` — poll every 3s until `ocr_status !== 'processing'`

---

## Offline Mode Implementation

### NetInfo Listener (in `app/_layout.tsx`)
```typescript
import NetInfo from '@react-native-community/netinfo'

useEffect(() => {
  const unsubscribe = NetInfo.addEventListener(state => {
    const wasOffline = sessionStore.isOffline
    sessionStore.setOffline(!state.isConnected)

    // Flush sync queue when coming back online
    if (wasOffline && state.isConnected) {
      syncQueueService.flush()
    }
  })
  return unsubscribe
}, [])
```

### SQLite Local Cache (`services/localCache.ts`)
```typescript
// Tables in expo-sqlite
// local_products: barcode, name, price_paise, confidence_score, source, cached_at
// -- populated on session start (top 500 products for selected store)
// -- checked on every barcode scan before hitting API

// On session start (online):
await localCache.warmForStore(storeId)  // fetches + stores top 500 products

// On barcode scan:
const cached = await localCache.getProduct(barcode)
if (cached) return { ...cached, fromCache: true }
// else hit API
```

### Sync Queue (`services/syncQueue.ts`)
```typescript
// Every write that fails offline is queued:
type SyncQueueItem = {
  id: string           // client-generated UUID (idempotency key)
  method: 'POST' | 'PATCH' | 'DELETE'
  url: string
  body: object
  createdAt: string
}

// flush() — called on reconnect, processes FIFO
// Each item sent with header: Idempotency-Key: item.id
// On 409 Conflict (already processed) → skip silently, remove from queue
```

---

## Barcode Scanner (`app/(tabs)/scan.tsx`)

```typescript
import { CameraView, useCameraPermissions } from 'expo-camera'

// NEVER import from 'expo-barcode-scanner' — deprecated, removed in SDK 51+

// Required barcode types for Indian retail:
const BARCODE_TYPES = ['ean13', 'ean8', 'upc_a', 'upc_e', 'code128', 'code39']

// Debounce — use ref, NOT state (state causes re-render lag)
const lastScannedRef = useRef<{ barcode: string; time: number } | null>(null)

const handleScan = ({ data: barcode }: BarcodeScanningResult) => {
  const now = Date.now()
  if (
    lastScannedRef.current?.barcode === barcode &&
    now - lastScannedRef.current.time < 2000
  ) return  // debounce — silent, no UI

  lastScannedRef.current = { barcode, time: now }
  onBarcodeScanned(barcode)  // → lookup waterfall → add to session
}

// Camera release — mandatory
useFocusEffect(useCallback(() => {
  return () => { /* camera releases automatically on unmount */ }
}, []))
```

### Scanner Error States (all must be implemented — see root CLAUDE.md §8)
- Camera permission denied → full-screen prompt + Settings deep-link via `Linking.openSettings()`
- Product not found (all sources exhausted) → bottom sheet: "Add manually" form
- Offline + not in cache → "Can't look up this product right now — add manually?"

---

## Monetary Values — CRITICAL RULE

**Store and compute in PAISE (integer). Display in ₹. No exceptions.**

```typescript
// ✅ Correct
const totalPaise = items.reduce((sum, i) => sum + i.pricePaise * i.qty, 0)
const display = `₹${(totalPaise / 100).toFixed(2)}`

// ❌ Never — float arithmetic causes rounding errors at scale
const total = items.reduce((sum, i) => sum + i.price * i.qty, 0)
```

---

## Confidence Score → UI Display (`utils/priceDisplay.ts`)

```typescript
// Translate confidence score to user-facing label (never show raw number)
export function getPriceLabel(pricePaise: number, confidence: number): string {
  const rupees = `₹${(pricePaise / 100).toFixed(2)}`
  if (confidence >= 0.80) return `~${rupees}`
  if (confidence >= 0.50) return `~${rupees} (estimated)`
  if (confidence >= 0.20) return `~${rupees} (rough estimate)`
  return 'Price unknown'
}

// Budget indicator colour
export function getBudgetColour(spentPaise: number, budgetPaise: number): string {
  const pct = spentPaise / budgetPaise
  if (pct >= 1.00) return '#EF4444'   // red — over budget
  if (pct >= 0.80) return '#F59E0B'   // amber — 80% used
  return '#22C55E'                     // green — safe
}
```

---

## Session Crash Recovery (`app/(tabs)/index.tsx`)

```typescript
// On home screen mount — check for persisted active session
useEffect(() => {
  const session = sessionStore.activeSession
  if (session && session.status === 'active' && session.items.length > 0) {
    Alert.alert(
      'Resume Shopping?',
      `You have an unfinished session at ${session.storeName} with ${session.items.length} items.`,
      [
        { text: 'Start New', style: 'destructive', onPress: sessionStore.clearSession },
        { text: 'Continue', onPress: () => router.push(`/session/${session.id}`) }
      ]
    )
    posthog.capture('session_resumed_after_crash')
  }
}, [])
```

---

## App Version Check (`app/_layout.tsx`)

```typescript
import * as Application from 'expo-application'
import semver from 'semver'  // install: semver + @types/semver

const config = await api.get('/v1/config')  // no auth required

if (config.maintenance_mode) {
  // Show full-screen maintenance screen — block all navigation
  uiStore.setMaintenanceMode(true)
  return
}

const currentVersion = Application.nativeApplicationVersion  // e.g. "1.0.0"
if (semver.lt(currentVersion, config.min_app_version)) {
  // Show full-screen force update modal — block all navigation
  uiStore.setForceUpdateRequired(true)
  return
}
```

---

## Analytics — PostHog (`services/analytics.ts`)

```typescript
import PostHog from 'posthog-react-native'

export const posthog = new PostHog(process.env.EXPO_PUBLIC_POSTHOG_KEY!, {
  host: 'https://app.posthog.com',
  disabled: __DEV__   // no events in development
})

// Wrapper — keeps event names consistent, prevents typos
export const analytics = {
  sessionStarted: (storeId: number, budgetPaise: number) =>
    posthog.capture('session_started', { store_id: storeId, budget_paise: budgetPaise }),

  itemScanned: (barcode: string, found: boolean, source: string, confidence: number) =>
    posthog.capture('item_scanned', { barcode, found, source, confidence }),

  itemNotFound: (barcode: string) =>
    posthog.capture('item_not_found', { barcode }),

  sessionFinished: (itemCount: number, estimatedPaise: number, budgetPaise: number) =>
    posthog.capture('session_finished', { item_count: itemCount, estimated_total_paise: estimatedPaise, budget_paise: budgetPaise }),

  receiptSkipped: () => posthog.capture('receipt_upload_skipped'),
  receiptUploaded: () => posthog.capture('receipt_upload_success'),
  offlineSession: () => posthog.capture('offline_session_started'),
  crashRecovery: () => posthog.capture('session_resumed_after_crash'),
}
// Import analytics from this file — never call posthog.capture() directly in components
```

---

## Component Structure

Three strict layers — never mix concerns:

```
components/
├── ui/              — pure presentational, no state, no API calls
│   ├── BudgetBar.tsx         — coloured progress bar (green/amber/red)
│   ├── PriceTag.tsx          — renders price + confidence label
│   ├── OfflineBanner.tsx     — persistent top banner when offline
│   ├── SessionItem.tsx       — single scanned item row
│   └── ConfirmSheet.tsx      — bottom sheet for destructive confirmations
├── containers/      — stateful logic, no styling
│   ├── ScannerContainer.tsx  — barcode scan → lookup → add to session
│   ├── SessionContainer.tsx  — session state management
│   └── ReceiptContainer.tsx  — receipt upload + OCR polling
└── screens/         — handled by Expo Router in app/ — no extra screen components
```

---

## Environment Variables (Mobile)

Expo reads env vars prefixed `EXPO_PUBLIC_` at build time. Never hardcode URLs or keys.

```bash
# .env.local (dev — points to local Docker API)
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_POSTHOG_KEY=your_posthog_key

# .env.production (prod — points to deployed API)
EXPO_PUBLIC_API_URL=https://api.smartcart.app
EXPO_PUBLIC_POSTHOG_KEY=your_posthog_key
```

When testing on a **physical Android device** against the local Docker API,
`localhost` won't work — the device can't reach your machine's localhost.
Use your machine's local network IP instead:
```bash
# Find your IP: ifconfig | grep "inet " (Mac/Linux) or ipconfig (Windows)
EXPO_PUBLIC_API_URL=http://192.168.1.x:8000
```

For iOS Simulator, `localhost` works fine.
For Android Emulator, use `http://10.0.2.2:8000` (emulator's alias for host localhost).

---

## API Client (`services/api.ts`)

```typescript
// axios instance with:
// - baseURL from EXPO_PUBLIC_API_URL env var
// - JWT injected from expo-secure-store on every request
// - 401 interceptor → clear JWT → redirect to /login
// - timeout: 8000ms (8s) — surface timeout errors, don't hang
// - retry: 2 retries on network error (not on 4xx/5xx)

// Offline queue integration:
// - On network error → add to syncQueue if it's a write (POST/PATCH/DELETE)
// - On success → remove from syncQueue if it was a queued item
```

---

## Key UX Rules — Non-Negotiable

- Running total updates **instantly** on scan (optimistic — don't wait for server confirmation)
- Budget bar colour changes in real time as items are added
- "Finish Shopping" button → always show `ConfirmSheet` first — accidental taps are costly
- Receipt upload → camera or gallery — two taps max to start upload
- Receipt upload is optional — always show a clear "Skip for now" option
- Always show "~" prefix or "estimated" label on prices — never imply exact
- Offline banner must be visible on every screen when offline — not just the scan screen
- Force update screen and maintenance screen must block all navigation (no back gesture)
