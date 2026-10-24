"""
Synthetic Fully Compliant BusLiner Quiet Luxury Fixture.
Serves as an oracle for self-testing and verification of all 91 E2E tests.
Strictly adheres to ORIGINAL_REQUEST.md, PROJECT.md, and survey_aura_style.md.
"""

SYNTHETIC_COMPLIANT_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
  <meta name="theme-color" content="#F5F1EA">
  <title>BusLiner • Кабинет перевозчика & Пульт водителя</title>

  <!-- Google Fonts Embed: Cormorant Garamond, Plus Jakarta Sans, JetBrains Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">

  <style>
    /* Quiet Luxury Tokens */
    :root {
      /* Warm Neutrals */
      --canvas-ivory: #F5F1EA;
      --canvas-bone: #E8E2D6;
      --canvas-sand: #D9CDB8;
      --canvas-stone: #CEBEA5;
      --surface-card: #FBF9F5;
      --surface-subtle: #E8E2D6;
      --surface-elevated: #FAF8F5;

      /* Deep Prestige Accents */
      --color-forest: #23312A;
      --color-forest-surface: #2C3E35;
      --color-oxblood: #5C2E2E;
      --color-oxblood-surface: #4B2424;
      --color-graphite: #2B2A28;
      --color-graphite-dark: #1E1D1B;

      /* Semantic Status */
      --status-forest: #23312A;
      --status-forest-bg: #EAEFEA;
      --accent-oxblood: #5C2E2E;

      /* Typography */
      --font-display: 'Cormorant Garamond', Garamond, Georgia, serif;
      --font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', SFMono-Regular, monospace;

      /* Typography Neutrals */
      --text-graphite: #2B2A28;
      --text-primary: #2B2A28;
      --text-muted: #5C5852;
      --text-faint: #8A847C;
      --text-light-primary: #F5F1EA;

      /* Architectural Hairline Boundaries */
      --border-taupe: #B8A99A;
      --border-hairline: rgba(184, 169, 154, 0.42);
      --border-subtle: rgba(184, 169, 154, 0.24);

      /* Strict Architectural Radii */
      --radius-sm: 3px;
      --radius-md: 6px;
      --radius-lg: 12px;
      --radius-pill: 9999px;

      /* Kinetic Motion Curves */
      --ease-drive: cubic-bezier(0.22, 1, 0.36, 1);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--canvas-ivory);
      color: var(--text-primary);
      font-family: var(--font-body);
      font-size: 16px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    /* iOS Auto-Zoom Prevention */
    input, select, textarea {
      font-size: 16px !important;
      font-family: var(--font-body);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
      background: var(--surface-card);
      color: var(--text-primary);
    }

    /* Display Typography & Italic Emphasis */
    .hero-deck-title, .section-heading {
      font-family: var(--font-display);
      letter-spacing: 0.08em;
      font-weight: 500;
    }

    .hero-deck-title em, .section-heading em {
      font-family: var(--font-display);
      font-style: italic;
      font-weight: 400;
      color: var(--color-oxblood);
    }

    /* Monospace Telemetry & Tracking */
    .mono {
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
    }

    .meta-micro-tag {
      font-family: var(--font-mono);
      letter-spacing: 0.05em;
    }

    .link-subtle-cta {
      font-family: var(--font-body);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-weight: 600;
      border: 1px solid var(--border-taupe);
      border-radius: var(--radius-sm);
      padding: 9px 18px;
      min-height: 48px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
      color: var(--text-primary);
    }

    .hero-deck-badge, .brand-meta-badge {
      font-family: var(--font-mono);
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    .footer-section-kicker {
      font-family: var(--font-mono);
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }

    /* Artisanal SVG Paper Grain Overlay (3.8% opacity) */
    .paper-grain-overlay {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 9999;
      opacity: 0.038;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 250 250' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    }

    /* Kinetic Lerp Cursor Follower */
    .custom-cursor-follower {
      position: fixed;
      top: 0;
      left: 0;
      width: 26px;
      height: 26px;
      border: 1px solid var(--border-taupe);
      border-radius: 50%;
      pointer-events: none;
      z-index: 10000;
      transform: translate(-50%, -50%);
      opacity: 0.85;
      transition: width 0.28s var(--ease-drive), height 0.28s var(--ease-drive);
    }

    /* Architectural Cards & Radii */
    .deck-principle-card, .card, .kpi-card, .trip-card, .feed-card {
      background: var(--surface-card);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius-sm);
      padding: 24px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .roster-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Touch Targets >= 48px */
    .btn-checkin-toggle {
      min-height: 48px;
      padding: 0 18px;
      font-size: 14px;
      font-weight: 700;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
      background: var(--canvas-bone);
      color: var(--text-primary);
      cursor: pointer;
    }

    .btn-checkin-toggle.boarded {
      background: var(--color-forest);
      color: var(--canvas-ivory);
      border-color: var(--color-forest);
    }

    .btn-call-passenger {
      width: 48px;
      height: 48px;
      min-width: 48px;
      min-height: 48px;
      border-radius: var(--radius-sm);
      background: var(--surface-subtle);
      border: 1px solid var(--border-hairline);
      color: var(--color-forest);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      text-decoration: none;
    }

    .btn-mobile-board {
      min-height: 48px;
      padding: 0 16px;
      font-size: 14px;
      font-weight: 700;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
    }

    .drawer-close-btn {
      width: 48px;
      height: 48px;
      min-width: 48px;
      min-height: 48px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
      background: var(--surface-subtle);
      cursor: pointer;
    }

    .btn-driver-hero {
      min-height: 48px;
      padding: 0 20px;
      border-radius: var(--radius-sm);
      font-weight: 600;
      border: 1px solid var(--border-hairline);
      cursor: pointer;
    }

    /* Driver Active Trip Top Banner */
    #driverHeroBanner {
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: var(--color-forest);
      color: var(--canvas-ivory);
      padding: 20px;
      border-radius: var(--radius-sm);
      margin-bottom: 24px;
    }

    /* Occupancy Bar */
    .occupancy-bar {
      width: 100%;
      height: 6px;
      background: rgba(245, 241, 234, 0.24);
      border-radius: var(--radius-sm);
      overflow: hidden;
    }

    .occupancy-fill {
      height: 100%;
      background: var(--canvas-bone);
      transition: width 0.3s ease;
    }

    /* Minibus 20-Seat Layout */
    .minibus-cabin-container {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 16px;
      background: var(--canvas-bone);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
    }

    .driver-seat-box {
      font-weight: 600;
      padding: 8px;
      background: var(--color-graphite);
      color: var(--canvas-ivory);
      border-radius: var(--radius-sm);
    }

    .cabin-aisle {
      width: 24px;
      min-height: 32px;
    }

    .seat-box {
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-hairline);
      background: var(--surface-card);
      font-family: var(--font-mono);
      font-size: 13px;
    }

    .seat-box.boarded {
      background: var(--color-forest);
      color: var(--canvas-ivory);
    }

    /* Manifest Flyout Drawer */
    .flyout-drawer {
      position: fixed;
      top: 0;
      right: 0;
      width: 480px;
      height: 100vh;
      background: var(--canvas-ivory);
      border-left: 1px solid var(--border-hairline);
      z-index: 2000;
      overflow-y: auto;
      padding: 24px;
    }

    .drawer-sheet-grabber-bar {
      display: none;
      width: 100%;
      padding: 8px 0;
      justify-content: center;
    }

    .sheet-grabber {
      width: 40px;
      height: 4px;
      background: var(--border-taupe);
      border-radius: 2px;
    }

    /* Desktop Sidebar & Mobile Bottom Navigation */
    .sidebar {
      width: 260px;
      background: var(--surface-card);
      border-right: 1px solid var(--border-hairline);
    }

    .mobile-bottom-nav-bar {
      display: none;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(245, 241, 234, 0.96);
      backdrop-filter: blur(12px);
      border-top: 1px solid var(--border-hairline);
      padding-bottom: env(safe-area-inset-bottom, 14px);
      z-index: 1000;
    }

    .screen-content-area {
      padding: 24px 24px calc(80px + env(safe-area-inset-bottom, 14px));
    }

    /* Mobile Responsive Transformations (< 768px) */
    @media (max-width: 768px) {
      .sidebar {
        display: none !important;
      }

      .mobile-bottom-nav-bar {
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: calc(60px + env(safe-area-inset-bottom, 14px));
      }

      .table-container {
        display: none !important;
      }

      .mobile-cards-feed {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .flyout-drawer {
        width: 100vw;
        max-width: 100vw;
        border-left: none;
        top: auto;
        bottom: 0;
        height: 92dvh;
        border-radius: 16px 16px 0 0;
      }

      .drawer-sheet-grabber-bar {
        display: flex;
      }
    }
  </style>
</head>
<body>
  <!-- Artisanal SVG Paper Grain Overlay -->
  <div class="paper-grain-overlay"></div>

  <!-- Kinetic Desktop Cursor Follower -->
  <div class="custom-cursor-follower" id="cursorFollower"></div>

  <!-- Sidebar (Desktop) -->
  <aside class="sidebar">
    <div class="brand-wordmark">BUSLINER</div>
    <nav class="nav-links">
      <a href="#dashboard" class="nav-link active">Обзор</a>
      <a href="#trips" class="nav-link">Рейсы</a>
      <a href="#schedule" class="nav-link">Расписание</a>
      <a href="#bookings" class="nav-link">Пассажиры</a>
      <a href="#finances" class="nav-link">Финансы</a>
      <a href="#settings" class="nav-link">Автопарк</a>
    </nav>
  </aside>

  <!-- Mobile Bottom Navigation Bar -->
  <nav class="mobile-bottom-nav-bar">
    <button class="nav-tab-btn" onclick="switchScreen('dashboard')">Обзор</button>
    <button class="nav-tab-btn" onclick="switchScreen('trips')">Рейсы</button>
    <button class="nav-tab-btn" onclick="switchScreen('schedule')">График</button>
    <button class="nav-tab-btn" onclick="switchScreen('bookings')">Пассажиры</button>
    <button class="nav-tab-btn" onclick="switchScreen('finances')">Финансы</button>
    <button class="nav-tab-btn" onclick="switchScreen('settings')">Парк</button>
  </nav>

  <!-- Main Content Area -->
  <main class="screen-content-area">
    <!-- Desktop Table Container -->
    <div class="table-container">
      <table class="desktop-table">
        <thead>
          <tr><th>Рейс</th><th>Отправление</th><th>Занятость</th></tr>
        </thead>
        <tbody>
          <tr><td>Минск — Вильнюс</td><td>18:45</td><td>18 / 20</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Driver Active Trip Top Banner -->
    <section id="driverHeroBanner">
      <div class="banner-top-row">
        <span class="hero-deck-badge">Активный рейс • Посадка открыта</span>
        <span class="departure-countdown mono" id="heroCountdown">До отправления: 18 мин</span>
      </div>
      <h1 class="hero-deck-title">Минск ➔ <em>Вильнюс</em> • 18:45</h1>
      <div class="vehicle-info-line">
        <span class="mono">Mercedes Sprinter 7TAX-8891</span>
        <span class="seat-badge mono">18 / 20 мест</span>
      </div>
      <div class="occupancy-bar">
        <div class="occupancy-fill" style="width: 90%;"></div>
      </div>
      <div class="hero-actions-row">
        <button class="btn-driver-hero primary" onclick="openTripDetails('BL-5715')">
          Открыть посадку пассажиров (Чек-ин)
        </button>
        <button class="btn-driver-hero secondary" onclick="broadcastTripDelay('BL-5715', 15)">
          Задержка +15 мин
        </button>
      </div>
    </section>

    <!-- Mobile Feeds for Tables -->
    <div class="mobile-cards-feed" id="dashboardUpcomingMobileCards">
      <div class="card feed-card">
        <div>Рейс Минск — Вильнюс • 18:45</div>
      </div>
    </div>

    <div class="mobile-cards-feed" id="bookingsMobileFeed">
      <div class="card feed-card">
        <div class="roster-name">Александр Волков</div>
        <a href="tel:+375291112233" class="btn-call-passenger" title="Позвонить Александру">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
        </a>
      </div>
    </div>

    <!-- Financial Requisites Block (Carrier Office) -->
    <section class="card finances-card" id="screen-finances">
      <h2 class="section-heading">Финансы и <em>выплаты</em></h2>
      <div class="kpi-grid">
        <div class="kpi-item">
          <span class="kpi-label">Валовая выручка</span>
          <span class="kpi-value mono" id="kpiGrossRevenue">12 480 BYN</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">Комиссия сервиса (5%)</span>
          <span class="kpi-value mono" id="kpiPlatformFee">- 624 BYN</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">К выплате на IBAN</span>
          <span class="kpi-value mono" id="kpiNetPayout">11 856 BYN</span>
        </div>
      </div>
      <div class="iban-requisites-box">
        <span class="mono-label">Расчетный счет перевозчика:</span>
        <span class="iban-text mono" id="carrierIban">BY22ALFA30130000001234567890</span>
        <span class="bank-bic mono">БИК: ALFABY2X</span>
        <button class="link-subtle-cta btn-magnetic" onclick="copyIbanToClipboard()">
          Копировать IBAN
        </button>
      </div>
      <!-- Mobile Route Profitability Cards Feed -->
      <div class="mobile-cards-feed" id="financesMobileFeed">
        <div class="card feed-card">
          <div class="route-header">Минск ➔ Вильнюс</div>
          <div class="mono">Доход: 8 400 BYN (Комиссия 5%: 420 BYN)</div>
        </div>
      </div>
    </section>

    <!-- Fleet Settings Section (with Mobile Cards) -->
    <section class="card" id="screen-settings">
      <h2 class="section-heading">Автопарк <em>перевозчика</em></h2>
      <div class="mobile-cards-feed" id="fleetMobileFeed">
        <div class="card feed-card">
          <div class="vehicle-name">Mercedes-Benz Sprinter 519</div>
          <div class="mono">20 мест • Госномер 7TAX-8891 • Статус: На линии</div>
        </div>
      </div>
    </section>

    <!-- Form Inputs with Virtual Keyboard Modes -->
    <div class="modal-form" style="display:none;">
      <input type="text" id="tripPriceInput" inputmode="decimal" value="70">
      <input type="text" id="bookingSeatNumber" inputmode="numeric" value="04">
      <input type="tel" id="bookingPhone" value="+375291112233">
    </div>

    <!-- Manifest Bottom Sheet / Flyout Drawer -->
    <div class="flyout-drawer" id="tripDetailsDrawer" style="display: none;">
      <div class="drawer-sheet-grabber-bar">
        <div class="sheet-grabber"></div>
      </div>
      <div class="drawer-header">
        <h3 class="section-heading">Посадочная <em>ведомость</em></h3>
        <button class="drawer-close-btn" onclick="closeTripDetails()" aria-label="Закрыть">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <!-- 20-Seat Minibus Cabin -->
      <div class="minibus-cabin-container" id="drawerSeatsGrid">
        <div class="driver-seat-box">Водитель</div>
        <div class="cabin-aisle"></div>
      </div>

      <!-- Passenger Roster List -->
      <div class="roster-list" id="drawerRosterList"></div>
    </div>
  </main>

  <script>
    // System Data Stores
    const DEFAULT_TRIPS = [
      { id: "BL-5715", route: "Минск — Вильнюс", departure: "18:45", vehicle: "Mercedes Sprinter", occupied: 18, capacity: 20, fare: 70, status: "boarding" },
      { id: "BL-5716", route: "Минск — Гродно", departure: "20:00", vehicle: "VW Crafter", occupied: 19, capacity: 20, fare: 35, status: "scheduled" }
    ];

    const DEFAULT_BOOKINGS = [
      { id: "TKT-8801", tripId: "BL-5715", seat: "01", name: "Александр Волков", phone: "+375 (29) 111-22-33", status: "boarded", payment: "paid", amount: 70 },
      { id: "TKT-8802", tripId: "BL-5715", seat: "02", name: "Екатерина Смирнова", phone: "+375 (29) 222-33-44", status: "confirmed", payment: "paid", amount: 70 },
      { id: "TKT-8804", tripId: "BL-5715", seat: "04", name: "Ольга Малиновская", phone: "+375 (29) 444-55-66", status: "confirmed", payment: "cash", amount: 70 }
    ];

    let trips = [...DEFAULT_TRIPS];
    let bookings = [...DEFAULT_BOOKINGS];
    let userRole = 'carrier';

    // Reactive Financial Engine
    function calculateFinancials(tripsList = trips) {
      const totalGross = tripsList.reduce((sum, t) => sum + (t.occupied * t.fare), 0);
      const platformFee = Math.round(totalGross * 0.05);
      const netPayout = totalGross - platformFee;
      const totalPassengers = tripsList.reduce((sum, t) => sum + t.occupied, 0);
      const avgTicket = totalPassengers > 0 ? Number((totalGross / totalPassengers).toFixed(1)) : 0;
      return { totalGross, platformFee, netPayout, avgTicket, totalPassengers };
    }

    // Delay Broadcast (Autonomous - Zero Dispatcher)
    function broadcastTripDelay(tripId, minutes) {
      const trip = trips.find(t => t.id === tripId);
      if (trip) {
        trip.delay = minutes;
        showToast(
          `Рейс ${tripId}: задержка ${minutes} мин`,
          'alert',
          `Пассажиры рейса и радар перевозчика оповещены о задержке на ${minutes} минут`
        );
        if (navigator.vibrate) navigator.vibrate([40, 60, 40]);
      }
    }

    // Passenger Boarding Check-in Toggle
    function toggleCheckin(bookingId) {
      const b = bookings.find(item => item.id === bookingId);
      if (b) {
        b.status = b.status === 'boarded' ? 'confirmed' : 'boarded';
        if (navigator.vibrate) navigator.vibrate([35]);
        renderManifestRoster();
        renderMinibusSeats();
        return b.status;
      }
      return null;
    }

    // Phone Sanitizer
    function sanitizePhoneNumber(phone) {
      return phone.replace(/[^\\d+]/g, '');
    }

    // Render Manifest Roster with tel: dialer and payment status
    function renderManifestRoster() {
      const rosterContainer = document.getElementById('drawerRosterList');
      if (!rosterContainer) return;
      rosterContainer.innerHTML = bookings.map(b => {
        const cleanPhone = sanitizePhoneNumber(b.phone);
        const isBoarded = b.status === 'boarded';
        const isPaid = b.payment === 'paid';
        const payBadge = isPaid
          ? '<span class="badge paid">Оплачено онлайн</span>'
          : `<span class="badge cash">Оплата водителю: ${b.amount} BYN</span>`;

        return `
          <div class="roster-item ${isBoarded ? 'boarded' : ''}" id="roster-${b.id}">
            <div class="roster-info">
              <span class="roster-name">${b.name}</span>
              <span class="roster-seat mono">Место ${b.seat}</span>
              ${payBadge}
            </div>
            <div class="roster-actions">
              <a href="tel:${cleanPhone}" class="btn-call-passenger" title="Позвонить ${b.name}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                </svg>
              </a>
              <button class="btn-checkin-toggle ${isBoarded ? 'boarded' : ''}" onclick="toggleCheckin('${b.id}')">
                ${isBoarded ? '✓ В салоне' : 'Посадить'}
              </button>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render 20-Seat Minibus Cabin
    function renderMinibusSeats() {
      const cabinContainer = document.getElementById('drawerSeatsGrid');
      if (!cabinContainer) return;
      let html = '<div class="driver-seat-box">Водитель</div><div class="cabin-aisle"></div>';
      for (let i = 1; i <= 20; i++) {
        const seatStr = i < 10 ? `0${i}` : `${i}`;
        const b = bookings.find(item => item.seat === seatStr);
        const isBoarded = b && b.status === 'boarded';
        html += `<div class="seat-box ${isBoarded ? 'boarded' : ''}" data-seat="${seatStr}">${seatStr}</div>`;
      }
      cabinContainer.innerHTML = html;
    }

    function openTripDetails(tripId) {
      const drawer = document.getElementById('tripDetailsDrawer');
      if (drawer) {
        drawer.style.display = 'block';
        renderManifestRoster();
        renderMinibusSeats();
      }
    }

    function closeTripDetails() {
      const drawer = document.getElementById('tripDetailsDrawer');
      if (drawer) drawer.style.display = 'none';
    }

    function switchScreen(screenId) {
      window.location.hash = '#' + screenId;
    }

    function setUserRole(role) {
      userRole = role;
      const banner = document.getElementById('driverHeroBanner');
      if (banner) banner.style.display = 'flex';
    }

    function copyIbanToClipboard() {
      showToast('IBAN скопирован в буфер обмена', 'success');
    }

    function showToast(title, type = 'info', description = '') {
      return { title, type, description };
    }

    // Kinetic Cursor Lerp on Desktop
    let mouseX = -100, mouseY = -100, cursorX = -100, cursorY = -100;
    if (typeof window !== 'undefined') {
      window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
      });
      function renderCursor() {
        cursorX += (mouseX - cursorX) * 0.22;
        cursorY += (mouseY - cursorY) * 0.22;
        const cursorEl = document.getElementById('cursorFollower');
        if (cursorEl) {
          cursorEl.style.transform = `translate(${cursorX}px, ${cursorY}px) translate(-50%, -50%)`;
        }
      }
    }
  </script>
</body>
</html>
"""
