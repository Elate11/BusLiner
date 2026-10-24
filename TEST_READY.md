# TEST READY: BusLiner Quiet Luxury E2E Test Suite

**Document Path**: `/Users/aleksandr/BusLiner/TEST_READY.md`  
**Author**: teamwork_preview_test_writer (Milestone M0)  
**Date**: 2026-10-24  
**Status**: APPROVED & PUBLISHED (100% Test Suite Verification via Self-Test Oracle)

---

## 1. Executive Summary

The automated E2E test suite for the **BusLiner Quiet Luxury transformation** has been designed, implemented, and fully verified. It is located at:
`/Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py`

The test suite operates as a strict, opaque-box, requirement-driven verification engine. It evaluates both static presentation (HTML5 semantic structure, CSS `:root` tokens, media queries, layout styling) and reactive interactive behavior (JavaScript functions, math algorithms, state mutations, and dialer actions).

### Certification Metrics
- **Total E2E Tests**: 91 distinct test assertions per target.
- **Coverage**: 15 Features (F1–F15) across 4 Tiers.
- **Self-Test Oracle Pass Rate**: **91/91 (100.0%)** verified against `/Users/aleksandr/BusLiner/tests/synthetic_compliant_fixture.py`.
- **Target Files**:
  - `/Users/aleksandr/BusLiner/carrier-workspace.html`
  - `/Users/aleksandr/BusLiner/carrier-dashboard.html`

---

## 2. Test Architecture & Runner Commands

The suite requires Python 3 with `beautifulsoup4` (already installed) and executes interactive JavaScript tests headlessly via Node.js (`node -e`).

### Quick Start Commands

```bash
# 1. Run all tests against both target files (default)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py

# 2. Run self-test against compliant reference fixture (proves test runner validity)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --selftest

# 3. Run tests specifically against Carrier Workspace (for Worker 1 in M1)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-workspace.html

# 4. Run tests specifically against Driver Dashboard (for Worker 2 in M2)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-dashboard.html

# 5. Filter by Tier or Feature
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --tier 1
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --feature F6

# 6. Structured JSON output for CI/CD pipelines
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --json
```

---

## 3. Feature Inventory Coverage Matrix (91 Tests)

| # | Feature | Requirement Source | Tier 1 (Isolated) | Tier 2 (Boundary) | Tier 3 (Cross) | Tier 4 (Scenario) | Total Tests |
|---|---------|-------------------|:-----------------:|:-----------------:|:--------------:|:-----------------:|:-----------:|
| **F1** | Quiet Luxury Tokens & No #FFFFFF | ORIGINAL_REQUEST R1, R4 | 5 tests (`T1_F1_01-05`) | 2 tests (`T2_01-02`) | 1 test (`T3_05`) | — | 8 |
| **F2** | Typographic Hierarchy (Cormorant, Mono) | ORIGINAL_REQUEST R1 | 5 tests (`T1_F2_01-05`) | — | — | — | 5 |
| **F3** | Architectural Radii (3px, 6px) | ORIGINAL_REQUEST R1 | 5 tests (`T1_F3_01-05`) | — | 1 test (`T3_05`) | — | 6 |
| **F4** | Paper Grain (3.8%) & Kinetic Cursor | ORIGINAL_REQUEST R1 | 5 tests (`T1_F4_01-05`) | — | 1 test (`T3_05`) | — | 6 |
| **F5** | Zero Dispatcher Architecture | ORIGINAL_REQUEST R2 | 5 tests (`T1_F5_01-05`) | — | 1 test (`T3_03`) | 1 test (`T4_03`) | 7 |
| **F6** | Carrier Financials (Gross, 5%, Net IBAN) | ORIGINAL_REQUEST R2 | 5 tests (`T1_F6_01-05`) | 1 test (`T2_07`) | 1 test (`T3_02`) | 1 test (`T4_02`) | 8 |
| **F7** | Mobile Cards for All Tables | ORIGINAL_REQUEST R3 | 5 tests (`T1_F7_01-05`) | — | 1 test (`T3_02`) | — | 6 |
| **F8** | Mobile Bottom Nav Reachability | ORIGINAL_REQUEST R3 | 5 tests (`T1_F8_01-05`) | 1 test (`T2_05`) | 1 test (`T3_02`) | — | 7 |
| **F9** | Driver Active Trip Top Banner | ORIGINAL_REQUEST R2 | 5 tests (`T1_F9_01-05`) | — | 1 test (`T3_03`) | — | 6 |
| **F10** | Driver Touch Targets (>= 48px) | ORIGINAL_REQUEST R2 | 5 tests (`T1_F10_01-05`) | — | 1 test (`T3_01`) | — | 6 |
| **F11** | 1-Tap Passenger Call (`tel:`) | ORIGINAL_REQUEST R2 | 5 tests (`T1_F11_01-05`) | 2 tests (`T2_03,06`) | 1 test (`T3_06`) | 1 test (`T4_01`) | 9 |
| **F12** | Passenger Check-in ("✓ В салоне") | ORIGINAL_REQUEST R2 | 5 tests (`T1_F12_01-05`) | — | 1 test (`T3_04`) | 1 test (`T4_01`) | 7 |
| **F13** | 20-Seat Minibus & 92dvh Bottom Sheet | ORIGINAL_REQUEST R2, R3 | 5 tests (`T1_F13_01-05`) | 1 test (`T2_04`) | 2 tests (`T3_01,04`) | 1 test (`T4_01`) | 9 |
| **F14** | iOS Anti-Zoom (font-size >= 16px) | ORIGINAL_REQUEST R3 | 5 tests (`T1_F14_01-05`) | — | 1 test (`T3_06`) | — | 6 |
| **F15** | Strict Zero `<img>` & Zero `[...]` | ORIGINAL_REQUEST R4 | 5 tests (`T1_F15_01-05`) | — | — | — | 5 |
| **TOTAL** | **Full Ecosystem Matrix** | | **75 Tests** | **7 Tests** | **6 Tests** | **3 Tests** | **91 Tests** |

