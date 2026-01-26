"""
Minimal test handler - no dependencies, just returns a response
"""
import json

def handler(event, context):
    """Minimal handler to test if Vercel Python functions work at all"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": True, "message": "Test handler works", "event_keys": list(event.keys()) if isinstance(event, dict) else "not_dict"})
    }

