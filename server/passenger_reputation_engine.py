#!/usr/bin/env python3
"""
BusLiner Two-Sided Passenger Reputation Engine (Feature 13)
===========================================================
Market-driven bilateral trust architecture for CIS intercity minibus transport.
Calculates passenger Trust Score (0–100), governs Seat Sniper queue priority,
eliminates no-shows, and gates payment methods without alienating regular users.

Design Rules:
  - Strictly 0 emojis in code, data, and telemetry.
  - Quiet Luxury terminology (Elite, Verified, Standard, Monitored).
  - Soft launch: Reputation impacts priorities and benefits, rather than banning purchases.
"""

import time
import math
import sqlite3
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "busliner.db")


@dataclass
class DriverReviewOnPassenger:
    review_id: str
    user_id: str
    driver_id: str
    trip_id: str
    rating: float           # 1.0 to 5.0
    was_punctual: bool      # Did passenger arrive on time for boarding
    was_no_show: bool       # Did passenger fail to appear
    tags: List[str]         # ['вежливый', 'чистый багаж', 'быстрая посадка', 'опоздание', 'конфликт']
    comment: Optional[str]
    created_at: float = field(default_factory=time.time)


@dataclass
class PassengerTrustProfile:
    user_id: str
    phone: Optional[str]
    full_name: str
    trust_score: float             # 0.0 to 100.0 (Base starting score: 75.0)
    trust_tier: str                # 'elite', 'verified', 'probation', 'restricted'
    tier_label: str                # Human-readable Russian label
    trips_completed: int = 0
    on_time_arrivals: int = 0
    no_shows_count: int = 0
    late_cancellations: int = 0
    driver_ratings_avg: float = 5.0
    driver_reviews_count: int = 0
    punctuality_rate: float = 1.0  # 0.0 to 1.0
    # Privilege & Restriction Flags
    sniper_priority_level: int = 2 # 1: Highest (Elite), 2: Standard, 3: Probation, 0: Blocked
    pay_on_board_allowed: bool = True
    late_cancellation_fee_waived: bool = False
    max_active_snipers: int = 3
    early_booking_days: int = 14
    reputation_badges: List[str] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PassengerReputationEngine:
    """
    Computes bilateral reputation metrics and enforces market incentives:
      - Elite (90–100): Priority Seat Sniper, 0-fee cancellation, VIP single seats
      - Verified (70–89): Normal Sniper Queue, pay-on-board permitted
      - Probation (40–69): Pre-auth required, 1 active sniper max
      - Restricted (<40): 100% upfront card prepayment, sniper cooldown 14 days
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._profiles_cache: Dict[str, PassengerTrustProfile] = {}
        self.init_reputation_schema()

    def init_reputation_schema(self) -> None:
        """Initializes database tables for passenger trust profiles and driver reviews."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS passenger_trust_profiles (
                        user_id TEXT PRIMARY KEY,
                        phone TEXT,
                        full_name TEXT,
                        trust_score REAL DEFAULT 75.0,
                        trust_tier TEXT DEFAULT 'verified',
                        trips_completed INTEGER DEFAULT 0,
                        on_time_arrivals INTEGER DEFAULT 0,
                        no_shows_count INTEGER DEFAULT 0,
                        late_cancellations INTEGER DEFAULT 0,
                        driver_ratings_avg REAL DEFAULT 5.0,
                        driver_reviews_count INTEGER DEFAULT 0,
                        updated_at REAL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS driver_passenger_reviews (
                        review_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        driver_id TEXT NOT NULL,
                        trip_id TEXT NOT NULL,
                        rating REAL NOT NULL,
                        was_punctual INTEGER DEFAULT 1,
                        was_no_show INTEGER DEFAULT 0,
                        tags TEXT,
                        comment TEXT,
                        created_at REAL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_driver_reviews_user ON driver_passenger_reviews(user_id)")
                conn.commit()
        except Exception as e:
            print(f"[PassengerReputationEngine] DB init warning: {e}", file=sys.stderr)

    def get_or_create_profile(self, user_id: str, phone: Optional[str] = None, full_name: Optional[str] = None) -> PassengerTrustProfile:
        """Fetches or registers a passenger trust profile."""
        if user_id in self._profiles_cache:
            return self._profiles_cache[user_id]

        profile = None
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, phone, full_name, trust_score, trust_tier, trips_completed, on_time_arrivals, no_shows_count, late_cancellations, driver_ratings_avg, driver_reviews_count FROM passenger_trust_profiles WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    profile = self._build_profile_from_row(row)
        except Exception:
            pass

        if not profile:
            # Default profile for new verified passengers (base score 75.0)
            clean_name = full_name or "Пассажир"
            profile = self._calculate_privileges(
                user_id=user_id,
                phone=phone,
                full_name=clean_name,
                trust_score=75.0,
                trips_completed=0,
                on_time_arrivals=0,
                no_shows_count=0,
                late_cancellations=0,
                driver_ratings_avg=5.0,
                driver_reviews_count=0
            )
            self._save_profile_to_db(profile)

        self._profiles_cache[user_id] = profile
        return profile

    def record_trip_completion(self, user_id: str, was_punctual: bool = True, driver_rating: float = 5.0) -> PassengerTrustProfile:
        """Reward on-time appearance and trip completion."""
        p = self.get_or_create_profile(user_id)
        p.trips_completed += 1
        if was_punctual:
            p.on_time_arrivals += 1

        # Update running driver rating average
        tot = (p.driver_ratings_avg * p.driver_reviews_count) + driver_rating
        p.driver_reviews_count += 1
        p.driver_ratings_avg = round(tot / p.driver_reviews_count, 2)

        # Recalculate score
        p.trust_score = self._compute_raw_score(p)
        updated = self._calculate_privileges(
            user_id=p.user_id,
            phone=p.phone,
            full_name=p.full_name,
            trust_score=p.trust_score,
            trips_completed=p.trips_completed,
            on_time_arrivals=p.on_time_arrivals,
            no_shows_count=p.no_shows_count,
            late_cancellations=p.late_cancellations,
            driver_ratings_avg=p.driver_ratings_avg,
            driver_reviews_count=p.driver_reviews_count
        )
        self._profiles_cache[user_id] = updated
        self._save_profile_to_db(updated)
        return updated

    def record_no_show(self, user_id: str, trip_id: str) -> PassengerTrustProfile:
        """Strong penalty for failing to show up without cancellation (-25 points)."""
        p = self.get_or_create_profile(user_id)
        p.no_shows_count += 1
        p.trust_score = max(5.0, p.trust_score - 25.0)

        updated = self._calculate_privileges(
            user_id=p.user_id,
            phone=p.phone,
            full_name=p.full_name,
            trust_score=p.trust_score,
            trips_completed=p.trips_completed,
            on_time_arrivals=p.on_time_arrivals,
            no_shows_count=p.no_shows_count,
            late_cancellations=p.late_cancellations,
            driver_ratings_avg=p.driver_ratings_avg,
            driver_reviews_count=p.driver_reviews_count
        )
        self._profiles_cache[user_id] = updated
        self._save_profile_to_db(updated)
        return updated

    def record_late_cancellation(self, user_id: str, trip_id: str, hours_before_trip: float) -> PassengerTrustProfile:
        """Moderate penalty for cancelling < 2 hours before trip (-12 points)."""
        p = self.get_or_create_profile(user_id)
        p.late_cancellations += 1
        penalty = 12.0 if hours_before_trip < 2.0 else 4.0
        p.trust_score = max(10.0, p.trust_score - penalty)

        updated = self._calculate_privileges(
            user_id=p.user_id,
            phone=p.phone,
            full_name=p.full_name,
            trust_score=p.trust_score,
            trips_completed=p.trips_completed,
            on_time_arrivals=p.on_time_arrivals,
            no_shows_count=p.no_shows_count,
            late_cancellations=p.late_cancellations,
            driver_ratings_avg=p.driver_ratings_avg,
            driver_reviews_count=p.driver_reviews_count
        )
        self._profiles_cache[user_id] = updated
        self._save_profile_to_db(updated)
        return updated

    def submit_driver_review(
        self,
        driver_id: str,
        user_id: str,
        trip_id: str,
        rating: float,
        was_punctual: bool,
        was_no_show: bool,
        tags: List[str],
        comment: Optional[str] = None
    ) -> DriverReviewOnPassenger:
        """Saves bilateral driver review on passenger behavior."""
        review_id = f"rev_{abs(hash(driver_id + user_id + trip_id + str(time.time()))) % 1000000:06d}"
        rev = DriverReviewOnPassenger(
            review_id=review_id,
            user_id=user_id,
            driver_id=driver_id,
            trip_id=trip_id,
            rating=rating,
            was_punctual=was_punctual,
            was_no_show=was_no_show,
            tags=tags,
            comment=comment
        )

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO driver_passenger_reviews 
                    (review_id, user_id, driver_id, trip_id, rating, was_punctual, was_no_show, tags, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (review_id, user_id, driver_id, trip_id, rating, 1 if was_punctual else 0, 1 if was_no_show else 0, json_tags := ",".join(tags), comment, rev.created_at))
                conn.commit()
        except Exception as e:
            print(f"[PassengerReputationEngine] Failed to save driver review: {e}", file=sys.stderr)

        if was_no_show:
            self.record_no_show(user_id, trip_id)
        else:
            self.record_trip_completion(user_id, was_punctual=was_punctual, driver_rating=rating)

        return rev

    def _compute_raw_score(self, p: PassengerTrustProfile) -> float:
        """Mathematical formula for trust score."""
        base = 75.0
        trip_bonus = min(20.0, p.trips_completed * 2.0)
        punct_ratio = (p.on_time_arrivals / p.trips_completed) if p.trips_completed > 0 else 1.0
        punct_bonus = (punct_ratio - 0.5) * 10.0
        driver_bonus = (p.driver_ratings_avg - 4.0) * 8.0

        penalties = (p.no_shows_count * 25.0) + (p.late_cancellations * 10.0)

        score = base + trip_bonus + punct_bonus + driver_bonus - penalties
        return round(max(5.0, min(100.0, score)), 1)

    def _calculate_privileges(
        self,
        user_id: str,
        phone: Optional[str],
        full_name: str,
        trust_score: float,
        trips_completed: int,
        on_time_arrivals: int,
        no_shows_count: int,
        late_cancellations: int,
        driver_ratings_avg: float,
        driver_reviews_count: int
    ) -> PassengerTrustProfile:
        punct_rate = round((on_time_arrivals / trips_completed) if trips_completed > 0 else 1.0, 2)

        badges = []
        if trips_completed >= 10:
            badges.append("Постоянный пассажир")
        if punct_rate >= 0.95 and trips_completed >= 5:
            badges.append("100% пунктуальность")
        if driver_ratings_avg >= 4.8 and driver_reviews_count >= 3:
            badges.append("Выбор экипажей")

        if trust_score >= 90.0:
            tier = "elite"
            tier_label = "Elite / Platinum"
            sniper_prio = 1  # Top of queue
            pay_on_board = True
            waive_cancel = True
            max_snipers = 5
            early_days = 30
            badges.append("Приоритет снайпера №1")
        elif trust_score >= 70.0:
            tier = "verified"
            tier_label = "Verified / Проверенный"
            sniper_prio = 2
            pay_on_board = True
            waive_cancel = False
            max_snipers = 3
            early_days = 14
        elif trust_score >= 40.0:
            tier = "probation"
            tier_label = "Probation / Внимательный"
            sniper_prio = 3
            pay_on_board = False # Strict card pre-auth only
            waive_cancel = False
            max_snipers = 1
            early_days = 7
        else:
            tier = "restricted"
            tier_label = "Restricted / Ограниченный"
            sniper_prio = 0 # Blocked from sniper
            pay_on_board = False # 100% upfront card payment only
            waive_cancel = False
            max_snipers = 0
            early_days = 2

        return PassengerTrustProfile(
            user_id=user_id,
            phone=phone,
            full_name=full_name,
            trust_score=trust_score,
            trust_tier=tier,
            tier_label=tier_label,
            trips_completed=trips_completed,
            on_time_arrivals=on_time_arrivals,
            no_shows_count=no_shows_count,
            late_cancellations=late_cancellations,
            driver_ratings_avg=driver_ratings_avg,
            driver_reviews_count=driver_reviews_count,
            punctuality_rate=punct_rate,
            sniper_priority_level=sniper_prio,
            pay_on_board_allowed=pay_on_board,
            late_cancellation_fee_waived=waive_cancel,
            max_active_snipers=max_snipers,
            early_booking_days=early_days,
            reputation_badges=badges
        )

    def _build_profile_from_row(self, row: Tuple[Any, ...]) -> PassengerTrustProfile:
        uid, phone, name, score, tier, trips, on_time, no_shows, late_cancels, drv_avg, drv_cnt = row
        return self._calculate_privileges(
            user_id=uid,
            phone=phone,
            full_name=name or "Пассажир",
            trust_score=score or 75.0,
            trips_completed=trips or 0,
            on_time_arrivals=on_time or 0,
            no_shows_count=no_shows or 0,
            late_cancellations=late_cancels or 0,
            driver_ratings_avg=drv_avg or 5.0,
            driver_reviews_count=drv_cnt or 0
        )

    def _save_profile_to_db(self, p: PassengerTrustProfile) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO passenger_trust_profiles
                    (user_id, phone, full_name, trust_score, trust_tier, trips_completed, on_time_arrivals, no_shows_count, late_cancellations, driver_ratings_avg, driver_reviews_count, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p.user_id, p.phone, p.full_name, p.trust_score, p.trust_tier, p.trips_completed, p.on_time_arrivals, p.no_shows_count, p.late_cancellations, p.driver_ratings_avg, p.driver_reviews_count, time.time()))
                conn.commit()
        except Exception as e:
            print(f"[PassengerReputationEngine] Save error: {e}", file=sys.stderr)


