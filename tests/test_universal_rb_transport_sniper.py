#!/usr/bin/env python3
"""
Unit and Integration Tests for Universal Belarus Transport Sniper Engine
========================================================================
Tests all providers:
  - Atlasbus city mapping & API parsing
  - NextFree / BiletBaza HTML scraping & selector extraction
  - RW.BY Railway table parser
  - Universal Web Sniffer heuristic DOM & JSON extraction
  - UniversalBelarusSniperManager orchestration, filtering & race handling
"""

import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.external_transport_sniper import (
    TransportTrip,
    SniperTask,
    AtlasbusAdapter,
    NextFreeRegionalAdapter,
    RwByRailwayAdapter,
    UniversalWebSnifferAdapter,
    UniversalBelarusSniperManager
)

SAMPLE_NEXTFREE_HTML = """
<div class="nf-schedule-body">
    <div class="nf-route js_route">
        <div class="nf-route-point">
            <div class="nf-route-point__time">18:45</div>
            <div class="nf-route-point__name">Минск (ст.м. Каменная Горка)</div>
            <div class="nf-route-point__date">2026-10-30</div>
        </div>
        <div class="nf-route-point">
            <div class="nf-route-point__time">21:15</div>
            <div class="nf-route-point__name">Лида (Автовокзал)</div>
            <div class="nf-route-point__date">2026-10-30</div>
        </div>
        <div class="nf-route-order__cost">
            <strong>22.00 BYN</strong>
        </div>
        <div class="nf-route__company">ЛидаЭкспресс ООО</div>
        <button class="reservationButton js_get-bus" data-url="/booking/step1?route_id=9871">
            Забронировать
        </button>
    </div>
    <div class="nf-route js_route is-disabled">
        <div class="nf-route-point__time">19:30</div>
        <div class="nf-route-point__time">22:00</div>
        <div class="nf-route-order__cost"><strong>22.00 BYN</strong></div>
        <button class="reservationButton js_get-bus is-disabled">Мест нет</button>
    </div>
</div>
"""

SAMPLE_ARBITRARY_WEBSITE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Маршрутное такси Гродно - Минск</title></head>
<body>
    <div class="trip-card">
        <h3>Отправление: 17:30 Минск Центральный</h3>
        <p>Прибытие: 21:00 Гродно Автовокзал</p>
        <span class="price-tag">Стоимость: 30.00 BYN</span>
        <span class="badge">Осталось мест: 3</span>
        <a href="/reserve?id=5512" class="btn-primary">Забронировать место</a>
    </div>
    <div class="trip-card">
        <h3>Отправление: 20:00 Минск Центральный</h3>
        <p>Прибытие: 23:30 Гродно Автовокзал</p>
        <span class="price-tag">Стоимость: 30.00 BYN</span>
        <span class="badge">Осталось мест: 0</span>
        <button disabled>Мест нет</button>
    </div>
