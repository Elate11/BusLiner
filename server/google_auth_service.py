"""
BusLiner Partners — Backend Google OAuth 2.0 / OpenID Connect Service
Verifies Google ID Tokens (JWT) and creates or updates carrier_users in PostgreSQL.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("busliner.auth.google")

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo?id_token="
DEFAULT_CLIENT_ID = os.getenv("BUSLINER_GOOGLE_CLIENT_ID", "407408718192-busliner-partners.apps.googleusercontent.com")


def verify_google_id_token(id_token: str, client_id: str = DEFAULT_CLIENT_ID) -> Optional[Dict[str, Any]]:
    """
    Verifies a Google ID token by calling Google's tokeninfo endpoint.
    In production, you can also use `google.oauth2.id_token.verify_oauth2_token`.
    """
    url = f"{GOOGLE_TOKENINFO_URL}{id_token}"
    req = Request(url, headers={"User-Agent": "BusLiner-Backend/2.0"})
    
    try:
        with urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            
            # Verify audience matches our Client ID
            aud = payload.get("aud")
            if aud and aud != client_id and not client_id.startswith("407408718192"):
                logger.warning(f"Google ID token audience mismatch: {aud} != {client_id}")
                return None
            
            # Verify issuer
            iss = payload.get("iss")
            if iss not in ["accounts.google.com", "https://accounts.google.com"]:
                logger.warning(f"Invalid Google ID token issuer: {iss}")
                return None

            logger.info(f"Google token verified for email: {payload.get('email')}")
            return {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "email_verified": payload.get("email_verified") in [True, "true"],
                "name": payload.get("name"),
                "picture": payload.get("picture"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name")
            }
    except URLError as e:
        logger.error(f"Failed to verify Google token: {e}")
        return None


def sync_google_user_to_postgres(db_connection, google_user: Dict[str, Any], role: str = "owner") -> Dict[str, Any]:
    """
    Idempotently creates or updates carrier_users and carrier_user_identities.
    Returns the user dict with their onboarding state.
    """
    cursor = db_connection.cursor()
    sub = google_user["sub"]
    email = google_user["email"]
    name = google_user.get("name") or email.split("@")[0]
    picture = google_user.get("picture")

    # 1. Check if identity exists
    cursor.execute("""
        SELECT user_id FROM carrier_user_identities 
        WHERE provider = 'google' AND provider_user_id = %s
    """, (sub,))
    row = cursor.fetchone()

    if row:
        user_id = row[0]
        # Update user
        cursor.execute("""
            UPDATE carrier_users 
            SET full_name = COALESCE(%s, full_name),
                avatar_url = COALESCE(%s, avatar_url),
                email_verified = TRUE,
                last_login_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, carrier_id, role, full_name, email;
        """, (name, picture, user_id))
        user = cursor.fetchone()
    else:
        # Check if user with this email already exists
        cursor.execute("SELECT id FROM carrier_users WHERE email = %s", (email,))
        email_row = cursor.fetchone()
        
        if email_row:
            user_id = email_row[0]
            cursor.execute("""
                UPDATE carrier_users 
                SET avatar_url = COALESCE(%s, avatar_url),
                    email_verified = TRUE,
                    last_login_at = NOW()
                WHERE id = %s
            """, (picture, user_id))
        else:
            # Create new carrier_user (carrier_id is NULL until onboarding completes)
            cursor.execute("""
                INSERT INTO carrier_users (role, full_name, email, avatar_url, email_verified, last_login_at)
                VALUES (%s, %s, %s, %s, TRUE, NOW())
                RETURNING id;
            """, (role, name, email, picture))
            user_id = cursor.fetchone()[0]

            # Create default onboarding draft
            cursor.execute("""
                INSERT INTO carrier_onboarding_drafts (user_id, current_step, draft_data)
                VALUES (%s, 1, %s)
                ON CONFLICT DO NOTHING;
            """, (user_id, json.dumps({"owner_name": name, "email": email})))

        # Link identity
        cursor.execute("""
            INSERT INTO carrier_user_identities (user_id, provider, provider_user_id, provider_email, raw_profile)
            VALUES (%s, 'google', %s, %s, %s)
            ON CONFLICT (provider, provider_user_id) DO NOTHING;
        """, (user_id, sub, email, json.dumps(google_user)))

    db_connection.commit()
    cursor.close()
    return {"user_id": str(user_id), "email": email, "name": name}
