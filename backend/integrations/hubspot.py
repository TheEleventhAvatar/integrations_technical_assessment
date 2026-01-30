import secrets
import json
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Replace these with your actual HubSpot App credentials
CLIENT_ID = 'YOUR_HUBSPOT_CLIENT_ID'
CLIENT_SECRET = 'YOUR_HUBSPOT_CLIENT_SECRET'
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'


async def authorize_hubspot(user_id, org_id):
    """Generate a HubSpot OAuth authorize URL and save state in Redis."""
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id,
    }
    encoded_state = json.dumps(state_data)

    auth_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=crm.objects.contacts.read%20crm.objects.deals.read&"
        f"state={encoded_state}"
    )

    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    return auth_url


async def oauth2callback_hubspot(request: Request):
    """Handle the OAuth callback from HubSpot, exchange code for token and store it."""
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')

    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    token_data = response.json()

    try:
        state_data = json.loads(encoded_state)
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')
        if user_id and org_id:
            await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(token_data), expire=600)
            await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
    except Exception:
        # ignore malformed state
        pass

    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)


async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return credentials


async def get_items_hubspot(credentials) -> list:
    """Placeholder: fetch items from HubSpot using provided credentials.
    Returns an empty list for now; implement as needed.
    """
    try:
        if isinstance(credentials, str):
            credentials = json.loads(credentials)
    except Exception:
        credentials = {}

    # TODO: implement actual HubSpot calls using credentials.get('access_token')
    return []