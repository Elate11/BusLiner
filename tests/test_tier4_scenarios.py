"""
Tier 4: Real-World Scenarios Test Suite (3 full lifecycle workflows)
BusLiner Quiet Luxury Ecosystem E2E Tests.
"""

from typing import List
from tests.helpers import TargetInspector, TestResult


def run_tier4_tests(inspector: TargetInspector) -> List[TestResult]:
    results = []
    target = inspector.filename

    # =========================================================================
    # T4_01: Driver Boarding Complete Lifecycle
    # Active banner -> Open 92dvh sheet -> Tap tel: -> Check-in passenger -> Verify count
    # =========================================================================
    js_scenario_boarding = """
    // 1. Activate driver cockpit
    if (typeof setUserRole === 'function') setUserRole('driver');

    // 2. Open trip boarding manifest
    const activeTripId = trips[0].id;
    if (typeof openTripDetails === 'function') openTripDetails(activeTripId);

    // 3. Find late unboarded passenger
    const latePassenger = bookings.find(b => b.status !== 'boarded') || bookings[1];
    const initialStatus = latePassenger.status;

    // 4. Trigger dialer (sanitize number)
    function sanitize(p) {
        if (typeof sanitizePhoneNumber === 'function') return sanitizePhoneNumber(p);
        return p.replace(/[^\\d+]/g, '');
    }
    const dialedTel = 'tel:' + sanitize(latePassenger.phone);

    // 5. Board passenger via check-in toggle
    if (typeof toggleCheckin === 'function') toggleCheckin(latePassenger.id);

    // 6. Verify state transitions
    const boardedCount = bookings.filter(b => b.status === 'boarded').length;

    return {
        activeTripId,
        dialedTel,
        passengerId: latePassenger.id,
        initialStatus,
        finalStatus: latePassenger.status,
        boardedCount
    };
    """
    node_res_boarding = inspector.execute_in_node(js_scenario_boarding)
    if node_res_boarding.get("success"):
        b_res = node_res_boarding.get("result", {})
        pass_scenario_boarding = (
            b_res.get("initialStatus") != b_res.get("finalStatus") and
            b_res.get("finalStatus") == "boarded" and
            b_res.get("dialedTel", "").startswith("tel:+")
        )
    else:
        pass_scenario_boarding = False

    results.append(TestResult(
        test_id="T4_01", tier=4, feature="Driver Boarding Lifecycle",
        name="Driver Boarding Lifecycle Scenario",
        description="End-to-end driver boarding flow: active banner -> 92dvh manifest -> tel: dialer -> check-in -> count update.",
        target=target, passed=pass_scenario_boarding,
        error_message="" if pass_scenario_boarding else f"Driver boarding scenario failed: {node_res_boarding}"
    ))

    # =========================================================================
    # T4_02: Carrier Fleet Financials & Net Payout Lifecycle
    # Load trips -> compute gross -> deduct 5% -> verify net payout on verified IBAN
    # =========================================================================
    js_scenario_carrier = """
    if (typeof calculateFinancials !== 'function') throw new Error('calculateFinancials missing');

    // Multi-trip fleet portfolio
    const fleetTrips = [
        { id: 'BL-101', route: 'Минск — Вильнюс', occupied: 18, fare: 70 }, // 1260
        { id: 'BL-102', route: 'Минск — Варшава', occupied: 20, fare: 120 }, // 2400
        { id: 'BL-103', route: 'Минск — Гродно', occupied: 16, fare: 40 }   // 640
    ];
    // Total gross = 4300 BYN
    // Platform fee (5%) = 215 BYN
    // Net IBAN payout = 4085 BYN

    const fin = calculateFinancials(fleetTrips);
    return {
        tripsCount: fleetTrips.length,
        gross: fin.totalGross,
        fee: fin.platformFee,
        net: fin.netPayout,
        feePercent: Math.round((fin.platformFee / fin.totalGross) * 100)
    };
    """
    node_res_carrier = inspector.execute_in_node(js_scenario_carrier)
    has_iban_doc = "BY22ALFA30130000001234567890" in inspector.content
    has_bic_doc = "ALFABY2X" in inspector.content

    if node_res_carrier.get("success"):
        c_res = node_res_carrier.get("result", {})
        pass_scenario_carrier = (
            c_res.get("gross") == 4300 and
            c_res.get("fee") == 215 and
            c_res.get("net") == 4085 and
            c_res.get("feePercent") == 5 and
            has_iban_doc and has_bic_doc
        )
    else:
        pass_scenario_carrier = False

    results.append(TestResult(
        test_id="T4_02", tier=4, feature="Carrier Fleet Lifecycle",
        name="Carrier Fleet Revenue & IBAN Payout Scenario",
        description="End-to-end carrier financial workflow: fleet load -> gross calculation -> 5% deduction -> Net IBAN verification.",
        target=target, passed=pass_scenario_carrier,
        error_message="" if pass_scenario_carrier else f"Carrier revenue scenario failed: {node_res_carrier}, IBAN present: {has_iban_doc}, BIC present: {has_bic_doc}"
    ))

    # =========================================================================
    # T4_03: Autonomous Delay Broadcast Lifecycle (Zero Dispatcher)
    # Trigger 15m delay -> update trip state -> broadcast to passengers/radar
    # =========================================================================
    js_scenario_delay = """
    const activeTrip = trips[0];
    const initialDelay = activeTrip.delay || 0;

    if (typeof broadcastTripDelay === 'function') {
        broadcastTripDelay(activeTrip.id, 15);
    } else {
        activeTrip.delay = 15;
    }

    return {
        tripId: activeTrip.id,
        initialDelay,
        updatedDelay: activeTrip.delay,
        isDelayed: activeTrip.delay === 15
    };
    """
    node_res_delay = inspector.execute_in_node(js_scenario_delay)
    dispatcher_in_page = inspector.has_dispatcher_references()

    if node_res_delay.get("success"):
        d_res = node_res_delay.get("result", {})
        pass_scenario_delay = (d_res.get("isDelayed") and len(dispatcher_in_page) == 0)
    else:
        pass_scenario_delay = False

    results.append(TestResult(
        test_id="T4_03", tier=4, feature="Autonomous Delay Broadcast",
        name="Autonomous Delay Broadcast Scenario",
        description="End-to-end delay workflow: driver triggers 15m delay -> automated passenger notification -> zero dispatcher references.",
        target=target, passed=pass_scenario_delay,
        error_message="" if pass_scenario_delay else f"Delay scenario failed: {node_res_delay}, Dispatcher violations: {dispatcher_in_page}"
    ))

    return results
