#!/usr/bin/env python3
"""
BusLiner Offline Driver Check-in & Cryptographic QR Verification System
=======================================================================================
Enables full offline boarding on the platform with:
1. Cryptographic QR Signature (HMAC-SHA256 with timestamp & nonce)
2. Local Verification (Zero network roundtrip required on platform)
3. Manifest Cache with version digest
4. Resilient Offline Sync Queue with conflict resolution and idempotency
"""

import os
import time
import json
import hmac
import hashlib
import secrets
from typing import Dict, Any, Tuple, Optional, List

# Production Secret key for QR ticket signing (loaded from environment)
DEFAULT_QR_SIGNING_KEY = os.getenv("BUSLINER_QR_SIGNING_KEY", "b3a7c6f09e4d1b8a5c2e7f90123456789abcdef0123456789abcdef01234567")


class QRCodeSigner:
    """Signs and verifies tamper-proof passenger boarding passes."""

    def __init__(self, secret_key: str = DEFAULT_QR_SIGNING_KEY):
        self.secret_key = secret_key.encode("utf-8")

    def generate_signed_qr_payload(self, ticket_id: str, trip_id: str, seat_no: int,
                                   passenger_name: str, valid_until_epoch: Optional[int] = None) -> str:
        """
        Creates an encrypted/signed string payload suitable for rendering as an SVG QR Code.
        Format: BL2:<ticket_id>:<trip_id>:<seat_no>:<issued_at>:<expires_at>:<nonce>:<signature>
        """
        issued_at = int(time.time())
        # Default expiration: 48 hours after issue
        expires_at = valid_until_epoch if valid_until_epoch else (issued_at + 172800)
        nonce = secrets.token_hex(4)

        base_string = f"{ticket_id}|{trip_id}|{seat_no}|{passenger_name.strip()}|{issued_at}|{expires_at}|{nonce}"
        signature = hmac.new(self.secret_key, base_string.encode("utf-8"), hashlib.sha256).hexdigest()[:24]

        # Compact payload with Base64 / colon encoding
        payload = {
            "v": 2,
            "t": ticket_id,
            "trip": trip_id,
            "seat": seat_no,
            "name": passenger_name.strip(),
            "iat": issued_at,
            "exp": expires_at,
            "nonce": nonce,
            "sig": signature
        }
        return json.dumps(payload, separators=(',', ':'))

    def verify_qr_payload(self, raw_payload_str: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies ticket signature without network access.
        Returns: (is_valid, reason_or_message, ticket_data)
        """
        try:
            data = json.loads(raw_payload_str)
        except Exception:
            return False, "Неверный формат QR-кода: поврежден JSON", None

        required_keys = {"v", "t", "trip", "seat", "name", "iat", "exp", "nonce", "sig"}
        if not required_keys.issubset(data.keys()):
            return False, "Неполная цифровая подпись в QR-коде", None

        # Check expiration
        now = int(time.time())
        if now > data["exp"]:
            return False, f"Срок действия билета истек (истек {time.ctime(data['exp'])})", data

        # Verify HMAC-SHA256 signature in constant-time
        base_string = f"{data['t']}|{data['trip']}|{data['seat']}|{data['name']}|{data['iat']}|{data['exp']}|{data['nonce']}"
        expected_sig = hmac.new(self.secret_key, base_string.encode("utf-8"), hashlib.sha256).hexdigest()[:24]

        if not hmac.compare_digest(expected_sig, data["sig"]):
            return False, "КРИТИЧЕСКАЯ ОШИБКА: Поддельная цифровая подпись билета!", None

        return True, "Билет подлинный и действителен для посадки", data


class ManifestManager:
    """Manages offline manifest caching, signatures, and delta synchronization."""

    def __init__(self):
        self.cached_manifests: Dict[str, Dict[str, Any]] = {}
        self.processed_sync_actions: Set[str] = set()

    def generate_manifest_digest(self, trip_id: str, passengers_list: List[Dict[str, Any]]) -> str:
        """Calculates a SHA-256 digest of the current passenger list for cache validation."""
        sorted_passengers = sorted(passengers_list, key=lambda p: p["seat"])
        payload = json.dumps(sorted_passengers, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def process_sync_batch(self, driver_id: str, trip_id: str,
                           actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes a batch of offline check-in events replayed by the driver's device.
        Guarantees idempotency and conflict resolution.
        """
        synced_count = 0
        conflicts = []

        for action in actions:
            action_id = action.get("sync_id", f"{action.get('ticket_id')}_{action.get('timestamp')}")
            ticket_id = action.get("ticket_id")

            if action_id in self.processed_sync_actions:
                # Idempotent replay: already synced
                synced_count += 1
                continue

            # Verify QR signature submitted with sync
            qr_data = action.get("qr_data")
            is_valid = True
            if qr_data:
                valid, msg, _ = QRCodeSigner().verify_qr_payload(json.dumps(qr_data) if isinstance(qr_data, dict) else str(qr_data))
                if not valid:
                    is_valid = False
                    conflicts.append({
                        "ticket_id": ticket_id,
                        "conflict": "invalid_signature",
                        "details": msg
                    })
                    continue

            self.processed_sync_actions.add(action_id)
            synced_count += 1

        return {
            "success": True,
            "trip_id": trip_id,
            "synced_count": synced_count,
            "conflicts_count": len(conflicts),
            "conflicts": conflicts,
            "server_timestamp": time.time()
        }
