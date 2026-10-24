#!/usr/bin/env python3
"""
BusLiner Quiet Luxury Ecosystem - Comprehensive E2E Test Runner
Requirement-driven, opaque-box test suite for Quiet Luxury transformation.
Covers 16 features across 4 tiers (97 total tests).

Usage:
  python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py
  python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-workspace.html
  python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --target carrier-dashboard.html
  python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --tier 1
  python3 /Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py --selftest
"""

import sys
import os
import argparse
import json
from typing import List, Dict

# Ensure tests module is importable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tests.helpers import TargetInspector, TestResult
from tests.test_tier1_isolation import run_tier1_tests
from tests.test_tier2_boundaries import run_tier2_tests
from tests.test_tier3_pairwise import run_tier3_tests
from tests.test_tier4_scenarios import run_tier4_tests
from tests.synthetic_compliant_fixture import SYNTHETIC_COMPLIANT_HTML


def run_tests_for_target(inspector: TargetInspector, tier_filter: str = "all", feature_filter: str = "all") -> List[TestResult]:
    all_results: List[TestResult] = []

    # Tier 1
    if tier_filter in ("all", "1"):
        t1_results = run_tier1_tests(inspector)
        if feature_filter != "all":
            t1_results = [r for r in t1_results if r.feature == feature_filter]
        all_results.extend(t1_results)

    # Tier 2
    if tier_filter in ("all", "2"):
        t2_results = run_tier2_tests(inspector)
        if feature_filter != "all":
            t2_results = [r for r in t2_results if feature_filter in r.feature]
        all_results.extend(t2_results)

    # Tier 3
    if tier_filter in ("all", "3"):
        t3_results = run_tier3_tests(inspector)
        if feature_filter != "all":
            t3_results = [r for r in t3_results if feature_filter in r.feature]
        all_results.extend(t3_results)

    # Tier 4
    if tier_filter in ("all", "4"):
        t4_results = run_tier4_tests(inspector)
        all_results.extend(t4_results)

    return all_results


def print_formatted_report(target_name: str, results: List[TestResult], verbose: bool = False):
    print("\n" + "=" * 80)
    print(f" TARGET: {target_name}")
    print("=" * 80)

    # Group by Tier
    tiers = {1: [], 2: [], 3: [], 4: []}
    for r in results:
        tiers[r.tier].append(r)

    tier_names = {
        1: "TIER 1: FEATURE ISOLATION TESTS (F1 - F16, >= 5 each)",
        2: "TIER 2: BOUNDARY & CORNER CASES",
        3: "TIER 3: PAIRWISE CROSS-FEATURE TESTS",
        4: "TIER 4: REAL-WORLD SCENARIOS"
    }

    for tier_num in sorted(tiers.keys()):
        tier_list = tiers[tier_num]
        if not tier_list:
            continue
        tier_passed = sum(1 for r in tier_list if r.passed)
        tier_total = len(tier_list)
        pct = (tier_passed / tier_total * 100) if tier_total > 0 else 0
        status_symbol = "✓" if tier_passed == tier_total else "✗"

        print(f"\n--- [{status_symbol}] {tier_names[tier_num]} ({tier_passed}/{tier_total} passed - {pct:.1f}%) ---")

        # Group by feature if Tier 1
        if tier_num == 1:
            features = {}
            for r in tier_list:
                features.setdefault(r.feature, []).append(r)
            for feat, f_tests in sorted(features.items()):
                f_pass = sum(1 for r in f_tests if r.passed)
                f_tot = len(f_tests)
                f_sym = "✓" if f_pass == f_tot else "✗"
                print(f"  [{f_sym}] Feature {feat} ({f_pass}/{f_tot}):")
                for r in f_tests:
                    mark = "  ✓" if r.passed else "  ✗"
                    print(f"    {mark} [{r.test_id}] {r.name}")
                    if not r.passed and (verbose or True):
                        # print indent error
                        print(f"        -> REASON: {r.error_message}")
        else:
            for r in tier_list:
                mark = "✓" if r.passed else "✗"
                feat_tag = f"[{r.feature}] " if r.feature else ""
                print(f"  [{mark}] [{r.test_id}] {feat_tag}{r.name}")
                if not r.passed:
                    print(f"      -> REASON: {r.error_message}")


