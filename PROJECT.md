# Project: BusLiner Quiet Luxury Ecosystem

## Architecture
- **Ecosystem**: High-craft passenger booking platform, carrier management office, driver mobile terminal, and dedicated passenger cabinet.
- **Authoritative Design Benchmark**: `/Users/aleksandr/BusLiner/aura-b2c-masterpiece.html` (Quiet Luxury: strictly NO BURGUNDY / NO OXBLOOD; primary CTA Deep Alpine Forest `#23312A`).
- **Target Files**:
  - `/Users/aleksandr/BusLiner/carrier-workspace.html` (Carrier Office: Fleet Analytics, IBAN, Schedule, Revenue, Ticket Booking & Creation; NO driver toggle).
  - `/Users/aleksandr/BusLiner/carrier-dashboard.html` (Driver Mobile Cockpit: Active Trip Banner, Platform, Countdown, Ticket Acceptance ONLY with Cash vs Online distinction, 20-seat Minibus, Manifest Bottom Sheet, 1-tap `tel:`, Trip Lifecycle; NO carrier toggle).
  - `/Users/aleksandr/BusLiner/passenger-cabinet.html` (Dedicated Passenger Cabinet: Active Ticket Card, SVG QR Boarding Pass, Seat/Driver Contact, BusLiner Miles Loyalty, Travel History, Profile).
