# Project: BusLiner Quiet Luxury Ecosystem

## Architecture
- **Ecosystem**: High-craft passenger booking platform, carrier management office, embedded driver mobile cockpit with Three.js 3D Minibus, and dedicated passenger cabinet.
- **Authoritative Design Benchmark**: `/Users/aleksandr/BusLiner/index.html` (Quiet Luxury: strictly NO BURGUNDY / NO OXBLOOD; primary CTA Deep Alpine Forest `#23312A`).
- **Target Files**:
  - `/Users/aleksandr/BusLiner/carrier-workspace.html` (Carrier Office with embedded `#screen-cockpit` + Three.js 3D Minibus + real-time status broadcast).
  - `/Users/aleksandr/BusLiner/carrier-dashboard.html` (Driver Mobile Cockpit with embedded `#screen-cockpit` + Three.js 3D Minibus + real-time status broadcast).
  - `/Users/aleksandr/BusLiner/passenger-cabinet.html` (Passenger Cabinet: 3 functions [trips list, profile, order with SVG QR], live trip status receiver, dynamically seeded active ticket).
- **Core Technology**: Semantic HTML5, CSS3 Custom Properties with fluid typography clamp(), vanilla modern JS, Three.js 3D Sprinter bus, BroadcastChannel ('busliner_trip_sync'), SVG paper grain texture, kinetic cursor physics, mobile bottom sheet and bottom nav.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Quiet Luxury Palette (STRICTLY NO BURGUNDY/OXBLOOD) | `--canvas-ivory: #F5F1EA`, `--canvas-bone: #E8E2D6`, `--color-forest: #23312A`, `--color-graphite: #2B2A28`, hairline borders. Strict elimination of pure `#FFFFFF`, `#000000`, and COMPLETE ELIMINATION of Burgundy/Oxblood (`#7A2320`, `#5C2E2E`, `#631917`, `#4B2424`). Primary CTA is Deep Alpine Forest (`#23312A`). | All files | User Directive |
| F2 | Typographic Hierarchy | Cormorant Garamond display with italic accents in `<em>...</em>`, Plus Jakarta Sans body, JetBrains Mono tabular telemetry with tracking hierarchy (0.05em–0.18em). | All files | Survey Explorer 1 |
| F3 | Architectural Radii & Hairline Dividers | Strict `--radius-sm: 3px` and `--radius-md: 6px`. Elimination of bulky 10-18px radii. Hairline dividers `rgba(184, 169, 154, 0.42)`. | All files | Survey Explorer 1 |
| F4 | Tactile Paper Grain & Kinetic Motion | 3.8% opacity SVG paper grain noise overlay (`feTurbulence`), 0.22 lerp kinetic cursor on desktop, magnetic CTA buttons (`.btn-magnetic`, `.link-subtle-cta`). | All files | Survey Explorer 1 |
| F5 | Zero Dispatcher Architecture | Purge line 1929 and all dispatcher references ("Диспетчер предупрежден..."). Replace with automated passenger notification and carrier fleet radar updates. | M1 & M2 | Survey Explorer 2 & 3 |
| F6 | Carrier Reactive Financials & 5% Fee | Reactive `calculateFinancials()` with `Math.max(0, ...)` zero-clamping computing Gross Revenue, 5% platform commission, and Net IBAN payout from trips and bookings data. | M1 | Survey Explorer 2 & Challenger 1 |
| F7 | Mobile Cards for All Tables | Mobile `< 768px` cards feed with occupancy progress bars for Dashboard, Trips, Bookings, Schedule, Finances (route profitability), and Settings (fleet vehicles). | M1 | Survey Explorer 2 |
| F8 | Complete Mobile Navigation Reachability | Mobile Bottom Nav providing reachability to all views (Dashboard, Trips, Schedule, Bookings, Finances, Settings/Fleet, Cockpit). | M1 | Survey Explorer 2 |
| F9 | Driver Active Trip Top Banner | Prominent top banner with departure time, route, platform, vehicle number, seat occupancy progress, and live departure countdown. | M1 & M2 | Survey Explorer 3 |
| F10 | Driver Touch Targets (>= 48px–52px) | Boarding controls (`.btn-checkin-toggle`, `.btn-call-passenger`, `.btn-mobile-board`) strictly >= 48px tap targets for thumb ergonomics. | M1 & M2 | Survey Explorer 3 |
| F11 | 1-Tap Passenger Call (`tel:`) | Direct dialer with sanitized phone number formatting (`String(phone || '').replace(...)`) and paid vs cash-on-board status indicator. | M1 & M2 | Survey Explorer 3 & Challenger 1 |
| F12 | Quick Ticket Acceptance & Payment Status | Instant boarding toggle ("Принять билет" -> "✓ Билет принят • В салоне") with clear payment distinction: "Оплачено онлайн" vs "Оплата водителю: 85 BYN" (cash collection notice). | M1 & M2 | User Update |
| F13 | 20-Seat Minibus Seatmap & 92dvh Bottom Sheet | Realistic 20-seat minibus cabin layout (driver seat, aisle, seat occupancy state) and manifest drawer transforming to a 92dvh mobile Bottom Sheet with tactile grabber handle. | M1 & M2 | Survey Explorer 3 |
| F14 | iOS Auto-Zoom Prevention | All form inputs, selects, and textareas enforce `font-size >= 16px`. | All files | Survey Explorer 2 & 3 |
| F15 | Strict Zero `<img>` & Zero `[...]` Guardrails | Strictly 0 `<img>` tags (SVG/CSS only) and 0 square brackets `[...]` in visible UI copy. | All files | ORIGINAL_REQUEST |
| F16 | Driver Ticket Acceptance ONLY | In driver mode/views: strictly NO ticket creation ("Оформить билет", "Добавить бронь вручную", "Создать рейс"). Driver ONLY accepts/validates tickets, searches, 1-tap calls, views seats, and manages trip lifecycle. | M1 & M2 | User Update |
| F17 | Elimination of Role Toggle Switch | Remove the visual toggle switch between carrier and driver from the UI. Dedicated separate experiences for carrier and driver without confusing switchers. | M1 & M2 | User Update |
| F18 | Dedicated Passenger Cabinet (3 Core Functions) | (1) Browse/book trips, (2) User Profile, (3) Active order with working vector SVG QR pass; dynamic active ticket pre-seeded in repository. | M4 | User Update 2026-10-24T15:01:58Z |
| F19 | Embedded Driver Cockpit Screen (#cockpit) | In `carrier-workspace.html` and `carrier-dashboard.html`: remove external footer link to driver terminal; fully embed first-class `#screen-cockpit` screen ("Пульт рейса") accessible via sidebar and bottom nav with trip hero, KPI tiles, quick actions, 20-seat layout, and manifest. | M1 & M2 | User Directive |
| F20 | Three.js 3D Sprinter Minibus Model | Integrate Three.js 3D minibus model into the driver cockpit in place of/alongside 2D layout (reference `seat-picker-3d-demo.html`). | M1 & M2 | User Update 2026-10-24T15:01:58Z |
| F21 | Real-Time Trip Status Sync | Instant bidirectional sync of trip status ("Посадка", "В пути", "Задержка +15 мин", "Завершен") between Driver Cockpit and Passenger Cabinet via `BroadcastChannel('busliner_trip_sync')` and `localStorage`. | All files | User Update 2026-10-24T15:01:58Z |
| F22 | Viewport Overflow & Keyboard Defenses | Eliminate horizontal scroll clipping at 320px/375px (`scrollWidth <= clientWidth`), add Escape key modal listeners in passenger cabinet. | All files | Challenger 1 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | E2E Testing Track | Requirement-driven automated test suite across all features (Tiers 1-4). Outputs `TEST_READY.md`. | none | DONE |
| M5 | 3D Minibus, Real-Time Sync & Mobile Defenses | Implement Three.js 3D minibus, BroadcastChannel sync, 3-function dynamic passenger cabinet, 320px overflow fix, and math/phone defenses across all 3 files. | M0 | IN_PROGRESS |
| M3 | Final Verification & Forensic Audit | Pass 100% of E2E tests, Reviewer approvals (2x), Challenger empirical tests (2x), Forensic Auditor clean verdict. | M5 | PLANNED |
