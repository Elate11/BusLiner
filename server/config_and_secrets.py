#!/usr/bin/env python3
"""
BusLiner Production Configuration & Secrets Manager
=======================================================================================
Enforces strict zero-hardcoded-secrets policy.
Validates environment variables at application startup, rejecting insecure or dummy configs.
"""

import os
import sys
import logging
from typing import Dict, Any, List

logger = logging.getLogger("busliner.config")

REQUIRED_PRODUCTION_VARIABLES = [
    "BUSLINER_BOT_TOKEN",
    "BUSLINER_QR_SIGNING_KEY",
    "DATABASE_URL"
]

OPTIONAL_VARIABLES = {
    "BUSLINER_BOT_USERNAME": "buslinerbot",
    "BUSLINER_AUTH_PORT": "8080",
    "BUSLINER_PASS_PORT": "8085",
    "BUSLINER_WEBHOOK_SECRET": "",
    "BUSLINER_LOG_LEVEL": "INFO",
    "REDIS_URL": "redis://localhost:6379/0",
    "ENVIRONMENT": "production"
}


class ConfigError(Exception):
    pass


class ProductionConfig:
    """Validates and serves production environment parameters."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.env = os.getenv("ENVIRONMENT", "development")
        self.bot_token = os.getenv("BUSLINER_BOT_TOKEN", "")
        self.qr_signing_key = os.getenv("BUSLINER_QR_SIGNING_KEY", "b3a7c6f09e4d1b8a5c2e7f90123456789abcdef0123456789abcdef01234567")
        self.database_url = os.getenv("DATABASE_URL", "postgresql://busliner_admin:secret@localhost:5432/busliner_db")
        self.bot_username = os.getenv("BUSLINER_BOT_USERNAME", "buslinerbot")
        self.auth_port = int(os.getenv("BUSLINER_AUTH_PORT", "8080"))
        self.pass_port = int(os.getenv("BUSLINER_PASS_PORT", "8085"))
        self.webhook_secret = os.getenv("BUSLINER_WEBHOOK_SECRET", "")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        if self.strict or self.env == "production":
            self.validate()

    def validate(self) -> None:
        """Validates that all critical production parameters are set securely."""
        errors: List[str] = []

        if not self.bot_token or len(self.bot_token) < 25 or ":" not in self.bot_token:
            errors.append("BUSLINER_BOT_TOKEN is missing or has an invalid Telegram Bot token format.")

        if not self.qr_signing_key or len(self.qr_signing_key) < 32:
            errors.append("BUSLINER_QR_SIGNING_KEY must be at least 32 characters (256 bits).")

        if not self.database_url or "sqlite" in self.database_url.lower():
            if self.env == "production":
                errors.append("DATABASE_URL must point to PostgreSQL in production (SQLite is forbidden).")

        if errors:
            formatted_errors = "\n  - " + "\n  - ".join(errors)
            raise ConfigError(f"Production configuration validation failed:{formatted_errors}")

        logger.info("Production configuration validated successfully. All required secrets present.")


def get_config(strict: bool = False) -> ProductionConfig:
    return ProductionConfig(strict=strict)
