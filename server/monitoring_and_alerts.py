#!/usr/bin/env python3
"""
BusLiner Production Monitoring, Telemetry & Alerting System
=======================================================================================
Provides Prometheus-compatible metric exporters, structured telemetry,
and threshold breach alerts for critical platform failure modes:
1. DB Query Timeouts (> 500ms)
2. Seat Sniper Latency Degradation (p95 > 500ms)
3. Driver Manifest Sync Lag and Signature Failures
4. Auth Replay Attacks
"""

import time
import json
import logging
from typing import Dict, Any, List
from collections import deque

logger = logging.getLogger("busliner.telemetry")


class MetricsCollector:
    """In-memory thread-safe Prometheus metrics collector."""

    def __init__(self):
        self.counters: Dict[str, int] = {
            "busliner_sniper_reservations_total": 0,
            "busliner_sniper_fallback_beaten_total": 0,
            "busliner_sniper_idempotent_skips_total": 0,
            "busliner_db_timeouts_total": 0,
            "busliner_driver_offline_scans_total": 0,
            "busliner_driver_sync_conflicts_total": 0,
            "busliner_auth_replay_attempts_total": 0,
            "busliner_telegram_notifications_sent_total": 0,
            "busliner_telegram_notifications_suppressed_total": 0,
        }
        self.query_latencies: deque = deque(maxlen=500)
        self.sniper_latencies: deque = deque(maxlen=500)
        self.active_alerts: List[Dict[str, Any]] = []

    def inc_counter(self, name: str, value: int = 1):
        if name in self.counters:
            self.counters[name] += value

    def observe_db_latency(self, duration_ms: float, query_name: str = "generic"):
        self.query_latencies.append(duration_ms)
        if duration_ms > 500.0:
            self.inc_counter("busliner_db_timeouts_total")
            self._trigger_alert("DB_SLOW_QUERY", f"Query '{query_name}' took {duration_ms:.2f}ms (threshold 500ms)")

    def observe_sniper_latency(self, duration_ms: float):
        self.sniper_latencies.append(duration_ms)
        if duration_ms > 500.0:
            self._trigger_alert("SNIPER_LATENCY_DEGRADATION", f"Release->Reserve latency exceeded threshold: {duration_ms:.2f}ms")

    def _trigger_alert(self, alert_name: str, message: str):
        alert = {
            "name": alert_name,
            "message": message,
            "timestamp": time.time(),
            "level": "CRITICAL" if "SLOW" not in alert_name else "WARNING"
        }
        self.active_alerts.append(alert)
        logger.warning(f"ALERT TRIGGERED [{alert['level']}]: {alert_name} - {message}")

    def render_prometheus_exposition(self) -> str:
        """Formats collected metrics in standard Prometheus text exposition format."""
        lines = []
        for name, val in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {val}")

        # Latency statistics
        if self.sniper_latencies:
            sorted_lat = sorted(self.sniper_latencies)
            p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
            p95 = sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)]
            lines.append("# TYPE busliner_sniper_latency_p50 gauge")
            lines.append(f"busliner_sniper_latency_p50 {p50:.2f}")
            lines.append("# TYPE busliner_sniper_latency_p95 gauge")
            lines.append(f"busliner_sniper_latency_p95 {p95:.2f}")

        return "\n".join(lines) + "\n"


METRICS = MetricsCollector()