def main():
    parser = argparse.ArgumentParser(description="BusLiner Quiet Luxury E2E Test Runner")
    parser.add_argument("--target", choices=["all", "carrier-workspace.html", "carrier-dashboard.html"], default="all",
                        help="Select test target file (default: all)")
    parser.add_argument("--tier", choices=["all", "1", "2", "3", "4"], default="all",
                        help="Filter tests by Tier (default: all)")
    parser.add_argument("--feature", default="all",
                        help="Filter tests by Feature, e.g. F1, F6 (default: all)")
    parser.add_argument("--selftest", action="store_true",
                        help="Run test suite against synthetic compliant Quiet Luxury reference fixture")
    parser.add_argument("--json", action="store_true",
                        help="Output results in JSON format")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose output mode")

    args = parser.parse_args()

    # Self-test mode verifies the test runner and all test assertions against the oracle
    if args.selftest:
        print("\n" + "=" * 80)
        print(" RUNNING SELF-TEST: Validating E2E test suite against synthetic compliant fixture")
        print("=" * 80)
        inspector = TargetInspector(file_path="", raw_content=SYNTHETIC_COMPLIANT_HTML)
        results = run_tests_for_target(inspector, args.tier, args.feature)
        print_formatted_report("Synthetic Compliant Reference Fixture", results, args.verbose)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        print("\n" + "=" * 80)
        print(f" SELF-TEST SUMMARY: Total: {total} | Passed: {passed} | Failed: {failed}")
        print("=" * 80)
        if failed == 0:
            print(f"\n>>> SELF-TEST SUCCESS: All {total} E2E tests verified 100% sound and passing! <<<\n")
            sys.exit(0)
        else:
            print(f"\n>>> SELF-TEST FAILED: {failed} tests failed on compliant fixture! <<<\n")
            sys.exit(1)

    # Standard execution against target files
    targets = []
    if args.target in ("all", "carrier-workspace.html"):
        targets.append(os.path.join(BASE_DIR, "carrier-workspace.html"))
    if args.target in ("all", "carrier-dashboard.html"):
        targets.append(os.path.join(BASE_DIR, "carrier-dashboard.html"))

    all_target_results = {}
    grand_total = 0
    grand_passed = 0
    grand_failed = 0

    for target_path in targets:
        target_name = os.path.basename(target_path)
        if not os.path.exists(target_path):
            print(f"ERROR: Target file not found: {target_path}", file=sys.stderr)
            sys.exit(2)

        inspector = TargetInspector(file_path=target_path)
        results = run_tests_for_target(inspector, args.tier, args.feature)
        all_target_results[target_name] = results

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        grand_total += total
        grand_passed += passed
        grand_failed += failed

        if not args.json:
            print_formatted_report(target_name, results, args.verbose)

    if args.json:
        output_data = {
            "grand_total": grand_total,
            "grand_passed": grand_passed,
            "grand_failed": grand_failed,
            "targets": {}
        }
        for t_name, r_list in all_target_results.items():
            output_data["targets"][t_name] = [
                {
                    "test_id": r.test_id,
                    "tier": r.tier,
                    "feature": r.feature,
                    "name": r.name,
                    "passed": r.passed,
                    "error_message": r.error_message
                }
                for r in r_list
            ]
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
        sys.exit(0 if grand_failed == 0 else 1)

    # Master summary
    print("\n" + "=" * 80)
    print(" BUSLINER QUIET LUXURY E2E SUITE - OVERALL SUMMARY")
    print("=" * 80)
    for t_name, r_list in all_target_results.items():
        t_total = len(r_list)
        t_pass = sum(1 for r in r_list if r.passed)
        t_fail = t_total - t_pass
        pct = (t_pass / t_total * 100) if t_total > 0 else 0
        status = "PASSED" if t_fail == 0 else "DEFECTS PENDING (Workers M1/M2)"
        print(f" • {t_name:30}: {t_pass:2d}/{t_total:2d} passed ({pct:5.1f}%) -> {status}")

    print("-" * 80)
    print(f" GRAND TOTAL: {grand_passed}/{grand_total} passed across {len(targets)} targets.")
    print("=" * 80)

    if grand_failed == 0:
        print("\n>>> ALL E2E TESTS PASSED (Exit code 0) <<<\n")
        sys.exit(0)
    else:
        print(f"\n>>> TEST RUN COMPLETE: {grand_failed} defects identified for milestone transformation (Exit code 1) <<<\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
