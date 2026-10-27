#!/usr/bin/env python3
"""
BusLiner Production Seat Sniper & Offline Check-in Test Suite
=======================================================================================
Verifies core architectural guarantees:
1. Race condition concurrency: Exactly 1 sniper captures seat; second gets graceful fallback.
2. Idempotency: Event replays never duplicate holds or debit miles twice.
3. Hold TTL expiration: Expired holds are reaped and re-emitted.
4. Anti-abuse ceilings: Maximum 3 active snipers per user identity.
5. Offline QR verification: Constant-time HMAC-SHA256 verification and tamper detection.
6. Telegram notification idempotency: Duplicate user/trip/event notifications suppressed.
"""

import sys
import os
import time
import asyncio
import unittest

# Ensure parent directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.sniper_engine import SeatSniperEngine, SniperOrder, SeatReleaseEvent
from server.offline_checkin import QRCodeSigner, ManifestManager
from server.telegram_webhook_gateway import NotificationOutbox


class TestSeatSniperProduction(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.engine = SeatSniperEngine()
        await self.engine.start()

    async def asyncTearDown(self):
        await self.engine.stop()

    async def test_sniper_concurrent_race_condition(self):
        """
        GIVEN two concurrent snipers with different queue priorities for the same route
        WHEN a seat release event occurs
        THEN exactly ONE sniper reserves the seat (status='reserved')
        AND the other sniper is marked 'failed_beaten' with graceful fallback alternatives.
        """
        # Sniper 1: Arrived first at t=100
        order1 = SniperOrder(
            order_id="order-alpha-001",
            user_id="user-111",
            client_identity="+375291112233",
            route_id="route-minsk-vilnius",
            departure_date="2026-05-25",
            time_window_start="17:00",
            time_window_end="19:00",
            preferred_seat_type="any",
            passenger_full_name="Ковалев А. В.",
            passenger_phone="+375291112233",
            passenger_passport_hash="hash_pass_001",
            auto_debit_consent=True,
            max_price_byn=100.0,
            queue_priority=100.0
        )

        # Sniper 2: Arrived second at t=200
        order2 = SniperOrder(
            order_id="order-beta-002",
            user_id="user-222",
            client_identity="+375292223344",
            route_id="route-minsk-vilnius",
            departure_date="2026-05-25",
            time_window_start="17:00",
            time_window_end="19:00",
            preferred_seat_type="any",
            passenger_full_name="Иванов И. И.",
            passenger_phone="+375292223344",
            passenger_passport_hash="hash_pass_002",
            auto_debit_consent=True,
            max_price_byn=100.0,
            queue_priority=200.0
        )

        ok1, _ = await self.engine.create_order(order1)
        ok2, _ = await self.engine.create_order(order2)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        # Single seat release event
        event = SeatReleaseEvent(
            event_id="evt-refund-001",
            trip_id="BL-5715",
            seat_id="seat-07A",
            seat_number=7,
            seat_type="window",
            fare_byn=95.0,
            release_reason="passenger_refund",
            idempotency_key="refund_bl5715_07a_unique_1",
            release_timestamp=time.time(),
            route_id="route-minsk-vilnius"
        )

        # Fire concurrent execution
        results = await self.engine.publish_seat_release(event)

        # Validate that exactly 2 evaluations took place
        self.assertEqual(len(results), 2)

        # Winner must be order1 (earlier in queue)
        winner = [r for r in results if r.success][0]
        loser = [r for r in results if not r.success][0]

        self.assertEqual(winner.order_id, "order-alpha-001")
        self.assertEqual(winner.status, "reserved")
        self.assertEqual(winner.seat_number, 7)
        self.assertGreater(winner.latency_ms, 0.0)

        # Loser must have fallback alternatives
        self.assertEqual(loser.order_id, "order-beta-002")
        self.assertEqual(loser.status, "failed_beaten")
        self.assertIn("перехвачено", loser.error)
        self.assertGreater(len(loser.alternative_trips), 0)

        # Verify latency telemetry recorded
        metrics = await self.engine.latency_tracker.get_percentiles()
        self.assertEqual(metrics["count"], 1)
        self.assertGreater(metrics["latest"], 0.0)

    async def test_sniper_event_replay_idempotence(self):
        """
        GIVEN a processed seat release event
        WHEN the same event is replayed with the same idempotency_key
        THEN the second attempt is safely ignored with zero double-reservations.
        """
        order = SniperOrder(
            order_id="order-gamma-003",
            user_id="user-333",
            client_identity="+375293334455",
            route_id="route-minsk-grodno",
            departure_date="2026-05-25",
            time_window_start="08:00",
            time_window_end="10:00",
            preferred_seat_type="any",
            passenger_full_name="Смирнов А. С.",
            passenger_phone="+375293334455",
            passenger_passport_hash="hash_pass_003",
            auto_debit_consent=True,
            max_price_byn=50.0
        )
        await self.engine.create_order(order)

        event = SeatReleaseEvent(
            event_id="evt-refund-002",
            trip_id="BL-8802",
            seat_id="seat-03A",
            seat_number=3,
            seat_type="window",
            fare_byn=35.0,
            release_reason="passenger_refund",
            idempotency_key="idemp_key_exact_repeat_001",
            route_id="route-minsk-grodno"
        )

        # First run: successfully reserved
        res1 = await self.engine.publish_seat_release(event)
        self.assertEqual(len(res1), 1)
        self.assertTrue(res1[0].success)

        # Second run: duplicate replay must return empty list (idempotent skip)
        res2 = await self.engine.publish_seat_release(event)
        self.assertEqual(len(res2), 0)

    async def test_sniper_reservation_cancellation(self):
        """
        GIVEN an active sniper order
        WHEN user cancels the order
        THEN order is not matched on subsequent events and anti-abuse quota is freed.
        """
        order = SniperOrder(
            order_id="order-delta-004",
            user_id="user-444",
            client_identity="+375294445566",
            route_id="route-minsk-brest",
            departure_date="2026-05-25",
            time_window_start="14:00",
            time_window_end="16:00",
            preferred_seat_type="any",
            passenger_full_name="Попов П. П.",
            passenger_phone="+375294445566",
            passenger_passport_hash="hash_pass_004",
            auto_debit_consent=True,
            max_price_byn=50.0
        )
        await self.engine.create_order(order)

        # Cancel
        cancelled = await self.engine.cancel_order(order.order_id)
        self.assertTrue(cancelled)

        event = SeatReleaseEvent(
            event_id="evt-cancel-test",
            trip_id="BL-1415",
            seat_id="seat-02A",
            seat_number=2,
            seat_type="aisle",
            fare_byn=38.0,
            release_reason="passenger_refund",
            idempotency_key="idemp_cancel_test_001",
            route_id="route-minsk-brest"
        )
        results = await self.engine.publish_seat_release(event)
        self.assertEqual(len(results), 0)

    async def test_sniper_anti_abuse_limits(self):
        """
        GIVEN a user identity with 3 active snipers
        WHEN attempting to create a 4th sniper order
        THEN creation is rejected with an anti-abuse message.
        """
        identity = "+375295556677"
        for i in range(3):
            o = SniperOrder(
                order_id=f"order-cap-{i}",
                user_id="user-555",
                client_identity=identity,
                route_id="route-minsk-vilnius",
                departure_date="2026-05-25",
                time_window_start="10:00",
                time_window_end="12:00",
                preferred_seat_type="any",
                passenger_full_name="Тестов Т. Т.",
                passenger_phone=identity,
                passenger_passport_hash="hash_pass_cap",
                auto_debit_consent=True,
                max_price_byn=100.0
            )
            ok, _ = await self.engine.create_order(o)
            self.assertTrue(ok)

        # 4th order must be denied
        o4 = SniperOrder(
            order_id="order-cap-overflow",
            user_id="user-555",
            client_identity=identity,
            route_id="route-minsk-vilnius",
            departure_date="2026-05-25",
            time_window_start="10:00",
            time_window_end="12:00",
            preferred_seat_type="any",
            passenger_full_name="Тестов Т. Т.",
            passenger_phone=identity,
            passenger_passport_hash="hash_pass_cap",
            auto_debit_consent=True,
            max_price_byn=100.0
        )
        ok4, msg = await self.engine.create_order(o4)
        self.assertFalse(ok4)
        self.assertIn("Превышен лимит", msg)

    async def test_sniper_hold_ttl_expiry(self):
        """
        GIVEN a seat held by a sniper order
        WHEN hold TTL expires (simulated by setting held_until into the past)
        THEN the seat is freed and re-emitted for subsequent eligible snipers.
        """
        seat_key = "BL-5715:seat-11A"
        self.engine.held_seats[seat_key] = {
            "order_id": "order-ttl-001",
            "held_until": time.time() - 10,  # Expired 10s ago
            "event_id": "evt-ttl-initial",
            "seat_number": 11
        }

        # Sniper waiting for re-released seat
        waiting_sniper = SniperOrder(
            order_id="order-ttl-waiter",
            user_id="user-waiter",
            client_identity="+375298889900",
            route_id="route-minsk-vilnius",
            departure_date="2026-05-25",
            time_window_start="17:00",
            time_window_end="19:00",
            preferred_seat_type="any",
            passenger_full_name="Ждущий Ж. Ж.",
            passenger_phone="+375298889900",
            passenger_passport_hash="hash_waiter",
            auto_debit_consent=True,
            max_price_byn=100.0
        )
        await self.engine.create_order(waiting_sniper)

        # Trigger one iteration of the reaper
        now = time.time()
        for s_key, hold_info in list(self.engine.held_seats.items()):
            if now >= hold_info["held_until"]:
                del self.engine.held_seats[s_key]
                trip_id, seat_id = s_key.split(":")
                re_release = SeatReleaseEvent(
                    event_id="evt-reaper-trigger",
                    trip_id=trip_id,
                    seat_id=seat_id,
                    seat_number=hold_info["seat_number"],
                    seat_type="any",
                    fare_byn=95.0,
                    release_reason="hold_ttl_expiry",
                    idempotency_key="idemp_reaper_test_001",
                    route_id="route-minsk-vilnius"
                )
                results = await self.engine.publish_seat_release(re_release)
                self.assertEqual(len(results), 1)
                self.assertTrue(results[0].success)
                self.assertEqual(results[0].order_id, "order-ttl-waiter")

    def test_offline_qr_crypto_verification(self):
        """
        GIVEN a ticket signed with HMAC-SHA256
        WHEN checked in offline by driver terminal
        THEN valid ticket is accepted and tampered ticket is rejected.
        """
        signer = QRCodeSigner(secret_key="my_ultra_secret_test_key_for_qr_verification_2026")
        payload = signer.generate_signed_qr_payload(
            ticket_id="BL-2026-99",
            trip_id="BL-5715",
            seat_no=7,
            passenger_name="Ковалев Д. М."
        )

        # 1. Valid payload passes verification
        is_valid, msg, data = signer.verify_qr_payload(payload)
        self.assertTrue(is_valid)
        self.assertEqual(data["t"], "BL-2026-99")
        self.assertEqual(data["seat"], 7)

        # 2. Tampered seat number fails verification
        tampered = payload.replace('"seat":7', '"seat":1')
        is_valid_t, msg_t, _ = signer.verify_qr_payload(tampered)
        self.assertFalse(is_valid_t)
        self.assertIn("Поддельная", msg_t)

    async def test_telegram_outbox_idempotence(self):
        """
        GIVEN a notification outbox
        WHEN dispatching the exact same (user_id, trip_id, event_type) twice
        THEN the second attempt is suppressed.
        """
        outbox = NotificationOutbox()
        ok1, id1 = await outbox.enqueue_notification(
            user_id="tg_123456",
            trip_id="BL-5715",
            event_type="seat_intercepted",
            payload={"seat": "07A"}
        )
        self.assertTrue(ok1)

        ok2, status = await outbox.enqueue_notification(
            user_id="tg_123456",
            trip_id="BL-5715",
            event_type="seat_intercepted",
            payload={"seat": "07A"}
        )
        self.assertFalse(ok2)
        self.assertEqual(status, "already_pending")

    async def test_sniper_preauth_hold_capture_and_void(self):
        """
        GIVEN a sniper order with card pre-authorization
        WHEN order is created -> funds are held (status='held')
        WHEN order wins seat -> funds are captured (status='captured')
        WHEN another order is cancelled -> funds are voided without fee (status='voided').
        """
        # Order 1: Will win and capture
        o1 = SniperOrder(
            order_id="order-preauth-win",
            user_id="user-win",
            client_identity="+375291234567",
            route_id="route-minsk-vilnius",
            departure_date="2026-05-25",
            time_window_start="17:00",
            time_window_end="19:00",
            preferred_seat_type="any",
            passenger_full_name="Победитель П. П.",
            passenger_phone="+375291234567",
            passenger_passport_hash="hash_win",
            auto_debit_consent=True,
            max_price_byn=95.0,
            card_token="tok_visa_belarusbank_8812"
        )
        ok1, _ = await self.engine.create_order(o1)
        self.assertTrue(ok1)
        hold_id_win = o1.pre_auth_hold_id
        self.assertIsNotNone(hold_id_win)
        self.assertEqual(self.engine.acquiring.holds[hold_id_win]["status"], "held")

        # Order 2: Will be cancelled and voided
        o2 = SniperOrder(
            order_id="order-preauth-cancel",
            user_id="user-cancel",
            client_identity="+375297654321",
            route_id="route-minsk-vilnius",
            departure_date="2026-05-25",
            time_window_start="17:00",
            time_window_end="19:00",
            preferred_seat_type="any",
            passenger_full_name="Отказник О. О.",
            passenger_phone="+375297654321",
            passenger_passport_hash="hash_cancel",
            auto_debit_consent=True,
            max_price_byn=95.0,
            card_token="tok_mastercard_prior_4401"
        )
        ok2, _ = await self.engine.create_order(o2)
        self.assertTrue(ok2)
        hold_id_cancel = o2.pre_auth_hold_id
        self.assertEqual(self.engine.acquiring.holds[hold_id_cancel]["status"], "held")

        # Cancel Order 2 -> check void
        await self.engine.cancel_order(o2.order_id, reason="passenger_changed_mind")
        self.assertEqual(self.engine.acquiring.holds[hold_id_cancel]["status"], "voided")

        # Release seat -> Order 1 wins -> check capture
        event = SeatReleaseEvent(
            event_id="evt-preauth-test",
            trip_id="BL-5715",
            seat_id="seat-08A",
            seat_number=8,
            seat_type="any",
            fare_byn=95.0,
            release_reason="passenger_refund",
            idempotency_key="idemp_preauth_test_001",
            route_id="route-minsk-vilnius"
        )
        res = await self.engine.publish_seat_release(event)
        self.assertEqual(len(res), 1)
        self.assertTrue(res[0].success)
        self.assertEqual(self.engine.acquiring.holds[hold_id_win]["status"], "captured")
        self.assertEqual(self.engine.acquiring.holds[hold_id_win]["captured_amount"], 95.0)

    def test_ml_noshow_prediction_and_drift(self):
        """
        GIVEN the in-house NoShowPredictorModel
        WHEN evaluating a passenger profile
        THEN model returns calibrated probability, confidence label, and top-3 explainable factors.
        AND when outcomes are logged, drift telemetry reports health metrics.
        """
        from server.ml_noshow_engine import ML_PREDICTOR

        # Profile A: Last-minute online prepaid passenger on Friday evening -> Very low no-show risk (< 5%)
        features_a = {
            "lead_time_hours": 1.5,
            "is_prepaid": True,
            "day_of_week": 5,
            "departure_hour": 18,
            "bad_weather": False,
            "passenger_prior_trips": 4
        }
        res_a = ML_PREDICTOR.predict(features_a)
        self.assertLess(res_a.no_show_probability, 0.08)
        self.assertFalse(res_a.model_fallback_active)
        self.assertGreater(len(res_a.top_factors), 0)
        self.assertIn("100% Онлайн-предоплата", [f.name for f in res_a.top_factors])

        # Profile B: Cash payment booked 10 days in advance during snowstorm -> High no-show risk (> 25%)
        features_b = {
            "lead_time_hours": 240.0,
            "is_prepaid": False,
            "day_of_week": 2,
            "departure_hour": 10,
            "bad_weather": True,
            "passenger_prior_trips": 0
        }
        res_b = ML_PREDICTOR.predict(features_b)
        self.assertGreater(res_b.no_show_probability, 0.20)
        self.assertIn("Оплата наличными водителю", [f.name for f in res_b.top_factors])

        # Drift test
        for _ in range(25):
            ML_PREDICTOR.predict(features_a)
            ML_PREDICTOR.record_actual_outcome(boarded=True)
        drift = ML_PREDICTOR.calculate_drift_metrics()
        self.assertIn(drift["status"], ["calibrating", "healthy", "drift_detected"])
        self.assertGreater(drift["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
