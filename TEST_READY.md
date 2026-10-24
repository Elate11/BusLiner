# TEST READY: BusLiner Quiet Luxury E2E Test Suite

**Document Path**: `/Users/aleksandr/BusLiner/TEST_READY.md`  
**Author**: teamwork_preview_test_writer (Milestone M0 — Updated for Palette & Driver Alignment)  
**Date**: 2026-10-24  
**Status**: APPROVED & PUBLISHED (100% Test Suite Verification via Self-Test Oracle: 97/97 Passed)

---

## 1. Executive Summary

The automated E2E test suite for the **BusLiner Quiet Luxury transformation** has been upgraded and aligned with the user's latest critical directives:
1. **Zero Burgundy / Oxblood**: Strict elimination of Burgundy/Oxblood (`#7A2320`, `#5C2E2E`, `#631917`, `#4B2424`) in favor of Deep Alpine Forest (`#23312A` / `#2C3E35`) and Deep Graphite (`#2B2A28`).
2. **Driver Acceptance-Only Architecture**: Driver cockpit strictly restricted to ticket acceptance/check-in, ticket search/validation, 1-tap `tel:` calling, 20-seat minibus occupancy inspection, and trip status controls. Zero ticket creation/booking forms in driver mode.

The test suite is located at:
`/Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py`

### Certification Metrics
- **Total E2E Tests**: 97 distinct test assertions per target.
- **Coverage**: 16 Features (F1–F16) across 4 Tiers.
- **Self-Test Oracle Pass Rate**: **97/97 (100.0%)** verified against `/Users/aleksandr/BusLiner/tests/synthetic_compliant_fixture.py`.
- **Target Files**:
  - `/Users/aleksandr/BusLiner/carrier-workspace.html`
  - `/Users/aleksandr/BusLiner/carrier-dashboard.html`

---

## 2. Test Architecture & Runner Commands

The suite requires Python 3 with `beautifulsoup4` and executes interactive JavaScript tests headlessly via Node.js (`node -e`).

### Quick Start Commands

```bash
# 1. Run all tests against both target files (default)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py

# 2. Run self-test against compliant reference fixture (proves test runner validity: 97/97 pass)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --selftest

# 3. Run tests specifically against Carrier Workspace (for Worker 1 in M1)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-workspace.html

# 4. Run tests specifically against Driver Dashboard (for Worker 2 in M2)
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-dashboard.html

# 5. Filter by Tier or Feature
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --tier 1
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --feature F16
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --feature F1

# 6. Structured JSON output for CI/CD pipelines
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --json
```

---

## 3. Feature Inventory Coverage Matrix (97 Tests)

| # | Feature | Requirement Source | Tier 1 (Isolated) | Tier 2 (Boundary) | Tier 3 (Cross) | Tier 4 (Scenario) | Total Tests |
|---|---------|-------------------|:-----------------:|:-----------------:|:--------------:|:-----------------:|:-----------:|
| **F1** | Quiet Luxury Palette (Deep Forest/Graphite, NO Burgundy/Oxblood) | User Directive 2026-10-24T13:59:07Z | 5 tests (`T1_F1_01-05`) | 2 tests (`T2_01-02`) | 1 test (`T3_05`) | — | 8 |
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
| **F15** | Strict Zero `<img>`, Zero `[...]`, Zero Burgundy/Oxblood | ORIGINAL_REQUEST R4 & User Directive | 6 tests (`T1_F15_01-06`) | — | — | — | 6 |
| **F16** | Driver Ticket Acceptance ONLY (No Ticket Creation) | User Directive 2026-10-24T13:56:20Z | 5 tests (`T1_F16_01-05`) | — | — | — | 5 |
| **TOTAL** | **Full Ecosystem Matrix** | | **81 Tests** | **7 Tests** | **6 Tests** | **3 Tests** | **97 Tests** |

---

## 4. Current Target Audit Status (Prior to Milestone Completion)

```
================================================================================
 BUSLINER QUIET LUXURY E2E SUITE - OVERALL SUMMARY
================================================================================
 • carrier-workspace.html        : 95/97 passed ( 97.9%) -> DEFECTS PENDING (Worker M1)
 • carrier-dashboard.html        : 95/97 passed ( 97.9%) -> DEFECTS PENDING (Worker M2)
--------------------------------------------------------------------------------
 GRAND TOTAL: 190/194 passed across 2 targets.
================================================================================
```

### Remaining Defects to be Resolved by Workers M1 and M2:

1. **`carrier-workspace.html`**:
   - `T1_F1_04`: Oxblood CSS variable `--color-oxblood: #5C2E2E;` must be removed and replaced with Deep Alpine Forest (`#23312A`) / Graphite (`#2B2A28`).
   - `T1_F15_06`: Hex code `#5C2E2E` must be completely removed from the file.

2. **`carrier-dashboard.html`**:
   - `T1_F1_04`: Oxblood CSS variable `--color-oxblood: #5C2E2E;` must be removed and replaced with Deep Alpine Forest (`#23312A`) / Graphite (`#2B2A28`).
   - `T1_F15_06`: Hex codes `#5C2E2E` and `#4B2424` must be completely removed from the file.

All Driver Mode features (F9, F10, F11, F12, F13, F16) and Tier 2–4 tests are already verified 100% compliant and passing!

---

## 5. Test File Directory Structure

```
/Users/aleksandr/BusLiner/tests/
├── __init__.py                     # Package declaration
├── helpers.py                      # TargetInspector, DOM/CSS/JS parser, Node test harness, oxblood detector
├── synthetic_compliant_fixture.py  # Self-test reference oracle (passes 97/97 tests - 100%)
├── test_tier1_isolation.py         # 81 Tier 1 tests (F1–F16 >= 5 each)
├── test_tier2_boundaries.py        # 7 Tier 2 boundary & corner case tests
├── test_tier3_pairwise.py          # 6 Tier 3 pairwise cross-feature tests
├── test_tier4_scenarios.py         # 3 Tier 4 real-world scenario tests
└── run_all_e2e_tests.py            # Primary CLI runner & reporter
```

---

## 6. Verification and Execution Instructions

To verify test suite soundness independently:

```bash
# Run test suite oracle self-test (must produce exit code 0):
python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --selftest
```
