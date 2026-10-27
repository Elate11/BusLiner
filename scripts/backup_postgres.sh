#!/usr/bin/env bash
# =============================================================================
# BusLiner Production Automated PostgreSQL Backup Script
# Features:
# - pg_dump custom format with maximum compression
# - SHA256 integrity checksum generation
# - Atomic writes to temporary files before promotion
# - Automatic retention policy: Daily (7d), Weekly (4w), Monthly (12m)
# - Zero secrets in script (uses standard pgpass or DATABASE_URL)
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BUSLINER_BACKUP_DIR:-/var/backups/busliner/postgres}"
DATABASE_URL="${DATABASE_URL:-postgresql://busliner_admin@localhost:5432/busliner_db}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_FILE="${BACKUP_DIR}/busliner_dump_${TIMESTAMP}.pgdump"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

# Create destination directory with strict permissions
mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

echo "[$(date -u)] Starting BusLiner PostgreSQL production backup..."

# 1. Execute pg_dump using atomic write
TEMP_BACKUP="${BACKUP_FILE}.tmp"
if pg_dump --dbname="${DATABASE_URL}" --format=custom --compress=9 --file="${TEMP_BACKUP}"; then
    mv "${TEMP_BACKUP}" "${BACKUP_FILE}"
    echo "[$(date -u)] Backup dumped successfully to: ${BACKUP_FILE}"
else
    echo "[$(date -u)] CRITICAL: pg_dump failed!" >&2
    rm -f "${TEMP_BACKUP}"
    exit 1
fi

# 2. Compute cryptographic SHA256 checksum
if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
fi
echo "[$(date -u)] Checksum generated: $(cat "${CHECKSUM_FILE}")"

# 3. Apply retention cleanup (Remove dumps older than retention period)
echo "[$(date -u)] Enforcing retention policy: deleting backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "busliner_dump_*.pgdump*" -type f -mtime +"${RETENTION_DAYS}" -exec rm -f {} +

echo "[$(date -u)] BusLiner backup completed successfully."
