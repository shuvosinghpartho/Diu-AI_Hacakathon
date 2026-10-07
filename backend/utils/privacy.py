import re
import copy

def redact_pii(data: dict) -> dict:
    """
    Recursively scans and masks PII (Personally Identifiable Information) 
    such as NID, phone numbers, and passport numbers for secure audit logging.
    """
    if not isinstance(data, dict):
        return data

    redacted = copy.deepcopy(data)
    
    # Simple recursive function
    def _mask(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ["nid_number", "passport_number", "sender", "receiver", "agent_number"]:
                    if isinstance(v, str) and len(v) > 4:
                        obj[k] = v[:2] + "*" * (len(v) - 4) + v[-2:]
                elif isinstance(v, str):
                    # Catch NID / Phones in raw text logs
                    obj[k] = re.sub(r'\b(01[3-9][0-9]{8})\b', r'01X-XXXX-XX\1'[-2:], v)
                elif isinstance(v, (dict, list)):
                    _mask(v)
        elif isinstance(obj, list):
            for item in obj:
                _mask(item)

    _mask(redacted)
    return redacted