- **Core Technology**: Semantic HTML5, CSS3 Custom Properties with fluid typography clamp(), vanilla modern JS, SVG paper grain texture, kinetic cursor physics, mobile bottom sheet and bottom nav.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Quiet Luxury Palette (STRICTLY NO BURGUNDY/OXBLOOD) | `--canvas-ivory: #F5F1EA`, `--canvas-bone: #E8E2D6`, `--color-forest: #23312A`, `--color-graphite: #2B2A28`, hairline borders. Strict elimination of pure `#FFFFFF`, `#000000`, and COMPLETE ELIMINATION of Burgundy/Oxblood (`#7A2320`, `#5C2E2E`, `#631917`, `#4B2424`). Primary CTA is Deep Alpine Forest (`#23312A`). | M1, M2, M4 | User Directive 2026-10-24T13:59:07Z |
| F2 | Typographic Hierarchy | Cormorant Garamond display with italic accents in `<em>...</em>`, Plus Jakarta Sans body, JetBrains Mono tabular telemetry with tracking hierarchy (0.05em–0.18em). | M1, M2, M4 | Survey Explorer 1 |
| F3 | Architectural Radii & Hairline Dividers | Strict `--radius-sm: 3px` and `--radius-md: 6px`. Elimination of bulky 10-18px radii. Hairline dividers `rgba(184, 169, 154, 0.42)`. | M1, M2, M4 | Survey Explorer 1 |
| F4 | Tactile Paper Grain & Kinetic Motion | 3.8% opacity SVG paper grain noise overlay (`feTurbulence`), 0.22 lerp kinetic cursor on desktop, magnetic CTA buttons (`.btn-magnetic`, `.link-subtle-cta`). | M1, M2, M4 | Survey Explorer 1 |
| F5 | Zero Dispatcher Architecture | Purge line 1929 and all dispatcher references ("Диспетчер предупрежден..."). Replace with automated passenger notification and carrier fleet radar updates. | M1 & M2 | Survey Explorer 2 & 3 |
| F6 | Carrier Reactive Financials & 5% Fee | Reactive `calculateFinancials()` computing Gross Revenue, 5% platform commission, and Net IBAN payout from trips and bookings data. | M1 | Survey Explorer 2 |
| F7 | Mobile Cards for All Tables | Mobile `< 768px` cards feed with occupancy progress bars for Dashboard, Trips, Bookings, Schedule, Finances (route profitability), and Settings (fleet vehicles). | M1 | Survey Explorer 2 |
| F8 | Complete Mobile Navigation Reachability | Mobile Bottom Nav providing reachability to all views (Dashboard, Trips, Schedule, Bookings, Finances, Settings/Fleet). | M1 | Survey Explorer 2 |
| F9 | Driver Active Trip Top Banner | Prominent top banner with departure time, route, platform, vehicle number, seat occupancy progress, and live departure countdown. | M2 | Survey Explorer 3 |
| F10 | Driver Touch Targets (>= 48px–52px) | Boarding controls (`.btn-checkin-toggle`, `.btn-call-passenger`, `.btn-mobile-board`) strictly >= 48px tap targets for thumb ergonomics. | M2 | Survey Explorer 3 |
| F11 | 1-Tap Passenger Call (`tel:`) | Direct dialer with sanitized phone number formatting and paid vs cash-on-board status indicator. | M2 | Survey Explorer 3 |
| F12 | Quick Ticket Acceptance & Payment Status | Instant boarding toggle ("Принять билет" -> "✓ Билет принят • В салоне") with clear payment distinction: "Оплачено онлайн" vs "Оплата водителю: 85 BYN" (cash collection notice). | M2 | User Update 2026-10-24T14:15:35Z |
| F13 | 20-Seat Minibus Seatmap & 92dvh Bottom Sheet | Realistic 20-seat minibus cabin layout (driver seat, aisle, seat occupancy state) and manifest drawer transforming to a 92dvh mobile Bottom Sheet with tactile grabber handle. | M2 | Survey Explorer 3 |
| F14 | iOS Auto-Zoom Prevention | All form inputs, selects, and textareas enforce `font-size >= 16px`. | M1, M2, M4 | Survey Explorer 2 & 3 |
| F15 | Strict Zero `<img>` & Zero `[...]` Guardrails | Strictly 0 `<img>` tags (SVG/CSS only) and 0 square brackets `[...]` in visible UI copy. | M1, M2, M4 | ORIGINAL_REQUEST |
| F16 | Driver Ticket Acceptance ONLY | In driver mode/views: strictly NO ticket creation ("Оформить билет", "Добавить бронь вручную", "Создать рейс"). Driver ONLY accepts/validates tickets, searches, 1-tap calls, views seats, and manages trip lifecycle. | M2 | User Update 2026-10-24T13:56:20Z |
| F17 | Elimination of Role Toggle Switch | Remove the visual toggle switch between carrier and driver from the UI. Dedicated separate experiences for carrier and driver without confusing switchers. | M1 & M2 | User Update 2026-10-24T14:15:35Z |
| F18 | Dedicated Passenger Cabinet | Create `/Users/aleksandr/BusLiner/passenger-cabinet.html`: Active ticket card (route, platform, seat, driver contact, SVG QR boarding pass), BusLiner Miles loyalty balance, past travel history, passenger profile. | M4 | User Update 2026-10-24T14:15:35Z |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | E2E Testing Track | Requirement-driven automated test suite across all features (Tiers 1-4). Outputs `TEST_READY.md`. | none | DONE (Extending for F17 & F18) |
| M1 | Carrier Workspace Polish | `carrier-workspace.html`: Remove role toggle switch, ensure 0 oxblood/burgundy, verify 100% tests pass. | none | IN_PROGRESS |
| M2 | Driver Dashboard Polish | `carrier-dashboard.html`: Remove role toggle switch, ensure 0 oxblood/burgundy, cash vs online payment display, driver trip lifecycle, verify 100% tests pass. | M0 | IN_PROGRESS |
| M4 | Passenger Cabinet Creation | Build `/Users/aleksandr/BusLiner/passenger-cabinet.html` in Quiet Luxury aesthetic with active ticket, SVG QR pass, Miles balance, history, profile, 0 img, 0 brackets, 0 burgundy. | M0 | IN_PROGRESS |
| M3 | Final E2E Test Suite Pass & Verification | 100% E2E test pass across all 3 files, 2x Reviewer approvals, 2x Challenger validations, Forensic Auditor CLEAN verdict. | M0, M1, M2, M4 | PLANNED |

## Code Layout
- `/Users/aleksandr/BusLiner/carrier-workspace.html` — Owned exclusively by Worker 1 in Milestone M1.
- `/Users/aleksandr/BusLiner/carrier-dashboard.html` — Owned exclusively by Worker 2 in Milestone M2.
- `/Users/aleksandr/BusLiner/passenger-cabinet.html` — Owned exclusively by Worker 3 in Milestone M4.
- `/Users/aleksandr/BusLiner/tests/` — Owned exclusively by Test Writer in Milestone M0.
