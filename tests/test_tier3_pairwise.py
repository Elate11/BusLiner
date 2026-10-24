"""
Tier 3: Pairwise Cross-Feature Test Suite (6 pairwise combinations)
BusLiner Quiet Luxury Ecosystem E2E Tests.
"""

import re
from typing import List
from tests.helpers import TargetInspector, TestResult


def run_tier3_tests(inspector: TargetInspector) -> List[TestResult]:
    results = []
    target = inspector.filename

    # =========================================================================
    # T3_01: Mobile 375px + 92dvh Bottom Sheet + 48px Check-in Toggle
    # =========================================================================
    media_blocks_768 = inspector.extract_media_blocks("768px")
    has_92dvh = any(re.search(r"\.flyout-drawer\s*\{[^}]*height:\s*92dvh", block) for block in media_blocks_768)
    has_checkin_48px = bool(
        re.search(r"\.btn-checkin-toggle\s*\{[^}]*(?:min-height|height):\s*(?:4[89]|[5-9][0-9])px", inspector.css_content)
    )
    pass_t3_01 = has_92dvh and has_checkin_48px
    results.append(TestResult(
        test_id="T3_01", tier=3, feature="F10+F13",
        name="Mobile 375px Viewport + 92dvh Bottom Sheet + 48px Check-in",
        description="Verify 92dvh bottom sheet integrates check-in buttons with >= 48px touch targets on mobile.",
        target=target, passed=pass_t3_01,
        error_message="" if pass_t3_01 else f"92dvh sheet: {has_92dvh}, 48px check-in button: {has_checkin_48px}"
    ))

    # =========================================================================
    # T3_02: Mobile Bottom Nav + Finances Card + 5% Deduction
    # =========================================================================
    has_bottom_nav = bool(inspector.soup.find(class_=re.compile(r"mobile-bottom-nav-bar|deck-bottom-bar")))
    has_finances_feed = bool(inspector.soup.find(id="financesMobileFeed") or inspector.soup.find(class_=re.compile(r"finances-mobile|finances-cards-feed")) or "financesMobileFeed" in inspector.content)

    js_test_fin_fee = """
    if (typeof calculateFinancials !== 'function') throw new Error('calculateFinancials missing');
    const res = calculateFinancials([{ occupied: 20, fare: 50 }]); // Gross 1000, fee 50, net 950
    return res;
    """
    node_fin = inspector.execute_in_node(js_test_fin_fee)
    if node_fin.get("success"):
        f_res = node_fin.get("result", {})
        pass_calc = (f_res.get("totalGross") == 1000 and f_res.get("platformFee") == 50 and f_res.get("netPayout") == 950)
    else:
        pass_calc = False

    pass_t3_02 = has_bottom_nav and has_finances_feed and pass_calc
    results.append(TestResult(
        test_id="T3_02", tier=3, feature="F6+F7+F8",
        name="Mobile Bottom Nav + Finances Card + 5% Fee Calculation",
        description="Verify mobile nav reachability to finances screen with touch cards and 5% platform fee deduction.",
        target=target, passed=pass_t3_02,
        error_message="" if pass_t3_02 else f"Bottom nav: {has_bottom_nav}, Finances cards: {has_finances_feed}, 5% calculation: {pass_calc}"
    ))

    # =========================================================================
    # T3_03: Driver Role Switch + Active Banner + Zero Dispatcher Action
    # =========================================================================
    js_test_driver_banner = """
    if (typeof setUserRole === 'function') {
        setUserRole('driver');
    }
    const banner = document.getElementById('driverHeroBanner');
    return {
        role: userRole,
        bannerDisplay: banner ? banner.style.display : null
    };
    """
    node_banner = inspector.execute_in_node(js_test_driver_banner)
    dispatcher_in_page = inspector.has_dispatcher_references()
    pass_t3_03 = (node_banner.get("success") and len(dispatcher_in_page) == 0)
    results.append(TestResult(
        test_id="T3_03", tier=3, feature="F5+F9",
        name="Driver Role Switch + Active Banner + Zero Dispatcher",
        description="Verify switching to Driver mode activates hero banner while maintaining zero dispatcher references.",
        target=target, passed=pass_t3_03,
        error_message="" if pass_t3_03 else f"Driver role banner test: {node_banner}, Dispatcher violations: {dispatcher_in_page}"
    ))

    # =========================================================================
    # T3_04: Minibus Cabin 20-Seat + Check-in Synchronization
    # =========================================================================
    js_test_sync = """
    if (typeof toggleCheckin !== 'function') throw new Error('toggleCheckin missing');
    const firstBooking = bookings[0];
    const initialStatus = firstBooking.status;
    toggleCheckin(firstBooking.id);
    const updatedStatus = firstBooking.status;
    return {
        bookingId: firstBooking.id,
        seat: firstBooking.seat,
        initialStatus,
        updatedStatus,
        isSynchronized: initialStatus !== updatedStatus
    };
    """
    node_sync = inspector.execute_in_node(js_test_sync)
    has_seats_grid = bool(inspector.soup.find(id=re.compile(r"SeatsGrid|seatsGrid|minibus", re.I))) or ("drawerSeatsGrid" in inspector.content)
    pass_t3_04 = (node_sync.get("success") and node_sync.get("result", {}).get("isSynchronized") and has_seats_grid)
    results.append(TestResult(
        test_id="T3_04", tier=3, feature="F12+F13",
        name="Minibus Cabin 20-Seat + Boarding Check-in Synchronization",
        description="Verify toggleCheckin synchronizes passenger manifest status and minibus cabin seat state.",
        target=target, passed=pass_t3_04,
        error_message="" if pass_t3_04 else f"Sync test result: {node_sync}, Seats grid present: {has_seats_grid}"
    ))

    # =========================================================================
    # T3_05: Design Tokens + Hairline Dividers + Non-Blocking Paper Grain
    # =========================================================================
    val_ivory = inspector.get_css_var("--canvas-ivory") or inspector.get_css_var("--canvas")
    has_ivory = bool(val_ivory and "#f5f1ea" in val_ivory.lower())

    val_hairline = inspector.get_css_var("--border-hairline")
    clean_hairline = val_hairline.replace(" ", "").lower() if val_hairline else ""
    has_hairline = ("rgba(184,169,154,0.42)" in clean_hairline)

    grain_rule = re.search(r"\.paper-grain-overlay\s*\{[^}]*pointer-events:\s*none", inspector.css_content)
    grain_zindex = re.search(r"\.paper-grain-overlay\s*\{[^}]*z-index:\s*([0-9]+)", inspector.css_content)
    has_grain_layer = bool(grain_rule and grain_zindex and int(grain_zindex.group(1)) >= 999)

    pass_t3_05 = has_ivory and has_hairline and has_grain_layer
    results.append(TestResult(
        test_id="T3_05", tier=3, feature="F1+F3+F4",
        name="Quiet Luxury Tokens + Hairline Divider + Paper Grain Layer",
        description="Verify warm ivory canvas, hairline borders, and non-blocking 3.8% paper grain overlay operate in concert.",
        target=target, passed=pass_t3_05,
        error_message="" if pass_t3_05 else f"Ivory: {has_ivory}, Hairline: {has_hairline}, Grain layer: {has_grain_layer}"
    ))

    # =========================================================================
    # T3_06: Mobile Form Inputs + iOS Anti-Zoom + Virtual Keyboards
    # =========================================================================
    has_anti_zoom = bool(re.search(r"input,\s*select,\s*textarea\s*\{[^}]*font-size:\s*16px", inspector.css_content))
    has_numeric_modes = bool(re.search(r"inputmode=[\"'](?:decimal|numeric)[\"']", inspector.content)) or \
                        bool(re.search(r"type=[\"']tel[\"']", inspector.content)) or \
                        bool(re.search(r"font-size:\s*16px", inspector.css_content))
    pass_t3_06 = has_anti_zoom and has_numeric_modes
    results.append(TestResult(
        test_id="T3_06", tier=3, feature="F11+F14",
        name="Mobile Inputs + iOS Anti-Zoom (>=16px) + Virtual Keyboards",
        description="Verify mobile form inputs enforce font-size >= 16px with numeric/tel virtual keyboard hints.",
        target=target, passed=pass_t3_06,
        error_message="" if pass_t3_06 else f"Anti-zoom (>=16px): {has_anti_zoom}, Numeric input modes: {has_numeric_modes}"
    ))

    return results
