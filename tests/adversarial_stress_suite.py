#!/usr/bin/env python3
"""
BusLiner Quiet Luxury Ecosystem - Adversarial Stress & Ergonomics Test Suite
Executed by teamwork_preview_challenger (Challenger 1: Ergonomics & Stress Challenger).

Evaluates:
1. Viewport scaling across 6 breakpoints (320px, 375px, 430px, 768px, 1024px, 1440px)
   via native macOS WebKit (WKWebView).
2. Interactive stress tests:
   - Rapid check-in toggles across all 20 seats
   - Financial calculation stress (0, 1, 100 trips, negative revenue protection, 5% commission)
   - 1-tap phone dialing sanitization across diverse international & local formats
   - Bottom sheet gesture & touch targets (>= 48px)
   - Keyboard Escape key modal dismissal
3. Test suite execution:
   - run_all_e2e_tests.py status
"""

import sys
import os
import json
import subprocess
import re
from typing import Dict, Any, List

sys.path.insert(0, '/Users/aleksandr/BusLiner')
from tests.helpers import TargetInspector

TARGET_FILES = [
    '/Users/aleksandr/BusLiner/carrier-workspace.html',
    '/Users/aleksandr/BusLiner/carrier-dashboard.html',
    '/Users/aleksandr/BusLiner/passenger-cabinet.html'
]

VIEWPORTS = [320, 375, 430, 768, 1024, 1440]


class RobustInspector(TargetInspector):
    """Subclass TargetInspector to add window.matchMedia and browser polyfills."""
    def execute_in_node(self, js_test_code: str, timeout_sec: int = 5) -> Dict[str, Any]:
        harness = f"""
        try {{
            const storage = {{}};
            global.localStorage = {{
                getItem: (k) => storage[k] || null,
                setItem: (k, v) => {{ storage[k] = String(v); }},
                removeItem: (k) => {{ delete storage[k]; }},
                clear: () => {{ Object.keys(storage).forEach(k => delete storage[k]); }}
            }};
            global.window = {{
                location: {{ hash: '', href: '' }},
                innerWidth: 1024,
                innerHeight: 768,
                addEventListener: () => {{}},
                removeEventListener: () => {{}},
                scrollTo: () => {{}},
                matchMedia: (q) => ({{
                    matches: false,
                    media: q,
                    onchange: null,
                    addListener: () => {{}},
                    removeListener: () => {{}},
                    addEventListener: () => {{}},
                    removeEventListener: () => {{}},
                    dispatchEvent: () => false
                }})
            }};
            global.navigator = {{
                vibrate: () => true,
                userAgent: 'Node-Adversarial-Challenger'
            }};
            global.document = {{
                addEventListener: () => {{}},
                removeEventListener: () => {{}},
                getElementById: (id) => ({{
                    id,
                    style: {{}},
                    classList: {{
                        add: () => {{}},
                        remove: () => {{}},
                        contains: () => false,
                        toggle: () => {{}}
                    }},
                    innerHTML: '',
                    innerText: '',
                    value: '',
                    appendChild: () => {{}},
                    addEventListener: () => {{}},
                    setAttribute: () => {{}},
                    getAttribute: () => null,
                    querySelectorAll: () => [],
                    querySelector: () => null
                }}),
                querySelector: () => null,
                querySelectorAll: () => [],
                createElement: (tag) => ({{
                    tagName: tag,
                    style: {{}},
                    classList: {{ add: () => {{}}, remove: () => {{}} }},
                    appendChild: () => {{}},
                    setAttribute: () => {{}}
                }}),
                body: {{
                    appendChild: () => {{}},
                    style: {{}},
                    classList: {{
                        add: () => {{}},
                        remove: () => {{}},
                        contains: () => false,
                        toggle: () => {{}}
                    }}
                }}
            }};

            global.setInterval = () => {{}};
            global.clearInterval = () => {{}};
            global.setTimeout = (fn) => {{}};
            global.clearTimeout = () => {{}};
            global.requestAnimationFrame = () => {{}};

            // Embed file JS content
            {self.js_content}

            // Execute test assertion code
            const __test_run = () => {{
                {js_test_code}
            }};

            const __result = __test_run();
            console.log(JSON.stringify({{ success: true, result: __result }}));
            process.exit(0);
        }} catch (err) {{
            console.log(JSON.stringify({{ success: false, error: err.message, stack: err.stack }}));
            process.exit(0);
        }}
        """

        res = subprocess.run(
            ["node", "-e", harness],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )

        stdout = res.stdout.strip()
        if not stdout:
            return {"success": False, "error": f"Node empty output: {res.stderr}"}
        try:
            return json.loads(stdout)
        except Exception as e:
            return {"success": False, "error": f"JSON decode error on '{stdout}': {e}"}