# Global singleton instance
passenger_reputation_engine = PassengerReputationEngine()


if __name__ == "__main__":
    print("Testing Passenger Reputation Engine (Two-Sided Trust)...")
    engine = PassengerReputationEngine()
    
    # 1. New passenger
    p1 = engine.get_or_create_profile("user_demo_alpha", "+375291112233", "Александр Волков")
    print(f"New Passenger: {p1.full_name} | Score: {p1.trust_score} ({p1.trust_tier.upper()}) | Priority: {p1.sniper_priority_level}")

    # 2. Complete 5 on-time trips with 5-star driver ratings
    for _ in range(5):
        p1 = engine.record_trip_completion("user_demo_alpha", was_punctual=True, driver_rating=5.0)
    print(f"After 5 Trips: Score: {p1.trust_score} ({p1.tier_label}) | Sniper Priority: Level {p1.sniper_priority_level} | Badges: {p1.reputation_badges}")

    # 3. Simulate No-Show
    p2 = engine.get_or_create_profile("user_demo_beta", "+375292223344", "Ненадежный Пассажир")
    p2 = engine.record_no_show("user_demo_beta", "BL-5715")
    print(f"After No-Show: {p2.full_name} | Score: {p2.trust_score} ({p2.tier_label}) | Pay on Board: {p2.pay_on_board_allowed} | Sniper: Level {p2.sniper_priority_level}")