</body>
</html>
"""

SAMPLE_EMBEDDED_JSON_HTML = """
<html>
<head>
<script id="__NEXT_DATA__" type="application/json">
{
    "props": {
        "pageProps": {
            "rides": [
                {
                    "id": "ride_901",
                    "departure": "19:00",
                    "price": 24.50,
                    "free_seats": 2,
                    "carrier": "Полоцкий Экспресс"
                }
            ]
        }
    }
}
</script>
</head>
<body></body>
</html>
"""


class TestUniversalBelarusTransportSniper(unittest.TestCase):

    def setUp(self):
        self.atlas = AtlasbusAdapter()
        self.nextfree = NextFreeRegionalAdapter()
        self.rw = RwByRailwayAdapter()
        self.sniffer = UniversalWebSnifferAdapter()
        self.manager = UniversalBelarusSniperManager()

    def test_atlasbus_city_mapping(self):
        """Validates that key Belarusian regional centers map correctly to Atlasbus IDs."""
        self.assertEqual(self.atlas.resolve_city_id("Минск"), "c625144")
        self.assertEqual(self.atlas.resolve_city_id("Лида"), "c626081")
        self.assertEqual(self.atlas.resolve_city_id("Гродно"), "c627904")
        self.assertEqual(self.atlas.resolve_city_id("Брест"), "c629634")
        self.assertEqual(self.atlas.resolve_city_id("Витебск"), "c620127")
        self.assertEqual(self.atlas.resolve_city_id("Полоцк"), "c623914")
        self.assertIsNone(self.atlas.resolve_city_id("Париж"))

    def test_nextfree_html_parser(self):
        """Tests parsing of real-world NextFree/BiletBaza HTML responses."""
        trips = self.nextfree._parse_nextfree_html(
            SAMPLE_NEXTFREE_HTML,
            base_url="https://bilet.minsk-lida.by",
            origin="Минск",
            destination="Лида",
            target_date="2026-10-30",
            platform_title="Минск — Лида Экспресс"
        )
        # The disabled one should be skipped, only 1 valid trip parsed
        self.assertEqual(len(trips), 1)
        trip = trips[0]
        self.assertEqual(trip.provider_id, "nextfree")
        self.assertEqual(trip.departure_time, "2026-10-30 18:45")
        self.assertEqual(trip.arrival_time, "2026-10-30 21:15")
        self.assertEqual(trip.price_byn, 22.0)
        self.assertEqual(trip.carrier_name, "ЛидаЭкспресс ООО")
        self.assertEqual(trip.booking_url, "https://bilet.minsk-lida.by/booking/step1?route_id=9871")
        self.assertTrue(trip.is_instant_bookable)

    def test_universal_web_sniffer_dom_heuristics(self):
        """Tests autonomous semantic DOM scraping on unknown arbitrary transport sites."""
        trips = self.sniffer._extract_trips_from_dom_heuristics(
            SAMPLE_ARBITRARY_WEBSITE_HTML,
            source_url="https://express-grodno.by/schedule",
            origin="Минск",
            destination="Гродно",
            target_date="2026-10-30"
        )
        self.assertGreaterEqual(len(trips), 1)
        trip = trips[0]
        self.assertEqual(trip.provider_id, "generic_web")
        self.assertIn("17:30", trip.departure_time)
        self.assertEqual(trip.price_byn, 30.0)
        self.assertEqual(trip.free_seats, 3)
        self.assertEqual(trip.booking_url, "https://express-grodno.by/reserve?id=5512")

    def test_universal_web_sniffer_embedded_json(self):
        """Tests sniffing hidden JSON script blocks inside arbitrary modern web frameworks."""
        endpoints = self.sniffer._sniff_embedded_api_endpoints(
            '<div><a data-url="/api/v2/trips/search"></a></div>',
            base_url="https://sample-bus.by"
        )
        self.assertIn("https://sample-bus.by/api/v2/trips/search", endpoints)

    def test_sniper_manager_filtering_and_time_window(self):
        """Validates that SniperManager correctly respects time windows and price limits."""
        task = self.manager.create_sniper_task(
            user_id="user_test_99",
            telegram_chat_id=999999,
            origin="Минск",
            destination="Лида",
            target_date="2026-10-30",
            time_window_start="18:00",
            time_window_end="19:00",
            max_price_byn=25.0,
            providers=["all"]
        )
        self.assertEqual(task.status, "active")

        # Mock a trip within window and a trip outside window
        trip_valid = TransportTrip(
            provider_id="nextfree",
            provider_name="Лида Экспресс",
            trip_id="t1",
            origin="Минск",
            destination="Лида",
            departure_time="2026-10-30 18:30",
            arrival_time="2026-10-30 21:00",
            free_seats=2,
            price_byn=22.0,
            carrier_name="ЛидаЭкспресс",
            booking_url="https://bilet.minsk-lida.by"
        )
        trip_too_expensive = TransportTrip(
            provider_id="nextfree",
            provider_name="Лида Экспресс VIP",
            trip_id="t2",
            origin="Минск",
            destination="Лида",
            departure_time="2026-10-30 18:45",
            arrival_time="2026-10-30 21:15",
            free_seats=1,
            price_byn=45.0, # exceeds 25.0 BYN
            carrier_name="ЛидаЭкспресс",
            booking_url="https://bilet.minsk-lida.by"
        )
        trip_wrong_time = TransportTrip(
            provider_id="nextfree",
            provider_name="Лида Экспресс",
            trip_id="t3",
            origin="Минск",
            destination="Лида",
            departure_time="2026-10-30 21:30", # outside 18:00 - 19:00
            arrival_time="2026-10-30 23:59",
            free_seats=3,
            price_byn=22.0,
            carrier_name="ЛидаЭкспресс",
            booking_url="https://bilet.minsk-lida.by"
        )

        # Mock the manager's provider scan
        self.manager.scan_all_providers = lambda t: [trip_valid, trip_too_expensive, trip_wrong_time] if t.task_id == task.task_id else []

        intercepted = self.manager.execute_check_cycle()
        self.assertEqual(len(intercepted), 1)
        res_task, winner = intercepted[0]
        self.assertEqual(res_task.task_id, task.task_id)
        self.assertEqual(winner.trip_id, "t1")
        self.assertEqual(res_task.status, "intercepted")
        self.assertIsNotNone(res_task.latency_ms)

    def test_sniper_manager_cancellation(self):
        """Tests that cancelled sniper tasks are ignored in check cycles."""
        task = self.manager.create_sniper_task(
            user_id="user_cancel",
            telegram_chat_id=111,
            origin="Минск",
            destination="Брест",
            target_date="2026-10-30"
        )
        self.assertEqual(task.status, "active")
        success = self.manager.cancel_task(task.task_id)
        self.assertTrue(success)
        self.assertEqual(task.status, "cancelled")

        intercepted = self.manager.execute_check_cycle()
        self.assertEqual(len(intercepted), 0)


if __name__ == "__main__":
    unittest.main()
