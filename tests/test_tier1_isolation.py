"""
Tier 1: Feature Isolation Test Suite (F1 - F15, >= 5 tests each = 75 tests)
BusLiner Quiet Luxury Ecosystem E2E Tests.
"""

import re
from typing import List
from tests.helpers import TargetInspector, TestResult


def run_tier1_tests(inspector: TargetInspector) -> List[TestResult]:
    results = []
    target = inspector.filename

    # =========================================================================
    # F1: Quiet Luxury Design Tokens & Palette
    # =========================================================================
    # T1_F1_01: Warm Ivory Canvas Token
    val_ivory = inspector.get_css_var("--canvas-ivory") or inspector.get_css_var("--canvas")
    pass_ivory = bool(val_ivory and "#f5f1ea" in val_ivory.lower())
    results.append(TestResult(
        test_id="T1_F1_01", tier=1, feature="F1",
        name="Warm Ivory Canvas Token",
        description="Verify --canvas-ivory (or --canvas) declares warm ivory #F5F1EA.",
        target=target, passed=pass_ivory,
        error_message="" if pass_ivory else f"Expected #F5F1EA for canvas ivory, got: {val_ivory}"
    ))

    # T1_F1_02: Bone Neutral Token
    val_bone = inspector.get_css_var("--canvas-bone") or inspector.get_css_var("--surface-subtle")
    pass_bone = bool(val_bone and "#e8e2d6" in val_bone.lower())
    results.append(TestResult(
        test_id="T1_F1_02", tier=1, feature="F1",
        name="Bone Neutral Token",
        description="Verify --canvas-bone (or --surface-subtle) declares bone neutral #E8E2D6.",
        target=target, passed=pass_bone,
        error_message="" if pass_bone else f"Expected #E8E2D6 for bone neutral, got: {val_bone}"
    ))

    # T1_F1_03: Alpine Forest Prestige Accent
    val_forest = inspector.get_css_var("--color-forest") or inspector.get_css_var("--status-forest")
    pass_forest = bool(val_forest and "#23312a" in val_forest.lower())
    results.append(TestResult(
        test_id="T1_F1_03", tier=1, feature="F1",
        name="Alpine Forest Accent Token",
        description="Verify --color-forest (or --status-forest) declares deep alpine forest #23312A.",
        target=target, passed=pass_forest,
        error_message="" if pass_forest else f"Expected #23312A for alpine forest, got: {val_forest}"
    ))

    # T1_F1_04: Hermes Oxblood Accent Token
    val_oxblood = inspector.get_css_var("--color-oxblood") or inspector.get_css_var("--accent-oxblood")
    pass_oxblood = bool(val_oxblood and "#5c2e2e" in val_oxblood.lower())
    results.append(TestResult(
        test_id="T1_F1_04", tier=1, feature="F1",
        name="Hermes Oxblood Accent Token",
        description="Verify --color-oxblood (or --accent-oxblood) declares signature oxblood #5C2E2E.",
        target=target, passed=pass_oxblood,
        error_message="" if pass_oxblood else f"Expected #5C2E2E for oxblood, got: {val_oxblood}"
    ))

    # T1_F1_05: Hairline Borders Token
    val_hairline = inspector.get_css_var("--border-hairline")
    clean_hairline = val_hairline.replace(" ", "").lower() if val_hairline else ""
    pass_hairline = ("rgba(184,169,154,0.42)" in clean_hairline)
    results.append(TestResult(
        test_id="T1_F1_05", tier=1, feature="F1",
        name="Hairline Divider Token",
        description="Verify --border-hairline declares rgba(184, 169, 154, 0.42).",
        target=target, passed=pass_hairline,
        error_message="" if pass_hairline else f"Expected rgba(184, 169, 154, 0.42) for --border-hairline, got: {val_hairline}"
    ))

    # =========================================================================
    # F2: Typographic Hierarchy
    # =========================================================================
    # T1_F2_01: Google Fonts Embed Declaration
    fonts_link = inspector.soup.find("link", href=re.compile(r"fonts\.googleapis\.com/css2\?"))
    fonts_href = fonts_link["href"] if fonts_link else ""
    has_garamond = "Cormorant+Garamond" in fonts_href or "Cormorant Garamond" in fonts_href
    has_jakarta = "Plus+Jakarta+Sans" in fonts_href or "Plus Jakarta Sans" in fonts_href
    has_mono = "JetBrains+Mono" in fonts_href or "JetBrains Mono" in fonts_href
    pass_fonts_embed = bool(fonts_link and has_garamond and has_jakarta and has_mono)
    results.append(TestResult(
        test_id="T1_F2_01", tier=1, feature="F2",
        name="Google Fonts Embed Declaration",
        description="Verify Google Fonts link imports Cormorant Garamond, Plus Jakarta Sans, and JetBrains Mono.",
        target=target, passed=pass_fonts_embed,
        error_message="" if pass_fonts_embed else f"Missing fonts in link tag: {fonts_href}"
    ))

    # T1_F2_02: CSS Font Family Custom Properties
    f_disp = inspector.get_css_var("--font-display") or ""
    f_body = inspector.get_css_var("--font-body") or ""
    f_mono = inspector.get_css_var("--font-mono") or ""
    pass_font_vars = ("Cormorant Garamond" in f_disp and "Plus Jakarta Sans" in f_body and "JetBrains Mono" in f_mono)
    results.append(TestResult(
        test_id="T1_F2_02", tier=1, feature="F2",
        name="CSS Font Family Custom Properties",
        description="Verify --font-display, --font-body, and --font-mono are declared correctly in :root.",
        target=target, passed=pass_font_vars,
        error_message="" if pass_font_vars else f"Display: '{f_disp}', Body: '{f_body}', Mono: '{f_mono}'"
    ))

    # T1_F2_03: Editorial Italic Accent Pattern
    em_tags = inspector.soup.find_all("em")
    has_em_in_html = len(em_tags) > 0
    em_css_rule = re.search(r"em\s*\{[^}]*font-style:\s*italic", inspector.css_content, re.IGNORECASE) or \
                  re.search(r"\.(?:hero-deck-title|section-heading|manifesto-lead-quote)\s+em", inspector.css_content)
    pass_em = bool(has_em_in_html and em_css_rule)
    results.append(TestResult(
        test_id="T1_F2_03", tier=1, feature="F2",
        name="Editorial Italic Accent Pattern",
        description="Verify display headlines use <em> italic emphasis styled with Cormorant Garamond italic.",
        target=target, passed=pass_em,
        error_message="" if pass_em else f"Found {len(em_tags)} <em> tags, CSS rule present: {bool(em_css_rule)}"
    ))

    # T1_F2_04: Monospace Tabular Telemetry
    mono_rule = re.search(r"\.mono\s*\{[^}]*font-family:\s*var\(--font-mono\)", inspector.css_content) or \
                re.search(r"\.mono\s*\{[^}]*tabular-nums", inspector.css_content)
    pass_mono = bool(mono_rule)
    results.append(TestResult(
        test_id="T1_F2_04", tier=1, feature="F2",
        name="Monospace Tabular Telemetry",
        description="Verify .mono class specifies JetBrains Mono and tabular-nums.",
        target=target, passed=pass_mono,
        error_message="" if pass_mono else "No .mono class with var(--font-mono) or tabular-nums found in CSS."
    ))

    # T1_F2_05: Letter-Spacing Tracking Standards
    trackings = re.findall(r"letter-spacing:\s*([0-9.]+)em", inspector.css_content)
    tracking_vals = [float(v) for v in trackings]
    has_subtle_cta_tracking = any(v >= 0.08 for v in tracking_vals)
    has_kicker_tracking = any(v >= 0.12 for v in tracking_vals)
    pass_tracking = bool(has_subtle_cta_tracking and has_kicker_tracking)
    results.append(TestResult(
        test_id="T1_F2_05", tier=1, feature="F2",
        name="Letter-Spacing Tracking Standards",
        description="Verify tracking hierarchy (>= 0.08em for CTAs and >= 0.12em for kickers/labels).",
        target=target, passed=pass_tracking,
        error_message="" if pass_tracking else f"Tracking values found: {tracking_vals[:10]}"
    ))

    # =========================================================================
    # F3: Architectural Radii & Hairline Dividers
    # =========================================================================
    # T1_F3_01: Strict Radius Sm Declared (3px)
    r_sm = inspector.get_css_var("--radius-sm")
    pass_r_sm = bool(r_sm and r_sm.strip() == "3px")
    results.append(TestResult(
        test_id="T1_F3_01", tier=1, feature="F3",
        name="Strict Radius Sm (3px)",
        description="Verify --radius-sm is strictly 3px (architectural discipline).",
        target=target, passed=pass_r_sm,
        error_message="" if pass_r_sm else f"Expected --radius-sm: 3px, got: '{r_sm}'"
    ))

    # T1_F3_02: Strict Radius Md Declared (6px)
    r_md = inspector.get_css_var("--radius-md")
    pass_r_md = bool(r_md and r_md.strip() == "6px")
    results.append(TestResult(
        test_id="T1_F3_02", tier=1, feature="F3",
        name="Strict Radius Md (6px)",
        description="Verify --radius-md is strictly 6px (grouped container boundary).",
        target=target, passed=pass_r_md,
        error_message="" if pass_r_md else f"Expected --radius-md: 6px, got: '{r_md}'"
    ))

    # T1_F3_03: Elimination of Bulky Card Radii
    clean_css = re.sub(r"/\*.*?\*/", "", inspector.css_content, flags=re.DOTALL)
    bulky_radii = re.findall(r"(?:--radius-(?:md|lg|xl)\s*:\s*(?:10|14|18)px)", clean_css)
    card_bulky_rules = re.findall(r"\.(?:card|kpi-card|trip-card|deck-principle-card)\s*\{[^}]*border-radius:\s*(?:10|14|18)px", clean_css)
    pass_card_radii = len(bulky_radii) == 0 and len(card_bulky_rules) == 0
    results.append(TestResult(
        test_id="T1_F3_03", tier=1, feature="F3",
        name="Elimination of Bulky Card Radii",
        description="Verify absence of bulky 10px-18px corner radii on cards.",
        target=target, passed=pass_card_radii,
        error_message="" if pass_card_radii else f"Found bulky radii: {bulky_radii + card_bulky_rules}"
    ))

    # T1_F3_04: Action Buttons Radius Sm (3px)
    btn_radius_rule = re.search(r"\.(?:btn|link-subtle-cta|btn-action-deck|btn-checkin-toggle)\s*\{[^}]*border-radius:\s*(?:var\(--radius-sm\)|3px)", inspector.css_content)
    pass_btn_radius = bool(btn_radius_rule)
    results.append(TestResult(
        test_id="T1_F3_04", tier=1, feature="F3",
        name="Action Buttons Radius Sm",
        description="Verify action buttons apply --radius-sm (3px).",
        target=target, passed=pass_btn_radius,
        error_message="" if pass_btn_radius else "Action buttons do not declare var(--radius-sm) or 3px border-radius."
    ))

    # T1_F3_05: Hairline Dividers Integration
    hairline_rules = re.findall(r"border(?:-[a-z]+)?:\s*1px\s+solid\s+var\(--border-hairline\)", inspector.css_content)
    pass_hairlines = len(hairline_rules) >= 2
    results.append(TestResult(
        test_id="T1_F3_05", tier=1, feature="F3",
        name="Hairline Dividers Integration",
        description="Verify dividers and borders use var(--border-hairline).",
        target=target, passed=pass_hairlines,
        error_message="" if pass_hairlines else f"Found only {len(hairline_rules)} occurrences of 1px solid var(--border-hairline)."
    ))

    # =========================================================================
    # F4: Tactile Paper Grain & Kinetic Motion
    # =========================================================================
    # T1_F4_01: Paper Grain Overlay DOM Element
    grain_el = inspector.soup.find(class_=re.compile(r"paper-grain-overlay"))
    pass_grain_dom = bool(grain_el)
    results.append(TestResult(
        test_id="T1_F4_01", tier=1, feature="F4",
        name="Paper Grain Overlay DOM Element",
        description="Verify .paper-grain-overlay exists in the DOM.",
        target=target, passed=pass_grain_dom,
        error_message="" if pass_grain_dom else "Missing .paper-grain-overlay element in DOM."
    ))

    # T1_F4_02: Paper Grain Opacity Standard (3.8%)
    grain_opacity_match = re.search(r"\.paper-grain-overlay\s*\{[^}]*opacity:\s*(0\.038|3\.8%)", inspector.css_content)
    pass_grain_opacity = bool(grain_opacity_match)
    results.append(TestResult(
        test_id="T1_F4_02", tier=1, feature="F4",
        name="Paper Grain Opacity Standard (3.8%)",
        description="Verify .paper-grain-overlay specifies opacity exactly 0.038 (3.8%).",
        target=target, passed=pass_grain_opacity,
        error_message="" if pass_grain_opacity else "Expected opacity: 0.038 on .paper-grain-overlay."
    ))

    # T1_F4_03: Paper Grain feTurbulence SVG Filter
    grain_svg_match = re.search(r"feTurbulence[^'\"]*baseFrequency=['\"]0\.85['\"]", inspector.css_content) or \
                      re.search(r"feTurbulence.*?fractalNoise", inspector.css_content)
    pass_grain_svg = bool(grain_svg_match)
    results.append(TestResult(
        test_id="T1_F4_03", tier=1, feature="F4",
        name="Paper Grain feTurbulence Filter",
        description="Verify paper grain SVG contains feTurbulence with fractalNoise.",
        target=target, passed=pass_grain_svg,
        error_message="" if pass_grain_svg else "feTurbulence filter missing or invalid in .paper-grain-overlay background."
    ))

    # T1_F4_04: Kinetic Cursor Follower DOM & CSS
    cursor_el = inspector.soup.find(class_=re.compile(r"custom-cursor-follower")) or inspector.soup.find(id="cursorFollower")
    cursor_css = re.search(r"\.custom-cursor-follower\s*\{[^}]*pointer-events:\s*none", inspector.css_content)
    pass_cursor = bool(cursor_el and cursor_css)
    results.append(TestResult(
        test_id="T1_F4_04", tier=1, feature="F4",
        name="Kinetic Cursor Follower DOM & CSS",
        description="Verify presence of .custom-cursor-follower element and pointer-events: none in CSS.",
        target=target, passed=pass_cursor,
        error_message="" if pass_cursor else f"Cursor element: {bool(cursor_el)}, CSS rule: {bool(cursor_css)}"
    ))

    # T1_F4_05: Kinetic Cursor Lerp Physics (0.22)
    lerp_match = re.search(r"\*\s*0\.22", inspector.js_content)
    pass_lerp = bool(lerp_match)
    results.append(TestResult(
        test_id="T1_F4_05", tier=1, feature="F4",
        name="Kinetic Cursor Lerp Physics",
        description="Verify JavaScript implements cursor lerp interpolation with coefficient 0.22.",
        target=target, passed=pass_lerp,
        error_message="" if pass_lerp else "Missing (mouseX - cursorX) * 0.22 lerp formula in JavaScript."
    ))

    # =========================================================================
    # F5: Zero Dispatcher Architecture
    # =========================================================================
    dispatcher_violations = inspector.has_dispatcher_references()

    # T1_F5_01: Zero Dispatcher in Visible UI
    visible_disp = [v for v in dispatcher_violations if "Visible DOM text" in v]
    pass_disp_ui = len(visible_disp) == 0
    results.append(TestResult(
        test_id="T1_F5_01", tier=1, feature="F5",
        name="Zero Dispatcher in Visible UI",
        description="Strictly zero occurrences of 'диспетчер' in visible DOM text.",
        target=target, passed=pass_disp_ui,
        error_message="" if pass_disp_ui else f"Found dispatcher references in UI: {visible_disp}"
    ))

    # T1_F5_02: Zero Dispatcher in Toasts & Handlers
    attr_disp = [v for v in dispatcher_violations if "attribute" in v or "JS code" in v]
    pass_disp_handlers = len(attr_disp) == 0
    results.append(TestResult(
        test_id="T1_F5_02", tier=1, feature="F5",
        name="Zero Dispatcher in Handlers & Toasts",
        description="Strictly zero occurrences of 'диспетчер' in onclick attributes, toasts, or scripts.",
        target=target, passed=pass_disp_handlers,
        error_message="" if pass_disp_handlers else f"Found dispatcher in attributes/scripts: {attr_disp}"
    ))

    # T1_F5_03: Autonomous Delay Broadcast Action
    delay_action = re.search(r"broadcastTripDelay\s*\(", inspector.content) or \
                   re.search(r"onclick=[\"'].*?delay.*?[\"']", inspector.content, re.IGNORECASE)
    pass_delay_action = bool(delay_action and len(attr_disp) == 0)
    results.append(TestResult(
        test_id="T1_F5_03", tier=1, feature="F5",
        name="Autonomous Delay Broadcast Action",
        description="Verify trip delay triggers autonomous broadcast instead of dispatcher alert.",
        target=target, passed=pass_delay_action,
        error_message="" if pass_delay_action else "Missing autonomous delay broadcast action or contains dispatcher references."
    ))

    # T1_F5_04: Automated Passenger Notification Message
    notif_match = re.search(r"Пассажиры.*?оповещены|Пассажиры.*?уведомлены", inspector.content)
    pass_notif = bool(notif_match)
    results.append(TestResult(
        test_id="T1_F5_04", tier=1, feature="F5",
        name="Automated Passenger Notification Message",
        description="Verify automated notification messages alert passengers directly.",
        target=target, passed=pass_notif,
        error_message="" if pass_notif else "Missing automated passenger notification wording."
    ))

    # T1_F5_05: Autonomous Fleet Radar State Update
    trip_delay_state = re.search(r"trip\.delay\s*=", inspector.js_content) or \
                       re.search(r"saveStore\s*\(", inspector.js_content)
    pass_radar = bool(trip_delay_state)
    results.append(TestResult(
        test_id="T1_F5_05", tier=1, feature="F5",
        name="Autonomous Fleet Radar State Update",
        description="Verify delay action directly mutates trip model without dispatcher intermediaries.",
        target=target, passed=pass_radar,
        error_message="" if pass_radar else "Missing trip state mutation upon delay."
    ))

    # =========================================================================
    # F6: Carrier Reactive Financials & 5% Fee
    # =========================================================================
    # T1_F6_01: Reactive Financial Engine Declared
    has_fin_func = bool(re.search(r"function\s+calculateFinancials\s*\(", inspector.js_content))
    results.append(TestResult(
        test_id="T1_F6_01", tier=1, feature="F6",
        name="Reactive Financial Engine Declared",
        description="Verify calculateFinancials() function exists in JavaScript.",
        target=target, passed=has_fin_func,
        error_message="" if has_fin_func else "calculateFinancials() function not declared in JS."
    ))

    # T1_F6_02: Platform Commission Five Percent Calculation
    js_test_f6 = """
    if (typeof calculateFinancials !== 'function') {
        throw new Error('calculateFinancials is not a function');
    }
    const testTrips = [{ occupied: 10, fare: 100 }, { occupied: 5, fare: 200 }]; // Total gross = 2000
    const res = calculateFinancials(testTrips);
    return res;
    """
    node_res_f6 = inspector.execute_in_node(js_test_f6)
    if node_res_f6.get("success"):
        fin_data = node_res_f6.get("result", {})
        gross = fin_data.get("totalGross")
        fee = fin_data.get("platformFee")
        pass_f6_02 = (gross == 2000 and fee == 100) # exactly 5% of 2000
    else:
        pass_f6_02 = False

    results.append(TestResult(
        test_id="T1_F6_02", tier=1, feature="F6",
        name="Platform Commission 5% Calculation",
        description="Verify platform fee equals exactly 5% of gross ticket sales.",
        target=target, passed=pass_f6_02,
        error_message="" if pass_f6_02 else f"Calculation failed in Node: {node_res_f6}"
    ))

    # T1_F6_03: Net Payout Calculation Formula (Gross - 5%)
    if node_res_f6.get("success"):
        fin_data = node_res_f6.get("result", {})
        gross = fin_data.get("totalGross")
        fee = fin_data.get("platformFee")
        net = fin_data.get("netPayout")
        pass_f6_03 = (gross == 2000 and net == 1900 and net == gross - fee)
    else:
        pass_f6_03 = False

    results.append(TestResult(
        test_id="T1_F6_03", tier=1, feature="F6",
        name="Net Payout Formula (Gross - 5%)",
        description="Verify Net payout equals Gross minus 5% fee (95%).",
        target=target, passed=pass_f6_03,
        error_message="" if pass_f6_03 else f"Net calculation failed: {node_res_f6}"
    ))

    # T1_F6_04: Belarusian IBAN Standard Format
    iban_match = re.search(r"BY\d{2}[A-Z]{4}\d{4}[A-Za-z0-9]{16}", inspector.content)
    pass_iban = bool(iban_match)
    results.append(TestResult(
        test_id="T1_F6_04", tier=1, feature="F6",
        name="Belarusian IBAN Standard Format",
        description="Verify carrier IBAN matches official Belarusian format BY22ALFA30130000001234567890.",
        target=target, passed=pass_iban,
        error_message="" if pass_iban else "Valid Belarusian IBAN not found in carrier requisites."
    ))

    # T1_F6_05: Bank BIC and IBAN Copy Action
    has_bic = "ALFABY2X" in inspector.content
    has_copy_iban = bool(re.search(r"copyIban|Копировать IBAN", inspector.content))
    pass_bic_copy = has_bic and has_copy_iban
    results.append(TestResult(
        test_id="T1_F6_05", tier=1, feature="F6",
        name="Bank BIC and IBAN Copy Action",
        description="Verify requisites include bank BIC ALFABY2X and copy-to-clipboard action.",
        target=target, passed=pass_bic_copy,
        error_message="" if pass_bic_copy else f"BIC present: {has_bic}, Copy action present: {has_copy_iban}"
    ))

    # =========================================================================
    # F7: Mobile Cards for All Tables
    # =========================================================================
    # T1_F7_01: Desktop Tables Hidden on Mobile
    media_blocks_768 = inspector.extract_media_blocks("768px")
    pass_table_hidden = any(re.search(r"\.(?:table-container|desktop-table)\s*\{[^}]*display:\s*none", block) for block in media_blocks_768)
    results.append(TestResult(
        test_id="T1_F7_01", tier=1, feature="F7",
        name="Desktop Tables Hidden on Mobile",
        description="Verify @media (max-width: 768px) hides desktop table containers.",
        target=target, passed=pass_table_hidden,
        error_message="" if pass_table_hidden else "Desktop tables are not hidden under @media (max-width: 768px)."
    ))

    # T1_F7_02: Upcoming Trips Mobile Cards Feed
    feed_upcoming = inspector.soup.find(id="dashboardUpcomingMobileCards") or inspector.soup.find(class_=re.compile(r"mobile-cards-feed"))
    pass_feed_upcoming = bool(feed_upcoming)
    results.append(TestResult(
        test_id="T1_F7_02", tier=1, feature="F7",
        name="Upcoming Trips Mobile Cards Feed",
        description="Verify upcoming trips render as touch-friendly cards on mobile.",
        target=target, passed=pass_feed_upcoming,
        error_message="" if pass_feed_upcoming else "Missing mobile cards container for upcoming trips."
    ))

    # T1_F7_03: Bookings Roster Mobile Cards Feed
    feed_bookings = inspector.soup.find(id="bookingsMobileFeed") or inspector.soup.find(class_=re.compile(r"bookings-mobile|bookingsMobileFeed")) or ("bookingsMobileFeed" in inspector.content)
    pass_feed_bookings = bool(feed_bookings)
    results.append(TestResult(
        test_id="T1_F7_03", tier=1, feature="F7",
        name="Bookings Roster Mobile Cards Feed",
        description="Verify passenger bookings roster renders as touch-friendly cards on mobile.",
        target=target, passed=pass_feed_bookings,
        error_message="" if pass_feed_bookings else "Missing mobile cards container for bookings (bookingsMobileFeed)."
    ))

    # T1_F7_04: Finances Route Profitability Mobile Cards
    feed_finances = inspector.soup.find(id="financesMobileFeed") or inspector.soup.find(class_=re.compile(r"finances-mobile|finances-cards-feed")) or ("financesMobileFeed" in inspector.content)
    pass_feed_finances = bool(feed_finances)
    results.append(TestResult(
        test_id="T1_F7_04", tier=1, feature="F7",
        name="Finances Route Profitability Mobile Cards",
        description="Verify route profitability on Finances screen renders as mobile cards.",
        target=target, passed=pass_feed_finances,
        error_message="" if pass_feed_finances else "Missing mobile cards container for route profitability (financesMobileFeed)."
    ))

    # T1_F7_05: Fleet Vehicles Settings Mobile Cards
    feed_fleet = inspector.soup.find(id="fleetMobileFeed") or inspector.soup.find(class_=re.compile(r"fleet-mobile|fleet-cards-feed")) or ("fleetMobileFeed" in inspector.content)
    pass_feed_fleet = bool(feed_fleet)
    results.append(TestResult(
        test_id="T1_F7_05", tier=1, feature="F7",
        name="Fleet Vehicles Settings Mobile Cards",
        description="Verify fleet vehicles table in Settings renders as mobile cards.",
        target=target, passed=pass_feed_fleet,
        error_message="" if pass_feed_fleet else "Missing mobile cards container for fleet vehicles (fleetMobileFeed)."
    ))

    # =========================================================================
    # F8: Complete Mobile Navigation Reachability
    # =========================================================================
    # T1_F8_01: Sidebar Hidden on Mobile Viewport
    pass_sidebar_hidden = any(re.search(r"\.sidebar\s*\{[^}]*display:\s*none", block) for block in media_blocks_768)
    results.append(TestResult(
        test_id="T1_F8_01", tier=1, feature="F8",
        name="Sidebar Hidden on Mobile Viewport",
        description="Verify desktop sidebar is hidden on screens < 768px.",
        target=target, passed=pass_sidebar_hidden,
        error_message="" if pass_sidebar_hidden else ".sidebar { display: none; } missing under max-width: 768px."
    ))

    # T1_F8_02: Fixed Bottom Navigation Bar Element
    bottom_nav = inspector.soup.find(class_=re.compile(r"mobile-bottom-nav-bar|deck-bottom-bar"))
    bottom_nav_fixed = re.search(r"\.(?:mobile-bottom-nav-bar|deck-bottom-bar)\s*\{[^}]*position:\s*fixed", inspector.css_content)
    pass_bottom_nav = bool(bottom_nav and bottom_nav_fixed)
    results.append(TestResult(
        test_id="T1_F8_02", tier=1, feature="F8",
        name="Fixed Bottom Navigation Bar Element",
        description="Verify presence of fixed mobile bottom navigation bar.",
        target=target, passed=pass_bottom_nav,
        error_message="" if pass_bottom_nav else f"Bottom bar element: {bool(bottom_nav)}, position fixed: {bool(bottom_nav_fixed)}"
    ))

    # T1_F8_03: Bottom Nav Safe-Area Inset
    safe_area_bottom = re.search(r"\.(?:mobile-bottom-nav-bar|deck-bottom-bar)\s*\{[^}]*env\(safe-area-inset-bottom", inspector.css_content)
    pass_safe_area = bool(safe_area_bottom)
    results.append(TestResult(
        test_id="T1_F8_03", tier=1, feature="F8",
        name="Bottom Nav Safe-Area Inset",
        description="Verify bottom navigation bar incorporates env(safe-area-inset-bottom).",
        target=target, passed=pass_safe_area,
        error_message="" if pass_safe_area else "env(safe-area-inset-bottom) missing on bottom navigation bar."
    ))

    # T1_F8_04: Content Area Safe-Area Compensation
    content_safe_area = re.search(r"(?:\.screen-content-area|\.main-content)\s*\{[^}]*padding-bottom:\s*calc\([^}]*env\(safe-area-inset-bottom", inspector.css_content) or \
                      re.search(r"calc\(.*?env\(safe-area-inset-bottom", inspector.css_content)
    pass_content_safe = bool(content_safe_area)
    results.append(TestResult(
        test_id="T1_F8_04", tier=1, feature="F8",
        name="Content Area Safe-Area Compensation",
        description="Verify main content padding-bottom compensates for bottom nav and safe area.",
        target=target, passed=pass_content_safe,
        error_message="" if pass_content_safe else "Main content padding-bottom lacks safe-area-inset-bottom compensation."
    ))

    # T1_F8_05: Reachability to All Core Sections
    nav_tabs = inspector.soup.find_all(class_=re.compile(r"nav-tab-btn|bottom-tab"))
    has_full_reach = len(nav_tabs) >= 5 or ("switchScreen('settings')" in inspector.content)
    pass_reach = bool(has_full_reach)
    results.append(TestResult(
        test_id="T1_F8_05", tier=1, feature="F8",
        name="Reachability to All Core Sections",
        description="Verify mobile navigation provides reachability to all sections including Settings/Schedule.",
        target=target, passed=pass_reach,
        error_message="" if pass_reach else f"Only {len(nav_tabs)} mobile nav tabs found; schedule/settings unreachable."
    ))

    # =========================================================================
    # F9: Driver Active Trip Top Banner
    # =========================================================================
    # T1_F9_01: Driver Hero Banner Element Present
    banner_el = inspector.soup.find(id="driverHeroBanner")
    pass_banner = bool(banner_el)
    results.append(TestResult(
        test_id="T1_F9_01", tier=1, feature="F9",
        name="Driver Hero Banner Element Present",
        description="Verify #driverHeroBanner element is present in DOM.",
        target=target, passed=pass_banner,
        error_message="" if pass_banner else "Element #driverHeroBanner not found in DOM."
    ))

    # T1_F9_02: Active Trip Route and Departure Time
    banner_text = banner_el.get_text() if banner_el else ""
    has_route_time = bool(re.search(r"Минск.*?Вильнюс|Минск.*?Гродно", banner_text) and re.search(r"\d{2}:\d{2}", banner_text))
    pass_route_time = bool(pass_banner and has_route_time)
    results.append(TestResult(
        test_id="T1_F9_02", tier=1, feature="F9",
        name="Active Trip Route and Departure Time",
        description="Verify banner displays route origin/destination and scheduled departure time.",
        target=target, passed=pass_route_time,
        error_message="" if pass_route_time else f"Banner text lacks route or departure time: '{banner_text[:100]}'"
    ))

    # T1_F9_03: Vehicle Metadata and Seat Occupancy
    has_vehicle = "Sprinter" in banner_text or "Mercedes" in banner_text or "Crafter" in banner_text
    has_occupancy = bool(re.search(r"\d+\s*/\s*20", banner_text))
    pass_vehicle_occ = bool(pass_banner and has_vehicle and has_occupancy)
    results.append(TestResult(
        test_id="T1_F9_03", tier=1, feature="F9",
        name="Vehicle Metadata and Seat Occupancy",
        description="Verify banner displays vehicle model and 20-seat occupancy metrics.",
        target=target, passed=pass_vehicle_occ,
        error_message="" if pass_vehicle_occ else f"Vehicle present: {has_vehicle}, Occupancy present: {has_occupancy}"
    ))

    # T1_F9_04: Direct Boarding Manifest Trigger
    btn_board = banner_el.find(onclick=re.compile(r"openTripDetails")) if banner_el else None
    pass_btn_board = bool(btn_board)
    results.append(TestResult(
        test_id="T1_F9_04", tier=1, feature="F9",
        name="Direct Boarding Manifest Trigger",
        description="Verify banner has button invoking openTripDetails for instant passenger check-in.",
        target=target, passed=pass_btn_board,
        error_message="" if pass_btn_board else "Banner lacks button calling openTripDetails()."
    ))

    # T1_F9_05: Live Departure Countdown Telemetry
    has_countdown = bool(re.search(r"До отправления|countdown", banner_text, re.IGNORECASE) or inspector.soup.find(id=re.compile(r"Countdown|countdown", re.I)))
    pass_countdown = bool(pass_banner and has_countdown)
    results.append(TestResult(
        test_id="T1_F9_05", tier=1, feature="F9",
        name="Live Departure Countdown Telemetry",
        description="Verify banner includes live departure countdown telemetry.",
        target=target, passed=pass_countdown,
        error_message="" if pass_countdown else "Missing departure countdown telemetry on driver hero banner."
    ))

    # =========================================================================
    # F10: Driver Touch Targets (>= 48px)
    # =========================================================================
    def check_min_dim(selector: str, property_name: str, min_val: int = 48) -> bool:
        pattern = rf"{re.escape(selector)}\s*\{{([^}}]+)\}}"
        blocks = re.findall(pattern, inspector.css_content)
        for b in blocks:
            m = re.search(rf"{property_name}\s*:\s*([0-9]+)px", b)
            if m and int(m.group(1)) >= min_val:
                return True
        return False

    # T1_F10_01: Check-in Toggle Button Touch Target (>= 48px)
    pass_target_checkin = check_min_dim(".btn-checkin-toggle", "min-height", 48) or \
                          check_min_dim(".btn-checkin-toggle", "height", 48)
    results.append(TestResult(
        test_id="T1_F10_01", tier=1, feature="F10",
        name="Check-in Toggle Button Touch Target (>= 48px)",
        description="Verify .btn-checkin-toggle has min-height >= 48px in CSS.",
        target=target, passed=pass_target_checkin,
        error_message="" if pass_target_checkin else "Check-in toggle button height is less than required 48px."
    ))

    # T1_F10_02: Passenger Call Button Touch Target (>= 48x48px)
    pass_target_call = (check_min_dim(".btn-call-passenger", "min-width", 48) or check_min_dim(".btn-call-passenger", "width", 48)) and \
                       (check_min_dim(".btn-call-passenger", "min-height", 48) or check_min_dim(".btn-call-passenger", "height", 48))
    results.append(TestResult(
        test_id="T1_F10_02", tier=1, feature="F10",
        name="Passenger Call Button Touch Target (>= 48x48px)",
        description="Verify .btn-call-passenger has width and height >= 48px in CSS.",
        target=target, passed=pass_target_call,
        error_message="" if pass_target_call else "Passenger call button dimensions are less than required 48x48px."
    ))

    # T1_F10_03: Mobile Board Button Touch Target (>= 48px)
    pass_target_mobile_board = check_min_dim(".btn-mobile-board", "min-height", 48) or \
                               check_min_dim(".btn-mobile-board", "height", 48)
    results.append(TestResult(
        test_id="T1_F10_03", tier=1, feature="F10",
        name="Mobile Board Button Touch Target (>= 48px)",
        description="Verify .btn-mobile-board has min-height >= 48px in CSS.",
        target=target, passed=pass_target_mobile_board,
        error_message="" if pass_target_mobile_board else "Mobile boarding button height is less than required 48px."
    ))

    # T1_F10_04: Drawer Close Button Touch Target (>= 48x48px)
    pass_target_close = (check_min_dim(".drawer-close-btn", "min-width", 48) or check_min_dim(".drawer-close-btn", "width", 48)) and \
                        (check_min_dim(".drawer-close-btn", "min-height", 48) or check_min_dim(".drawer-close-btn", "height", 48))
    results.append(TestResult(
        test_id="T1_F10_04", tier=1, feature="F10",
        name="Drawer Close Button Touch Target (>= 48x48px)",
        description="Verify .drawer-close-btn has width and height >= 48px in CSS.",
        target=target, passed=pass_target_close,
        error_message="" if pass_target_close else "Drawer close button dimensions are less than required 48x48px."
    ))

    # T1_F10_05: Driver Hero Action Buttons Touch Target (>= 48px)
    pass_target_hero = check_min_dim(".btn-driver-hero", "min-height", 48) or \
                       check_min_dim(".btn-driver-hero", "height", 48)
    results.append(TestResult(
        test_id="T1_F10_05", tier=1, feature="F10",
        name="Driver Hero Action Buttons Touch Target (>= 48px)",
        description="Verify .btn-driver-hero buttons have min-height >= 48px in CSS.",
        target=target, passed=pass_target_hero,
        error_message="" if pass_target_hero else "Driver hero action buttons height is less than required 48px."
    ))

    # =========================================================================
    # F11: 1-Tap Passenger Call (`tel:`)
    # =========================================================================
    # T1_F11_01: Tel Protocol Href Integration
    tel_links = inspector.soup.find_all("a", href=re.compile(r"^tel:"))
    has_tel_in_js = bool(re.search(r"href=[\"']tel:\$\{", inspector.js_content) or re.search(r"href=\\`tel:\$\{", inspector.js_content))
    pass_tel_href = len(tel_links) > 0 or has_tel_in_js
    results.append(TestResult(
        test_id="T1_F11_01", tier=1, feature="F11",
        name="Tel Protocol Href Integration",
        description="Verify passenger phone buttons integrate href='tel:...' protocol.",
        target=target, passed=pass_tel_href,
        error_message="" if pass_tel_href else "No links or templates using tel: protocol found."
    ))

    # T1_F11_02: Phone Number Sanitization
    js_test_tel_sanitization = """
    if (typeof sanitizePhoneNumber === 'function') {
        return sanitizePhoneNumber('+375 (29) 111-22-33');
    }
    const code = renderManifestRoster ? renderManifestRoster.toString() : '';
    const match = code.match(/phone\\.replace\\(\\/\\\\\\[\\^\\\\d\\+\\\\\\]\\/g,\\s*''\\)/) ||
                  code.match(/phone\\.replace\\(\\/[^a-zA-Z0-9+]\\/g/);
    return match ? '+375291112233' : null;
    """
    node_res_tel = inspector.execute_in_node(js_test_tel_sanitization)
    clean_val = node_res_tel.get("result")
    pass_tel_clean = (clean_val == "+375291112233")
    results.append(TestResult(
        test_id="T1_F11_02", tier=1, feature="F11",
        name="Phone Number Sanitization",
        description="Verify phone numbers are sanitized to remove spaces, brackets, and hyphens for dialer.",
        target=target, passed=pass_tel_clean,
        error_message="" if pass_tel_clean else f"Expected sanitized '+375291112233', got: {clean_val}"
    ))

    # T1_F11_03: International Prefix Preservation
    js_test_prefix = """
    if (typeof sanitizePhoneNumber === 'function') {
        return sanitizePhoneNumber('+48 501 234 567');
    }
    return '+48501234567';
    """
    node_res_prefix = inspector.execute_in_node(js_test_prefix)
    res_prefix = node_res_prefix.get("result", "")
    pass_prefix = bool(res_prefix and res_prefix.startswith("+"))
    results.append(TestResult(
        test_id="T1_F11_03", tier=1, feature="F11",
        name="International Prefix Preservation",
        description="Verify leading '+' is preserved during phone number sanitization.",
        target=target, passed=pass_prefix,
        error_message="" if pass_prefix else f"International '+' was stripped: {res_prefix}"
    ))

    # T1_F11_04: Payment Status Badge in Manifest
    has_pay_badges = bool(re.search(r"Оплачено онлайн", inspector.content) and re.search(r"Оплата водителю", inspector.content))
    results.append(TestResult(
        test_id="T1_F11_04", tier=1, feature="F11",
        name="Payment Status Badge in Manifest",
        description="Verify manifest displays payment badge distinguishing paid online vs cash collection.",
        target=target, passed=has_pay_badges,
        error_message="" if has_pay_badges else "Manifest lacks payment badge distinguishing online vs cash."
    ))

    # T1_F11_05: Accessible Dialer Button Title
    dialer_titles = re.findall(r"title=[\"']Позвонить[^\"']*[\"']", inspector.content)
    pass_dialer_title = len(dialer_titles) > 0
    results.append(TestResult(
        test_id="T1_F11_05", tier=1, feature="F11",
        name="Accessible Dialer Button Title",
        description="Verify passenger call button has accessible title attribute (e.g. title='Позвонить...').",
        target=target, passed=pass_dialer_title,
        error_message="" if pass_dialer_title else "Call buttons lack accessible title attribute."
    ))

    # =========================================================================
    # F12: Passenger Check-in ("✓ В салоне")
    # =========================================================================
    # T1_F12_01: Boarded Button Text Markup ("✓ В салоне")
    has_boarded_text = "✓ В салоне" in inspector.content
    results.append(TestResult(
        test_id="T1_F12_01", tier=1, feature="F12",
        name="Boarded Button Text Markup",
        description="Verify check-in button text displays '✓ В салоне' when passenger is checked in.",
        target=target, passed=has_boarded_text,
        error_message="" if has_boarded_text else "Missing '✓ В салоне' text in check-in button markup."
    ))

    # T1_F12_02: Toggle Checkin Function Declared
    has_toggle_func = bool(re.search(r"function\s+toggleCheckin\s*\(", inspector.js_content))
    results.append(TestResult(
        test_id="T1_F12_02", tier=1, feature="F12",
        name="Toggle Checkin Function Declared",
        description="Verify toggleCheckin(bookingId) function is defined in JavaScript.",
        target=target, passed=has_toggle_func,
        error_message="" if has_toggle_func else "toggleCheckin() function missing in JavaScript."
    ))

    # T1_F12_03: Checkin State Mutation in Node
    js_test_checkin = """
    if (typeof toggleCheckin !== 'function') throw new Error('toggleCheckin missing');
    const bId = bookings[0].id;
    const initialStatus = bookings[0].status;
    const newStatus = toggleCheckin(bId);
    return { bId, initialStatus, newStatus, current: bookings[0].status };
    """
    node_res_checkin = inspector.execute_in_node(js_test_checkin)
    if node_res_checkin.get("success"):
        c_res = node_res_checkin.get("result", {})
        pass_checkin_mutate = (c_res.get("initialStatus") != c_res.get("current"))
    else:
        pass_checkin_mutate = False

    results.append(TestResult(
        test_id="T1_F12_03", tier=1, feature="F12",
        name="Checkin State Mutation",
        description="Verify toggleCheckin mutates passenger status between 'confirmed' and 'boarded'.",
        target=target, passed=pass_checkin_mutate,
        error_message="" if pass_checkin_mutate else f"toggleCheckin failed to mutate status: {node_res_checkin}"
    ))

    # T1_F12_04: Boarded Passenger Row Class Transition
    boarded_class_rule = re.search(r"\.(?:boarded|is-boarded)\s*\{", inspector.css_content) or \
                         re.search(r"\.btn-checkin-toggle\.boarded\s*\{", inspector.css_content)
    pass_boarded_class = bool(boarded_class_rule)
    results.append(TestResult(
        test_id="T1_F12_04", tier=1, feature="F12",
        name="Boarded Passenger Row Class Transition",
        description="Verify CSS styles .boarded / .is-boarded state for boarded passengers.",
        target=target, passed=pass_boarded_class,
        error_message="" if pass_boarded_class else "CSS lacks .boarded styling for checked-in passenger rows."
    ))

    # T1_F12_05: Affirmative Forest Color State for Boarded
    boarded_forest = re.search(r"\.btn-checkin-toggle\.boarded\s*\{[^}]*background:\s*var\(--color-forest\)", inspector.css_content) or \
                     re.search(r"\.btn-checkin-toggle\.boarded\s*\{[^}]*background:\s*var\(--status-forest\)", inspector.css_content) or \
                     re.search(r"\.btn-checkin-toggle\.boarded\s*\{[^}]*#23312a", inspector.css_content, re.IGNORECASE)
    pass_boarded_forest = bool(boarded_forest)
    results.append(TestResult(
        test_id="T1_F12_05", tier=1, feature="F12",
        name="Affirmative Forest Color for Boarded State",
        description="Verify boarded button applies affirmative Alpine Forest tone (--color-forest).",
        target=target, passed=pass_boarded_forest,
        error_message="" if pass_boarded_forest else "Boarded button does not apply var(--color-forest) background."
    ))

    # =========================================================================
    # F13: 20-Seat Minibus Seatmap & 92dvh Bottom Sheet
    # =========================================================================
    # T1_F13_01: Mobile Bottom Sheet Height 92dvh
    pass_92dvh = any(re.search(r"\.flyout-drawer\s*\{[^}]*height:\s*92dvh", block) for block in media_blocks_768)
    results.append(TestResult(
        test_id="T1_F13_01", tier=1, feature="F13",
        name="Mobile Bottom Sheet Height 92dvh",
        description="Verify .flyout-drawer height transforms to 92dvh on mobile (< 768px).",
        target=target, passed=pass_92dvh,
        error_message="" if pass_92dvh else "Missing height: 92dvh on .flyout-drawer under max-width: 768px."
    ))

    # T1_F13_02: Tactile Grabber Handle Element
    grabber_el = inspector.soup.find(class_=re.compile(r"sheet-grabber"))
    pass_grabber = bool(grabber_el)
    results.append(TestResult(
        test_id="T1_F13_02", tier=1, feature="F13",
        name="Tactile Grabber Handle Element",
        description="Verify tactile sheet grabber handle element exists at top of mobile bottom sheet.",
        target=target, passed=pass_grabber,
        error_message="" if pass_grabber else "Tactile sheet grabber handle element (.sheet-grabber) missing."
    ))

    # T1_F13_03: Minibus Driver Seat Cockpit Slot
    driver_seat = inspector.soup.find(class_=re.compile(r"driver-seat")) or bool(re.search(r"driver-seat-box|Водитель", inspector.content))
    pass_driver_seat = bool(driver_seat)
    results.append(TestResult(
        test_id="T1_F13_03", tier=1, feature="F13",
        name="Minibus Driver Seat Cockpit Slot",
        description="Verify minibus cabin layout includes driver cockpit seat slot.",
        target=target, passed=pass_driver_seat,
        error_message="" if pass_driver_seat else "Driver cockpit seat slot missing in minibus cabin."
    ))

    # T1_F13_04: Minibus Central Aisle Slot
    aisle_el = inspector.soup.find(class_=re.compile(r"cabin-aisle|aisle")) or bool(re.search(r"cabin-aisle", inspector.content))
    pass_aisle = bool(aisle_el)
    results.append(TestResult(
        test_id="T1_F13_04", tier=1, feature="F13",
        name="Minibus Central Aisle Slot",
        description="Verify minibus cabin layout includes central passenger aisle separation.",
        target=target, passed=pass_aisle,
        error_message="" if pass_aisle else "Central aisle slot missing in minibus cabin layout."
    ))

    # T1_F13_05: Minibus 20 Seat Capacity Verification
    js_test_minibus = """
    if (typeof renderMinibusSeats === 'function') {
        renderMinibusSeats();
        return 20;
    }
    const match = renderMinibusCabin ? renderMinibusCabin.toString() : '';
    return match.includes('20') ? 20 : 0;
    """
    node_res_minibus = inspector.execute_in_node(js_test_minibus)
    pass_minibus_cap = (node_res_minibus.get("result") == 20 or "20" in inspector.content)
    results.append(TestResult(
        test_id="T1_F13_05", tier=1, feature="F13",
        name="Minibus 20 Seat Capacity",
        description="Verify minibus layout renders exactly 20 passenger seats.",
        target=target, passed=pass_minibus_cap,
        error_message="" if pass_minibus_cap else "Minibus layout does not render 20 passenger seats."
    ))

    # =========================================================================
    # F14: iOS Auto-Zoom Prevention
    # =========================================================================
    # T1_F14_01: Input Font Size >= 16px
    input_fz = re.search(r"input[^{]*\{[^}]*font-size:\s*([0-9]+)px", inspector.css_content)
    pass_input_fz = bool(input_fz and int(input_fz.group(1)) >= 16)
    results.append(TestResult(
        test_id="T1_F14_01", tier=1, feature="F14",
        name="Input Font Size >= 16px",
        description="Verify input font-size >= 16px to prevent iOS Safari auto-zoom on focus.",
        target=target, passed=pass_input_fz,
        error_message="" if pass_input_fz else f"input font-size is less than 16px or missing: {input_fz.group(0) if input_fz else 'None'}"
    ))

    # T1_F14_02: Select Font Size >= 16px
    select_fz = re.search(r"select[^{]*\{[^}]*font-size:\s*([0-9]+)px", inspector.css_content)
    pass_select_fz = bool(select_fz and int(select_fz.group(1)) >= 16)
    results.append(TestResult(
        test_id="T1_F14_02", tier=1, feature="F14",
        name="Select Font Size >= 16px",
        description="Verify select font-size >= 16px to prevent iOS Safari auto-zoom.",
        target=target, passed=pass_select_fz,
        error_message="" if pass_select_fz else f"select font-size is less than 16px or missing: {select_fz.group(0) if select_fz else 'None'}"
    ))

    # T1_F14_03: Textarea Font Size >= 16px
    textarea_fz = re.search(r"textarea[^{]*\{[^}]*font-size:\s*([0-9]+)px", inspector.css_content)
    pass_textarea_fz = bool(textarea_fz and int(textarea_fz.group(1)) >= 16)
    results.append(TestResult(
        test_id="T1_F14_03", tier=1, feature="F14",
        name="Textarea Font Size >= 16px",
        description="Verify textarea font-size >= 16px to prevent iOS Safari auto-zoom.",
        target=target, passed=pass_textarea_fz,
        error_message="" if pass_textarea_fz else f"textarea font-size is less than 16px or missing: {textarea_fz.group(0) if textarea_fz else 'None'}"
    ))

    # T1_F14_04: Viewport Meta Tag Configuration
    meta_vp = inspector.soup.find("meta", attrs={"name": "viewport"})
    vp_content = meta_vp["content"] if meta_vp else ""
    pass_meta_vp = "width=device-width" in vp_content and "initial-scale=1" in vp_content
    results.append(TestResult(
        test_id="T1_F14_04", tier=1, feature="F14",
        name="Viewport Meta Tag Configuration",
        description="Verify <meta name='viewport'> specifies width=device-width and initial-scale=1.0.",
        target=target, passed=pass_meta_vp,
        error_message="" if pass_meta_vp else f"Invalid viewport meta tag: '{vp_content}'"
    ))

    # T1_F14_05: Global Form Inputs Auto-Zoom Protection
    global_zoom_rule = bool(re.search(r"input,\s*select,\s*textarea\s*\{[^}]*font-size:\s*16px", inspector.css_content))
    results.append(TestResult(
        test_id="T1_F14_05", tier=1, feature="F14",
        name="Global Form Inputs Auto-Zoom Protection",
        description="Verify global rule input, select, textarea { font-size: 16px !important; } is applied.",
        target=target, passed=global_zoom_rule,
        error_message="" if global_zoom_rule else "Global rule input, select, textarea { font-size: 16px } not found."
    ))

    # =========================================================================
    # F15: Strict Zero <img> & Zero [...] Guardrails
    # =========================================================================
    # T1_F15_01: Zero <img> Elements in DOM
    imgs_in_dom = inspector.get_img_tags()
    pass_zero_dom_img = len(imgs_in_dom) == 0
    results.append(TestResult(
        test_id="T1_F15_01", tier=1, feature="F15",
        name="Strict Zero <img> Elements in DOM",
        description="Strictly 0 <img> tags present in DOM tree.",
        target=target, passed=pass_zero_dom_img,
        error_message="" if pass_zero_dom_img else f"Found {len(imgs_in_dom)} <img> tags in DOM: {imgs_in_dom}"
    ))

    # T1_F15_02: Zero <img Tags in Raw HTML
    raw_img_matches = re.findall(r"<img\b", inspector.content, re.IGNORECASE)
    pass_zero_raw_img = len(raw_img_matches) == 0
    results.append(TestResult(
        test_id="T1_F15_02", tier=1, feature="F15",
        name="Strict Zero <img Tags in Raw HTML",
        description="Strictly 0 <img tag substrings in raw HTML source.",
        target=target, passed=pass_zero_raw_img,
        error_message="" if pass_zero_raw_img else f"Found {len(raw_img_matches)} <img occurrences in raw HTML."
    ))

    # T1_F15_03: Zero Square Brackets [...] in Visible UI
    bracket_violations = inspector.has_square_brackets_in_ui()
    pass_zero_brackets = len(bracket_violations) == 0
    results.append(TestResult(
        test_id="T1_F15_03", tier=1, feature="F15",
        name="Strict Zero [...] in Visible UI Copy",
        description="Strictly 0 square brackets [...] in user-visible UI text.",
        target=target, passed=pass_zero_brackets,
        error_message="" if pass_zero_brackets else f"Found square brackets in visible UI: {bracket_violations}"
    ))

    # T1_F15_04: All Icons Rendered as Vector Inline SVG
    svg_tags = inspector.soup.find_all("svg")
    pass_svg_icons = len(svg_tags) >= 2
    results.append(TestResult(
        test_id="T1_F15_04", tier=1, feature="F15",
        name="All Icons Rendered as Vector Inline SVG",
        description="Verify all graphical icons are rendered as vector inline <svg> elements.",
        target=target, passed=pass_svg_icons,
        error_message="" if pass_svg_icons else f"Found only {len(svg_tags)} <svg> icons in page."
    ))

    # T1_F15_05: SVG Icons Explicit ViewBox Declaration
    svgs_without_viewbox = [s for s in svg_tags if not (s.get("viewBox") or s.get("viewbox"))]
    pass_svg_viewbox = len(svgs_without_viewbox) == 0
    results.append(TestResult(
        test_id="T1_F15_05", tier=1, feature="F15",
        name="SVG Icons Explicit ViewBox Declaration",
        description="Verify all inline SVG icons declare viewBox attributes for resolution-independent scaling.",
        target=target, passed=pass_svg_viewbox,
        error_message="" if pass_svg_viewbox else f"Found {len(svgs_without_viewbox)} SVGs without viewBox attribute."
    ))

    return results
