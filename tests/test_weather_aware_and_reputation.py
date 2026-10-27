#!/usr/bin/env python3
"""
Unit and Integration Tests for Weather-Aware Travel (F14) and Two-Sided Reputation (F13)
========================================================================================
Validates:
  1. Weather corridor checkpoint extraction & friction calculation.
  2. Severe weather delay probability and 1-tap free rebooking advisory.
  3. Passenger Trust Score formula (on-time bonuses, no-show penalties).
  4. Reputation-driven Seat Sniper prioritization (Elite passenger beats Verified in race).
"""

import sys
import os
import unittest
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.weather_aware_travel import weather_engine, RouteWeatherAssessment
from server.passenger_reputation_engine import passenger_reputation_engine, PassengerTrustProfile
from server.sniper_engine import SeatSniperEngine, SniperOrder, SeatReleaseEvent


class TestWeatherAwareAndReputation(unittest.TestCase):

    def setUp(self):
        self.weather = weather_engine
        self.reputation = passenger_reputation_engine

    def test_weather_aware_corridor_evaluation_m7(self):
        """Tests highway segment checkpoint analysis along M7 (Minsk - Vilnius)."""
        assessment = self.weather.assess_route_weather("Минск — Вильнюс", "18:45", simulated_scenario="clear")
        self.assertEqual(assessment.route_name, "Минск — Вильнюс")
        self.assertGreaterEqual(len(assessment.checkpoints), 4)
        self.assertEqual(assessment.overall_risk_level, "low")
        self.assertFalse(assessment.free_reschedule_eligible)
        self.assertLessEqual(assessment.delay_probability, 0.20)

    def test_weather_aware_snowstorm_hazard_and_free_reschedule(self):
        """Tests that snowstorm triggers delay risk, friction drop, and free reschedule eligibility."""
        assessment = self.weather.assess_route_weather("Минск — Вильнюс", "18:45", simulated_scenario="snowstorm")
        self.assertIn(assessment.overall_risk_level, ["high", "critical"])
        self.assertGreaterEqual(assessment.delay_probability, 0.50)
        self.assertGreaterEqual(assessment.expected_delay_min, 30)
        self.assertTrue(assessment.free_reschedule_eligible)
        self.assertIsNotNone(assessment.alternative_departure_time)
        self.assertIsNotNone(assessment.critical_segment)

        # Check friction drops
        friction_levels = [cp.road_friction for cp in assessment.checkpoints]
        self.assertTrue(any(f < 0.40 for f in friction_levels))

    def test_passenger_reputation_progression_to_elite(self):
        """Tests that completing trips on time with 5-star reviews promotes user to Elite."""
        uid = f"user_test_{int(time.time() * 1000)}"
        profile = self.reputation.get_or_create_profile(uid, "+375291234567", "Анна Мороз")
        self.assertEqual(profile.trust_score, 75.0)
        self.assertEqual(profile.trust_tier, "verified")
        self.assertEqual(profile.sniper_priority_level, 2)

        # Complete 8 on-time trips with 5-star driver reviews
        for _ in range(8):
            profile = self.reputation.record_trip_completion(uid, was_punctual=True, driver_rating=5.0)

        self.assertGreaterEqual(profile.trust_score, 90.0)
        self.assertEqual(profile.trust_tier, "elite")
        self.assertEqual(profile.sniper_priority_level, 1) # Priority Level 1 in Sniper
        self.assertTrue(profile.late_cancellation_fee_waived)
        self.assertIn("Приоритет снайпера №1", profile.reputation_badges)

    def test_passenger_reputation_no_show_penalty(self):
        """Tests that failing to show up penalizes user by 25 points and drops privileges."""
        uid = f"user_noshow_{int(time.time() * 1000)}"
        profile = self.reputation.get_or_create_profile(uid, "+375299876543", "Виктор Иванов")
        self.assertEqual(profile.trust_score, 75.0)

        # Record No-Show
        penalized = self.reputation.record_no_show(uid, "BL-5715")
        self.assertEqual(penalized.trust_score, 50.0)
        self.assertEqual(penalized.trust_tier, "probation")
        self.assertFalse(penalized.pay_on_board_allowed) # Pre-auth required
        self.assertEqual(penalized.sniper_priority_level, 3)

    def test_sniper_priority_queue_two_sided_reputation_sorting(self):
        """
        Validates that a passenger with higher reputation wins the sniper race
        even if their order was submitted slightly after another order.
        """
        async def run_race():
            engine = SeatSniperEngine()
            await engine.start()

            # Order A: Lower trust (70.0), created earlier at T=100
            order_a = SniperOrder(
                order_id="order_std_trust",
                user_id="user_std",
                client_identity="user_std",
                route_id="route_minsk_vilnius",
                departure_date="2026-10-30",
                time_window_start="18:00",
                time_window_end="19:00",
                preferred_seat_type="any",
                passenger_full_name="Стандартный Пассажир",
                passenger_phone="+375291111111",
                passenger_passport_hash="hash_a",
                auto_debit_consent=True,
                max_price_byn=100.0,
                passenger_trust_score=70.0,
                queue_priority=100.0
            )

            # Order B: Elite trust (98.0), created later at T=200
            order_b = SniperOrder(
                order_id="order_elite_trust",
                user_id="user_elite",
                client_identity="user_elite",
                route_id="route_minsk_vilnius",
                departure_date="2026-10-30",
                time_window_start="18:00",
                time_window_end="19:00",
                preferred_seat_type="any",
                passenger_full_name="Элитный Пассажир",
                passenger_phone="+375292222222",
                passenger_passport_hash="hash_b",
                auto_debit_consent=True,
                max_price_byn=100.0,
                passenger_trust_score=98.0,
                queue_priority=200.0
            )

            await engine.create_order(order_a)
            await engine.create_order(order_b)

            # Seat release event
            event = SeatReleaseEvent(
                event_id="ev_rep_race_01",
                trip_id="BL-5715",
                route_id="route_minsk_vilnius",
                seat_id="07A",
                seat_number=7,
                seat_type="window",
                fare_byn=95.0,
                release_reason="passenger_refund",
                idempotency_key="idemp_rep_race_01",
                release_timestamp=time.time(),
                departure_time="18:45"
            )

            results = await engine.publish_seat_release(event)
            await engine.stop()
            return results

        results = asyncio.run(run_race())
        self.assertEqual(len(results), 2)
        winner = [r for r in results if r.success][0]
        # Order B with trust_score 98.0 MUST WIN the race over order A with trust_score 70.0!
        self.assertEqual(winner.order_id, "order_elite_trust")
        self.assertEqual(winner.status, "reserved")


if __name__ == "__main__":
    unittest.main()
