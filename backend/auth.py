import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# In production, this would be validated against a secure vault or database.
VALID_API_KEYS = {
    "vp-live-2026-secure-key",
    "vp-test-key-local",
    os.getenv("VISIONPAY_API_KEY", "")
}

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header or api_key_header not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Access denied.",
        )
    return api_key_header
