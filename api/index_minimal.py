"""
Minimal test handler to isolate the issue
"""
import json

def handler(event, context):
    """Minimal handler that just returns a simple response"""
    try:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "message": "Minimal handler works"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e), "type": type(e).__name__})
        }

