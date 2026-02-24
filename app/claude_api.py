"""Claude.ai API client for usage data."""
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://claude.ai",
    "Referer": "https://claude.ai/",
}

def _request(url, session_key):
    headers = {**HEADERS_BASE, "Cookie": f"sessionKey={session_key}"}
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def get_account_usage(session_key):
    """Fetch usage data for a single Claude account.
    
    Returns dict with email, plan, session/weekly/opus/sonnet usage, or None on error.
    """
    try:
        # Get org
        orgs = _request("https://claude.ai/api/organizations", session_key)
        if not orgs:
            return {"error": "No organization found"}
        org_id = orgs[0]["uuid"]
        org_name = orgs[0].get("name", "")
        
        # Get account
        account = _request("https://claude.ai/api/account", session_key)
        email = account.get("email_address", "unknown")
        
        # Get usage
        usage = _request(f"https://claude.ai/api/organizations/{org_id}/usage", session_key)
        
        five_hour = usage.get("five_hour", {})
        seven_day = usage.get("seven_day", {})
        opus = usage.get("seven_day_opus")
        sonnet = usage.get("seven_day_sonnet")
        
        return {
            "email": email,
            "org_name": org_name,
            "session": {
                "used": five_hour.get("utilization", 0),
                "remaining": 100 - five_hour.get("utilization", 0),
                "resets_at": five_hour.get("resets_at"),
            },
            "weekly": {
                "used": seven_day.get("utilization", 0),
                "remaining": 100 - seven_day.get("utilization", 0),
                "resets_at": seven_day.get("resets_at"),
            },
            "opus": {
                "used": opus.get("utilization", 0) if opus else None,
                "remaining": (100 - opus["utilization"]) if opus and opus.get("utilization") is not None else None,
                "resets_at": opus.get("resets_at") if opus else None,
            } if opus else None,
            "sonnet": {
                "used": sonnet.get("utilization", 0) if sonnet else None,
                "remaining": (100 - sonnet["utilization"]) if sonnet and sonnet.get("utilization") is not None else None,
                "resets_at": sonnet.get("resets_at") if sonnet else None,
            } if sonnet else None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code} (session may be expired)", "email": "unknown"}
    except Exception as e:
        return {"error": str(e), "email": "unknown"}

def fetch_all_usage(profiles):
    """Fetch usage for all profiles with rate limiting.
    
    Args:
        profiles: list from chrome.scan_all_profiles()
    
    Returns list of dicts with profile info + usage data.
    """
    results = []
    for i, p in enumerate(profiles):
        if i > 0:
            time.sleep(1)  # Rate limit
        
        usage = get_account_usage(p["session_key"])
        results.append({
            "profile": p["profile"],
            "profile_name": p["profile_name"],
            **usage,
        })
    return results