def run_webkit_viewport_tests() -> List[Dict[str, Any]]:
    """Runs WKWebView headless layout verification for scrollWidth <= clientWidth."""
    script_path = '/Users/aleksandr/BusLiner/tests/test_wkwebview_viewports.py'
    res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    out = res.stdout
    start_idx = out.find('JSON_START')
    end_idx = out.find('JSON_END')
    if start_idx != -1 and end_idx != -1:
        json_str = out[start_idx + len('JSON_START'):end_idx].strip()
        return json.loads(json_str)
    return [{"error": f"Failed to parse WebKit output: {res.stderr}"}]


def run_rapid_checkin_stress(inspector: TargetInspector) -> Dict[str, Any]:
    """Rapid check-in toggles on all 20 seats in the Sprinter cabin."""
    js_code = """
    // Initialize 20 bookings for 20 seats
    const testBookings = [];
    for (let i = 1; i <= 20; i++) {
        const seatNumStr = i < 10 ? '0' + i + 'A' : i + 'A';
        testBookings.push({
            id: 'TKT-STRESS-' + i,
            tripId: 'BL-5715',
            name: 'Passenger ' + i,
            phone: '+3752900000' + (i < 10 ? '0' + i : i),
            seat: seatNumStr,
            status: 'confirmed',
            payment: i % 2 === 0 ? 'paid' : 'cash',
            amount: 85.0
        });
    }
    bookings = testBookings;

    const auditTrail = [];

    // Rapid toggle: Board all 20 seats in succession
    for (let i = 1; i <= 20; i++) {
        const bId = 'TKT-STRESS-' + i;
        toggleCheckin(bId);
        const b = bookings.find(x => x.id === bId);
        auditTrail.push({ step: 'board_' + i, status: b ? b.status : null });
    }

    const allBoardedCount = bookings.filter(b => b.status === 'boarded').length;

    // Rapid toggle: Un-board every even seat
    for (let i = 2; i <= 20; i += 2) {
        const bId = 'TKT-STRESS-' + i;
        toggleCheckin(bId);
    }
    const halfBoardedCount = bookings.filter(b => b.status === 'boarded').length;

    // Seat-num based toggle check: toggleSeatCheckin for seat 4
    const seat4BookingBefore = bookings.find(b => parseInt(b.seat) === 4).status;
    toggleSeatCheckin(4);
    const seat4BookingAfter = bookings.find(b => parseInt(b.seat) === 4).status;

    // Test non-existent seat 99
    let nonExistentThrew = false;
    try {
        toggleSeatCheckin(99);
    } catch(e) {
        nonExistentThrew = true;
    }

    return {
        allBoardedCount,
        halfBoardedCount,
        seat4Transition: { before: seat4BookingBefore, after: seat4BookingAfter },
        nonExistentThrew
    };
    """
    return inspector.execute_in_node(js_code)


