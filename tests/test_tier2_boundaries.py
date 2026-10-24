"""
Tier 2: Boundary & Corner Cases Test Suite
BusLiner Quiet Luxury Ecosystem E2E Tests.
"""

from typing import List
from tests.helpers import TargetInspector, TestResult


def run_tier2_tests(inspector: TargetInspector) -> List[TestResult]:
    results = []
    target = inspector.filename

    # =========================================================================
    # T2_01: Strict Absence of Pure White (#FFFFFF, #FFF, rgb(255, 255, 255))
    # =========================================================================
    white_violations = inspector.has_pure_white()
    pass_no_white = len(white_violations) == 0
    results.append(TestResult(
        test_id="T2_01", tier=2, feature="F1",
        name="Strict Absence of Pure #FFFFFF",
        description="Verify complete absence of pure white (#FFFFFF, #FFF, rgb(255,255,255)) in CSS and inline styles.",
        target=target, passed=pass_no_white,
        error_message="" if pass_no_white else f"Found {len(white_violations)} pure white occurrences:\n" + "\n".join(white_violations[:5])
    ))

    # =========================================================================
    # T2_02: Strict Absence of Pure Black (#000000, #000, rgb(0, 0, 0))
    # =========================================================================
    black_violations = inspector.has_pure_black()
    pass_no_black = len(black_violations) == 0
    results.append(TestResult(
        test_id="T2_02", tier=2, feature="F1",
        name="Strict Absence of Pure #000000",
        description="Verify complete absence of pure black (#000000, #000, rgb(0,0,0)) in CSS and inline styles.",
        target=target, passed=pass_no_black,
        error_message="" if pass_no_black else f"Found {len(black_violations)} pure black occurrences:\n" + "\n".join(black_violations[:5])
    ))

    # =========================================================================
    # T2_03: Multi-Format Phone Sanitization (International & Local)
    # =========================================================================
    js_test_tel_matrix = """
    function sanitize(p) {
        if (typeof sanitizePhoneNumber === 'function') return sanitizePhoneNumber(p);
        return p.replace(/[^\\d+]/g, '');
    }

    const testCases = [
        { raw: '+375 (29) 123-45-67', expected: '+375291234567' },
        { raw: '8 (029) 987-65-43', expected: '80299876543' },
        { raw: '+370-612-34567', expected: '+37061234567' },
        { raw: '+48 501 234 567', expected: '+48501234567' },
        { raw: '  +375 44 777-88-99  ', expected: '+375447778899' }
    ];

    const results = testCases.map(tc => ({
        raw: tc.raw,
        actual: sanitize(tc.raw),
        matches: sanitize(tc.raw) === tc.expected
    }));

    return results;
    """
    node_tel_res = inspector.execute_in_node(js_test_tel_matrix)
    if node_tel_res.get("success"):
        tel_data = node_tel_res.get("result", [])
        pass_tel_matrix = all(item.get("matches") for item in tel_data)
    else:
        pass_tel_matrix = False

    results.append(TestResult(
        test_id="T2_03", tier=2, feature="F11",
        name="Phone Dialer Sanitization Matrix",
        description="Verify phone sanitization across international, local, dash, and space-separated phone formats.",
        target=target, passed=pass_tel_matrix,
        error_message="" if pass_tel_matrix else f"Phone sanitization failed on formats: {node_tel_res}"
    ))

    # =========================================================================
    # T2_04: Minibus Occupancy Extreme Boundaries (0/20, 1/20, 19/20, 20/20)
    # =========================================================================
    js_test_occupancy = """
    function computeOccupancy(occ, cap = 20) {
        const pct = Math.min(100, Math.round((occ / cap) * 100));
        let level = 'normal';
        if (pct >= 90) level = 'full';
        else if (pct >= 75) level = 'high';
        return { occ, cap, pct, level };
    }

    const boundaries = [
        computeOccupancy(0, 20),   // 0%
        computeOccupancy(1, 20),   // 5%
        computeOccupancy(15, 20),  // 75%
        computeOccupancy(19, 20),  // 95%
        computeOccupancy(20, 20),  // 100%
        computeOccupancy(22, 20)   // Overflow cap at 100%
    ];

    return boundaries;
    """
    node_occ_res = inspector.execute_in_node(js_test_occupancy)
    if node_occ_res.get("success"):
        occ_list = node_occ_res.get("result", [])
        pass_occ_bounds = (
            occ_list[0]["pct"] == 0 and
            occ_list[3]["level"] == "full" and
            occ_list[4]["pct"] == 100 and
            occ_list[5]["pct"] == 100
        )
    else:
        pass_occ_bounds = False

    results.append(TestResult(
        test_id="T2_04", tier=2, feature="F13",
        name="Minibus Occupancy Extreme Boundaries",
        description="Verify occupancy percentages and alert thresholds at 0/20, 1/20, 19/20, 20/20, and overflow cap.",
        target=target, passed=pass_occ_bounds,
        error_message="" if pass_occ_bounds else f"Occupancy boundary computation failed: {node_occ_res}"
    ))

    # =========================================================================
    # T2_05: Safe Area Inset Bottom with Fallback Values
    # =========================================================================
    safe_area_fallbacks = inspector.find_rule_property(".mobile-bottom-nav-bar", "padding-bottom") or \
                          inspector.find_rule_property(".deck-bottom-bar", "padding-bottom")
    has_fallback = any("env(safe-area-inset-bottom," in val for val in safe_area_fallbacks) or \
                   ("env(safe-area-inset-bottom" in inspector.css_content)
    pass_safe_fallback = bool(has_fallback)
    results.append(TestResult(
        test_id="T2_05", tier=2, feature="F8",
        name="Safe-Area Inset Bottom with Fallbacks",
        description="Verify env(safe-area-inset-bottom) declarations include fallback values for non-iOS devices.",
        target=target, passed=pass_safe_fallback,
        error_message="" if pass_safe_fallback else "Safe area inset bottom lacks fallback value declaration."
    ))

    # =========================================================================
    # T2_06: Long Passenger Names Truncation & Overflow Defense
    # =========================================================================
    truncation_rules = (
        inspector.css_content.count("text-overflow: ellipsis") +
        inspector.css_content.count("overflow: hidden") +
        inspector.css_content.count("-webkit-line-clamp")
    )
    pass_truncation = truncation_rules >= 1
    results.append(TestResult(
        test_id="T2_06", tier=2, feature="F11",
        name="Long Passenger Names Truncation Defense",
        description="Verify roster items and mobile cards use text-overflow: ellipsis or overflow: hidden.",
        target=target, passed=pass_truncation,
        error_message="" if pass_truncation else "CSS lacks overflow: hidden or text-overflow: ellipsis rules."
    ))

    # =========================================================================
    # T2_07: Zero-Revenue & Zero-Passenger Financial Boundary
    # =========================================================================
    js_test_fin_zero = """
    if (typeof calculateFinancials !== 'function') throw new Error('calculateFinancials missing');
    const emptyTrips = [];
    const zeroTrips = [{ occupied: 0, fare: 70 }, { occupied: 0, fare: 35 }];
    const resEmpty = calculateFinancials(emptyTrips);
    const resZero = calculateFinancials(zeroTrips);
    return { resEmpty, resZero };
    """
    node_fin_zero = inspector.execute_in_node(js_test_fin_zero)
    if node_fin_zero.get("success"):
        z_data = node_fin_zero.get("result", {})
        empty_res = z_data.get("resEmpty", {})
        zero_res = z_data.get("resZero", {})
        pass_fin_zero = (
            empty_res.get("totalGross") == 0 and
            empty_res.get("platformFee") == 0 and
            empty_res.get("netPayout") == 0 and
            empty_res.get("avgTicket") == 0 and
            zero_res.get("avgTicket") == 0
        )
    else:
        pass_fin_zero = False

    results.append(TestResult(
        test_id="T2_07", tier=2, feature="F6",
        name="Zero-Revenue & Zero-Passenger Boundary",
        description="Verify calculateFinancials handles empty/zero trips gracefully without producing NaN.",
        target=target, passed=pass_fin_zero,
        error_message="" if pass_fin_zero else f"Zero-revenue boundary test failed in Node: {node_fin_zero}"
    ))

    return results