---

## 4. Baseline Test Run Results (Pre-Transformation Audit)

When executed against the current baseline files, the runner detects the exact defects documented by the survey teams:

```
================================================================================
BUSLINER QUIET LUXURY E2E SUITE - OVERALL SUMMARY
================================================================================
 • carrier-workspace.html        : 64/91 passed ( 70.3%) -> DEFECTS PENDING (Worker M1)
 • carrier-dashboard.html        : 53/91 passed ( 58.2%) -> DEFECTS PENDING (Worker M2)
--------------------------------------------------------------------------------
 GRAND TOTAL: 117/182 passed across 2 targets.
================================================================================
```

### Key Defect Categories Flagged for Resolution:

1. **Dispatcher Residue (`T1_F5_02`, `T3_03`, `T4_03`)**:
   - `Tag <button> attribute 'onclick="showToast(\'Диспетчер предупрежден о задержке рейса на 15 минут\', \'alert\')"'`
   - Target resolution: Replace with `broadcastTripDelay()` notifying passengers via SMS/Push and updating carrier fleet radar.

2. **Reactive Financial Engine (`T1_F6_01-03`, `T2_07`, `T4_02`)**:
   - `calculateFinancials()` missing in JavaScript; revenue and 5% commission values are static HTML strings.
   - Target resolution: Implement reactive `calculateFinancials()` formula calculating Gross, exactly 5% fee, and Net payout. Add bank BIC `ALFABY2X` to IBAN card.

3. **Touch Targets (`T1_F10_01-05`, `T3_01`)**:
   - Boarding buttons (`.btn-checkin-toggle`, `.btn-call-passenger`, `.btn-mobile-board`, `.drawer-close-btn`) are 40–44px.
   - Target resolution: Increase minimum dimensions to `>= 48px`.

4. **Missing Mobile Cards (`T1_F7_04`, `T1_F7_05`)**:
   - Desktop tables for Route Profitability (`screen-finances`) and Fleet Vehicles (`screen-settings`) hide without mobile card alternatives.
   - Target resolution: Add `#financesMobileFeed` and `#fleetMobileFeed` card containers.

5. **Pure White & Color Tokens (`T2_01`, `T1_F1_03`, `T1_F1_04`)**:
   - 12 occurrences of `#FFFFFF` in CSS; Oxblood `#7A2320` and Forest `#2E4F3E` diverge from benchmark.
   - Target resolution: Replace `#FFFFFF` with warm ivory/card neutrals; apply `#5C2E2E` (Oxblood) and `#23312A` (Forest).

6. **Minibus Layout & Tactile Grabber (`T1_F13_02`, `T1_F13_04`)**:
   - 20-seat layout lacks driver seat cockpit slot and central passenger aisle separation; 92dvh Bottom Sheet lacks top grabber pill.
   - Target resolution: Implement realistic Sprinter 20-seat blueprint with driver seat and aisle; add `.sheet-grabber`.

---

## 5. Test File Directory Structure

```
/Users/aleksandr/BusLiner/tests/
├── __init__.py                     # Package declaration
├── helpers.py                      # TargetInspector, DOM/CSS/JS parser, Node test harness
├── synthetic_compliant_fixture.py  # Self-test reference oracle (passes 91/91 tests)
├── test_tier1_isolation.py         # 75 Tier 1 tests (F1–F15 >= 5 each)
├── test_tier2_boundaries.py        # 7 Tier 2 boundary & corner case tests
├── test_tier3_pairwise.py          # 6 Tier 3 pairwise cross-feature tests
├── test_tier4_scenarios.py         # 3 Tier 4 real-world scenario tests
└── run_all_e2e_tests.py            # Primary CLI runner & reporter
```

---

## 6. Next Steps for Implementation Tracks

1. **Worker 1 (Milestone M1)**:
   - Edit `/Users/aleksandr/BusLiner/carrier-workspace.html`.
   - Run `python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-workspace.html` until all 91 tests pass (100%).
2. **Worker 2 (Milestone M2)**:
   - Edit `/Users/aleksandr/BusLiner/carrier-dashboard.html`.
   - Run `python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-dashboard.html` until all 91 tests pass (100%).
3. **Milestone M3 (Final Verification)**:
   - Run `python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py` and confirm exit code 0 across both files.