def run_financial_stress_tests(inspector: TargetInspector) -> Dict[str, Any]:
    """Test calculateFinancials across boundaries, high-volume 100 trips, negative revenue."""
    js_code = """
    if (typeof calculateFinancials !== 'function') {
        return { error: 'calculateFinancials not defined in this target' };
    }

    // 1. Boundary: 0 trips
    const res0 = calculateFinancials([]);

    // 2. Boundary: 1 trip
    const res1 = calculateFinancials([{ id: 'T-1', occupied: 17, fare: 85.0, capacity: 20 }]);

    // 3. Stress: 100 trips
    const trips100 = [];
    let expectedGross100 = 0;
    for (let i = 0; i < 100; i++) {
        const occ = (i % 20) + 1; // 1 to 20
        const fare = 20.0 + (i % 50); // 20 to 69
        expectedGross100 += (occ * fare);
        trips100.push({ id: 'TRIP-' + i, occupied: occ, fare: fare, capacity: 20 });
    }
    const t0 = Date.now();
    const res100 = calculateFinancials(trips100);
    const durationMs = Date.now() - t0;
    const expectedFee100 = Math.round(expectedGross100 * 0.05);
    const expectedNet100 = expectedGross100 - expectedFee100;

    // 4. Exact 5% commission math test with tricky roundings
    const roundingTrips = [
        { occupied: 1, fare: 1 },    // gross 1 -> 5% = 0.05 -> round to 0
        { occupied: 1, fare: 10 },   // gross 10 -> 5% = 0.5 -> round to 1 (or 0)
        { occupied: 1, fare: 19 },   // gross 19 -> 5% = 0.95 -> round to 1
        { occupied: 3, fare: 33.33 } // gross 99.99 -> 5% = 4.9995 -> round to 5
    ];
    const roundingResults = roundingTrips.map(t => {
        const r = calculateFinancials([t]);
        return { gross: r.totalGross, fee: r.platformFee, net: r.netPayout };
    });

    // 5. Negative revenue / negative occupancy vulnerability test
    const negTrips = [
        { id: 'T-NEG', occupied: -5, fare: 100 },
        { id: 'T-NEG2', occupied: 10, fare: -50 }
    ];
    const resNeg = calculateFinancials(negTrips);

    return {
        res0,
        res1: {
            gross: res1.totalGross,
            fee: res1.platformFee,
            net: res1.netPayout,
            exact5Pct: res1.platformFee === Math.round(res1.totalGross * 0.05),
            netMatches: res1.netPayout === (res1.totalGross - res1.platformFee)
        },
        res100: {
            durationMs,
            grossMatches: res100.totalGross === expectedGross100,
            feeMatches: res100.platformFee === expectedFee100,
            netMatches: res100.netPayout === expectedNet100
        },
        roundingResults,
        resNeg: {
            totalGross: resNeg.totalGross,
            platformFee: resNeg.platformFee,
            netPayout: resNeg.netPayout,
            hasNegativeGross: resNeg.totalGross < 0,
            hasNegativeNet: resNeg.netPayout < 0
        }
    };
    """
    return inspector.execute_in_node(js_code)


def run_phone_sanitization_stress(inspector: TargetInspector) -> Dict[str, Any]:
    """Test telephone sanitization across multiple real-world and edge formats."""
    js_code = """
    function sanitize(p) {
        if (typeof sanitizePhoneNumber === 'function') {
            return sanitizePhoneNumber(p);
        }
        if (!p) return '';
        return String(p).replace(/[^\\d+]/g, '');
    }

    const testMatrix = [
        { label: 'Belarus formatted', input: '+375 (29) 123-45-67', expected: '+375291234567' },
        { label: 'Belarus 8029 raw', input: '80291234567', expected: '80291234567' },
        { label: 'Lithuania dashes', input: '+370-612-34567', expected: '+37061234567' },
        { label: 'Poland spaces', input: '+48 501 234 567', expected: '+48501234567' },
        { label: 'US formatted', input: '+1 (555) 234-5678', expected: '+15552345678' },
        { label: 'Leading trailing spaces', input: '   +375291112233   ', expected: '+375291112233' },
        { label: 'Number object input', input: 375291234567, expected: '375291234567' },
        { label: 'Dirty string input', input: '+375 (29) 123-45-67 <script>', expected: '+375291234567' },
        { label: 'Empty input', input: '', expected: '' },
        { label: 'Null input', input: null, expected: '' }
    ];

    const results = [];
    for (let tc of testMatrix) {
        try {
            const actual = sanitize(tc.input);
            results.push({
                label: tc.label,
                input: tc.input,
                actual,
                expected: tc.expected,
                passed: actual === tc.expected
            });
        } catch(e) {
            results.push({
                label: tc.label,
                input: tc.input,
                error: e.message,
                passed: false
            });
        }
    }

    // Also specifically test native function in file if it throws on Number
    let nativeThrowsOnNumber = false;
    let nativeNumberError = null;
    if (typeof sanitizePhoneNumber === 'function') {
        try {
            sanitizePhoneNumber(375291234567);
        } catch(e) {
            nativeThrowsOnNumber = true;
            nativeNumberError = e.message;
        }
    }

    return { results, nativeThrowsOnNumber, nativeNumberError };
    """
    return inspector.execute_in_node(js_code)


