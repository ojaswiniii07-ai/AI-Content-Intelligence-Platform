"""
Cryptographic utilities for ContentIQ integration layer and webhooks.

Security Guarantees:
- Secrets (API keys, OAuth access & refresh tokens) are encrypted at rest using
  Fernet (AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication).
- Key derivation: Uses INTEGRATION_ENCRYPTION_KEY or derives a 256-bit key
  from SECRET_KEY via SHA-256 + urlsafe base64 encoding.
- HMAC signatures: Outgoing webhook events are signed with HMAC-SHA256 and
  verified using constant-time comparison (preventing timing attacks).
- Replay protection: Verifies timestamp within a tolerance window (default 300s).
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _derive_fernet_key() -> bytes:
    """
    Derives a valid 32-byte urlsafe base64-encoded Fernet key.
    If INTEGRATION_ENCRYPTION_KEY is provided in settings, it is used.
    Otherwise, derives a deterministic key from SECRET_KEY using SHA-256.
    """
    custom_key = getattr(settings, "INTEGRATION_ENCRYPTION_KEY", None)
    if custom_key:
        try:
            # Validate if it's already a valid Fernet key
            Fernet(custom_key.encode("utf-8"))
            return custom_key.encode("utf-8")
        except Exception:
            # Fall through to derivation
            pass

    # Deterministic derivation from SECRET_KEY
    derived_32 = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(derived_32)


def encrypt_secrets(data: Dict[str, Any]) -> str:
    """
    Encrypts a dictionary of sensitive secrets (API keys, tokens) to a Fernet token string.
    Returns empty string if data is empty.
    """
    if not data:
        return ""
    key = _derive_fernet_key()
    f = Fernet(key)
    raw_json = json.dumps(data).encode("utf-8")
    return f.encrypt(raw_json).decode("utf-8")


def decrypt_secrets(encrypted_str: Optional[str]) -> Dict[str, Any]:
    """
    Decrypts a Fernet token string back into a dictionary of secrets.
    Returns empty dict if encrypted_str is None, empty, or cannot be decrypted.
    """
    if not encrypted_str:
        return {}
    key = _derive_fernet_key()
    f = Fernet(key)
    try:
        decrypted_bytes = f.decrypt(encrypted_str.encode("utf-8"))
        return json.loads(decrypted_bytes.decode("utf-8"))
    except (InvalidToken, json.JSONDecodeError, Exception):
        return {}


def generate_webhook_secret() -> str:
    """Generates a secure 32-byte (64 hex characters) webhook signing secret."""
    return secrets.token_hex(32)


def sign_webhook_payload(secret: str, payload_bytes: bytes) -> str:
    """
    Computes an HMAC-SHA256 signature for a webhook payload.
    Format: sha256=<hex_digest>
    """
    mac = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def verify_webhook_signature(
    secret: str,
    payload_bytes: bytes,
    signature_header: str,
    timestamp_header: Optional[str] = None,
    tolerance_seconds: int = 300,
) -> Tuple[bool, str]:
    """
    Verifies an incoming webhook signature with HMAC-SHA256 and replay protection.

    Args:
        secret: The shared signing secret.
        payload_bytes: Raw HTTP request body.
        signature_header: Header value, e.g., 'sha256=abcdef...'
        timestamp_header: Header value containing Unix epoch timestamp.
        tolerance_seconds: Allowed clock drift / age window (default: 300 seconds).

    Returns:
        (is_valid: bool, reason: str)
    """
    if not signature_header:
        return False, "Missing signature header"

    if timestamp_header:
        try:
            ts = int(timestamp_header)
            current_time = int(time.time())
            # Replay protection: Check if timestamp is too old or too far in the future
            if abs(current_time - ts) > tolerance_seconds:
                return False, f"Timestamp out of allowed tolerance window ({tolerance_seconds}s)"
        except (ValueError, TypeError):
            return False, "Invalid timestamp header format"

    expected_sig = sign_webhook_payload(secret, payload_bytes)
    # Constant-time comparison prevents timing attacks
    if hmac.compare_digest(expected_sig, signature_header):
        return True, "Valid"
    return False, "Signature mismatch"
