import secrets
import json
import logging
from typing import Any, Dict, List
from urllib.parse import urlencode, unquote

import httpx
from fastapi import Request, HTTPException
from starlette.responses import HTMLResponse

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from integrations.integration_item import IntegrationItem

# =====================
# HubSpot App Config
# =====================
CLIENT_ID = "3405d3b3-699e-4565-9c93-436a190d88d7"
CLIENT_SECRET = "ad939ff8-a69d-4400-9ed9-ac10e693d05b"
REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"

SCOPES = [
    "crm.objects.contacts.read",
    "crm.objects.deals.read",
]

logger = logging.getLogger("integrations.hubspot")
logging.basicConfig(level=logging.INFO)


# =====================
# Authorize URL
# =====================
async def authorize_hubspot(user_id: str, org_id: str) -> str:
    # Use a short opaque token as the `state` query parameter and store the
    # full payload server-side. This avoids JSON/quoting issues during the
    # redirect round-trip which can cause `Invalid state payload` errors.
    state_token = secrets.token_urlsafe(32)
    state_payload = {
        "csrf": secrets.token_urlsafe(24),
        "user_id": user_id,
        "org_id": org_id,
    }

    # Persist the payload keyed by the token (one-time use)
    await add_key_value_redis(f"hubspot_state_token:{state_token}", json.dumps(state_payload), expire=600)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state_token,
    }

    auth_url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"
    return auth_url


# =====================
# OAuth Callback
# =====================
async def oauth2callback_hubspot(request: Request) -> HTMLResponse:
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Expect a short token in the `state` parameter. Look up the full payload
    # from Redis. Log the raw values to aid debugging if something goes wrong.
    try:
        state_token = unquote(state)
        logger.debug('oauth callback raw state=%s', state)
        stored = await get_value_redis(f"hubspot_state_token:{state_token}")
        if not stored:
            logger.warning('No stored state for token %s', state_token)
            raise HTTPException(status_code=400, detail="State mismatch or expired")
        state_data = json.loads(stored)
        user_id = state_data["user_id"]
        org_id = state_data["org_id"]
    except HTTPException:
        raise
    except Exception:
        logger.exception('Failed to parse or retrieve state payload')
        raise HTTPException(status_code=400, detail="Invalid state payload")

    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
        )

    if token_resp.status_code != 200:
        logger.error(token_resp.text)
        raise HTTPException(status_code=400, detail="Token exchange failed")

    token_data = token_resp.json()

    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(token_data),
        expire=3600,
    )
    await delete_key_redis(f"hubspot_state:{org_id}:{user_id}")

    return HTMLResponse(
        """
        <html>
          <body>
            <script>window.close();</script>
            <p>HubSpot connected. You may close this window.</p>
          </body>
        </html>
        """
    )


# =====================
# Get Credentials
# =====================
async def get_hubspot_credentials(user_id: str, org_id: str) -> Dict[str, Any]:
    key = f"hubspot_credentials:{org_id}:{user_id}"
    raw = await get_value_redis(key)

    if not raw:
        raise HTTPException(status_code=400, detail="No credentials found")

    await delete_key_redis(key)
    return json.loads(raw)


# =====================
# Fetch HubSpot Contacts
# =====================
async def get_items_hubspot(credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
    # credentials may be passed as a JSON string (from a form), as a raw
    # token string (frontend may store just the token), or as a dict.
    if isinstance(credentials, str):
        try:
            # JSON-encoded value could be a dict or a raw string (e.g. '"tok"')
            parsed = json.loads(credentials)
        except Exception:
            parsed = credentials
        credentials = parsed

    if isinstance(credentials, dict):
        access_token = credentials.get("access_token")
    else:
        # treat the value itself as the access token (covers raw token strings)
        access_token = credentials
    if not access_token:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    items: List[IntegrationItem] = []

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers,
            params={"limit": 100},
        )
        resp.raise_for_status()

        for r in resp.json().get("results", []):
            props = r.get("properties", {})
            name = (
                f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                or props.get("email")
                or r["id"]
            )

            item = IntegrationItem(
                id=r["id"],
                type="Contact",
                name=name,
                parent_id=None,
                parent_path_or_name=None,
                url=None,
            )

            setattr(item, "email", props.get("email"))
            setattr(item, "phone", props.get("phone"))
            setattr(item, "company", props.get("company"))

            items.append(item)

    return [
        {
            "id": i.id,
            "type": i.type,
            "name": i.name,
            "email": getattr(i, "email", None),
            "phone": getattr(i, "phone", None),
            "company": getattr(i, "company", None),
            "parent_id": i.parent_id,
            "parent_path_or_name": i.parent_path_or_name,
            "url": i.url,
        }
        for i in items
    ]