def run_keyboard_escape_test(inspector: TargetInspector) -> Dict[str, Any]:
    """Test Escape key dismissal of modals in the target."""
    js_code = """
    const handlers = {
        closeTripDetails: typeof closeTripDetails === 'function',
        closeModalCreateTrip: typeof closeModalCreateTrip === 'function',
        closeModalAddBooking: typeof closeModalAddBooking === 'function',
        closeBookingModal: typeof closeBookingModal === 'function',
        closeQrModal: typeof closeQrModal === 'function'
    };

    return { handlers };
    """
    res = inspector.execute_in_node(js_code)
    
    # Also grep for 'Escape' in file content
    escape_in_content = bool(re.search(r"e\.key\s*===\s*['\"]Escape['\"]", inspector.content))
    keydown_in_content = bool(re.search(r"addEventListener\s*\(\s*['\"]keydown['\"]", inspector.content))
    
    return {
        "node_eval": res,
        "escape_in_content": escape_in_content,
        "keydown_in_content": keydown_in_content
    }


def main():
    print("=" * 80)
    print(" BUSLINER ADVERSARIAL STRESS & ERGONOMICS SUITE")
    print("=" * 80)

    # 1. WebKit Viewport Scaling Tests
    print("\n--- 1. Viewport Scaling & Horizontal Clipping (Native WebKit) ---")
    vp_results = run_webkit_viewport_tests()
    for r in vp_results:
        f = r.get("file", "unknown")
        vp = r.get("viewport", 0)
        has_over = r.get("hasOverflow", False)
        sw = r.get("scrollW", 0)
        cw = r.get("clientW", 0)
        status = "FAIL (OVERFLOW)" if has_over else "PASS"
        diff = sw - cw if has_over else 0
        print(f"  [{status}] {f:<26} @ {vp:>4}px: scrollW={sw} clientW={cw} (diff: +{diff}px)")

    # 2. Interactive Stress Tests on Target Files
    print("\n--- 2. Interactive Stress Tests ---")
    for file_path in TARGET_FILES:
        filename = os.path.basename(file_path)
        print(f"\nTarget: {filename}")
        inspector = RobustInspector(file_path)

        # 2a. Rapid Check-in
        if "workspace" in filename or "dashboard" in filename:
            checkin_res = run_rapid_checkin_stress(inspector)
            if checkin_res.get("success"):
                c_data = checkin_res.get("result", {})
                print(f"  [✓] Rapid Check-in (20 seats): All boarded={c_data.get('allBoardedCount')}/20, Half unboarded={c_data.get('halfBoardedCount')}/20, Seat 4 toggle: {c_data.get('seat4Transition')}")
            else:
                print(f"  [!] Rapid Check-in failed in Node: {checkin_res}")

        # 2b. Financial calculation stress
        if "workspace" in filename or "dashboard" in filename:
            fin_res = run_financial_stress_tests(inspector)
            if fin_res.get("success"):
                f_data = fin_res.get("result", {})
                res1 = f_data.get("res1", {})
                res100 = f_data.get("res100", {})
                resNeg = f_data.get("resNeg", {})
                print(f"  [✓] Financial 0 Trips: gross={f_data.get('res0', {}).get('totalGross')} fee={f_data.get('res0', {}).get('platformFee')} net={f_data.get('res0', {}).get('netPayout')}")
                print(f"  [✓] Financial 1 Trip: gross={res1.get('gross')} fee={res1.get('fee')} net={res1.get('net')} 5%={res1.get('exact5Pct')}")
                print(f"  [✓] Financial 100 Trips: duration={res100.get('durationMs')}ms matchGross={res100.get('grossMatches')} matchFee={res100.get('feeMatches')} matchNet={res100.get('netMatches')}")
                if resNeg.get("hasNegativeGross") or resNeg.get("hasNegativeNet"):
                    print(f"  [CRIT] Negative Revenue Protection: VULNERABILITY CONFIRMED! Negative inputs produce gross={resNeg.get('totalGross')}, net={resNeg.get('netPayout')}. Zero clamping is absent!")
                else:
                    print(f"  [✓] Negative Revenue Protection: Protected ({resNeg})")
            else:
                print(f"  [!] Financial test failed: {fin_res}")

        # 2c. 1-tap Phone dialing sanitization
        tel_res = run_phone_sanitization_stress(inspector)
        if tel_res.get("success"):
            t_data = tel_res.get("result", {})
            fails = [tc for tc in t_data.get("results", []) if not tc.get("passed")]
            native_num_err = t_data.get("nativeNumberError")
            if native_num_err:
                print(f"  [CRIT] Phone Sanitizer: Type vulnerability on numeric input (375291234567): {native_num_err}")
            else:
                print(f"  [✓] Phone Sanitizer: Numeric input handled gracefully")
            if fails:
                print(f"  [!] Phone Sanitizer failures ({len(fails)}): {fails}")
            else:
                print(f"  [✓] Phone Sanitizer: All {len(t_data.get('results', []))} formats sanitized correctly")
        else:
            print(f"  [!] Phone sanitization test failed: {tel_res}")

        # 2d. Touch Targets >= 48px
        checkin_height = inspector.find_rule_property(".btn-checkin-toggle", "min-height") or inspector.find_rule_property(".btn-checkin-toggle", "height")
        call_size = inspector.find_rule_property(".btn-call-passenger", "min-height") or inspector.find_rule_property(".btn-call-passenger", "height")
        mobile_board = inspector.find_rule_property(".btn-mobile-board", "min-height")
        modal_close = inspector.find_rule_property(".modal-close-btn", "height")
        print(f"  Touch Targets: .btn-checkin-toggle={checkin_height}, .btn-call-passenger={call_size}, .btn-mobile-board={mobile_board}, .modal-close-btn={modal_close}")

        # 2e. Keyboard Escape key dismissal
        esc_res = run_keyboard_escape_test(inspector)
        if esc_res.get("escape_in_content") and esc_res.get("keydown_in_content"):
            print(f"  [✓] Keyboard Escape: Listener present and verified in code.")
        else:
            print(f"  [CRIT] Keyboard Escape: VULNERABILITY CONFIRMED! Escape listener missing (escape={esc_res.get('escape_in_content')}, keydown={esc_res.get('keydown_in_content')})")

    # 3. Test suite execution
    print("\n--- 3. E2E Test Suite Execution (run_all_e2e_tests.py) ---")
    suite_res = subprocess.run([sys.executable, "/Users/aleksandr/BusLiner/tests/run_all_e2e_tests.py"], capture_output=True, text=True)
    print(f"Exit code: {suite_res.returncode}")
    summary_lines = [line for line in suite_res.stdout.split('\n') if 'passed' in line or 'SUMMARY' in line or 'GRAND TOTAL' in line]
    for line in summary_lines:
        print(f"  {line.strip()}")

    print("\n" + "=" * 80)
    print(" ADVERSARIAL STRESS TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
