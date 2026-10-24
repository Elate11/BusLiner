# E2E Test Infra: BusLiner Quiet Luxury Ecosystem

## Test Philosophy
- Requirement-driven, opaque-box testing based strictly on `ORIGINAL_REQUEST.md` and `PROJECT.md § Feature Inventory`.
- Independent of internal implementation quirks.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinations + Real-World Driver/Carrier Scenarios.

## Feature Inventory Coverage Matrix
| # | Feature | Requirement Source | Tier 1 (Isolated) | Tier 2 (Boundary) | Tier 3 (Cross) | Tier 4 (Scenario) |
|---|---------|-------------------|:-----------------:|:-----------------:|:--------------:|:-----------------:|
| F1 | Quiet Luxury Tokens & No #FFFFFF | ORIGINAL_REQUEST R1, R4 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F2 | Typography (Cormorant, Mono) | ORIGINAL_REQUEST R1 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F3 | Architectural Radii (3px, 6px) | ORIGINAL_REQUEST R1 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F4 | Paper Grain (3.8%) & Kinetic Cursor | ORIGINAL_REQUEST R1 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F5 | Zero Dispatcher Rule | ORIGINAL_REQUEST R2 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F6 | Carrier Financials (Gross, 5%, Net) | ORIGINAL_REQUEST R2 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F7 | Mobile Cards for All Tables | ORIGINAL_REQUEST R3 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F8 | Mobile Bottom Nav Reachability | ORIGINAL_REQUEST R3 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F9 | Driver Active Trip Top Banner | ORIGINAL_REQUEST R2 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F10 | Driver Touch Targets (>= 48px) | ORIGINAL_REQUEST R2 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F11 | 1-Tap Passenger Call (tel:) | ORIGINAL_REQUEST R2 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F12 | Passenger Check-in ("✓ В салоне") | ORIGINAL_REQUEST R2 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F13 | 20-Seat Minibus & 92dvh Bottom Sheet | ORIGINAL_REQUEST R2, R3 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F14 | iOS Anti-Zoom (font-size >= 16px) | ORIGINAL_REQUEST R3 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F15 | Zero <img> & Zero [...] Guardrails | ORIGINAL_REQUEST R4 | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |
| F16 | Driver Ticket Acceptance ONLY (No Ticket Creation) | ORIGINAL_REQUEST Follow-up | ✓ (5 tests) | ✓ (5 tests) | ✓ | ✓ |

## Test Architecture
- Test Runner: Python 3 with Playwright / BeautifulSoup / AST.
- Test Directory: `/Users/aleksandr/BusLiner/tests/`
- Command: `python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py`
- Output: Pass/fail matrix per tier, exit code 0 on complete pass.
