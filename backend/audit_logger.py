import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Request

logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)

async def log_audit_action(db: AsyncIOMotorDatabase, request: Request, action: str, details: dict):
    """
    Centralized audit logging for API requests.
    Supports future integration with centralized logging systems (e.g. ELK, Datadog)
    """
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key", "unauthenticated")
    
    audit_entry = {
        "timestamp": datetime.now(timezone.utc),
        "client_ip": client_ip,
        "api_key_used": api_key,
        "action": action,
        "details": details,
    }
    
    # Write to local console/stdout for container logging
    logger.info(f"AUDIT_LOG: {action} from {client_ip} [Key: {api_key}]")
    
    # Write to MongoDB for persistence
    try:
        await db.audit_logs.insert_one(audit_entry)
    except Exception as e:
        logger.error(f"Failed to write audit log to DB: {e}")
