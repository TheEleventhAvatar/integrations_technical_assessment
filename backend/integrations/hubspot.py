import secrets
import json
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse

# Replace these with your actual HubSpot App credentials
CLIENT_ID = 'YOUR_HUBSPOT_CLIENT_ID'
CLIENT_SECRET = 'YOUR_HUBSPOT_CLIENT_SECRET'
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'

async def authorize_hubspot(user_id, org_id):
    # State is used to pass user/org context through the OAuth flow
    state_data = {
        'user_id': user_id,
        'org_id': org_id,
    }
    encoded_state = json.dumps(state_data)
    
    # HubSpot Auth URL
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=crm.objects.contacts.read%20crm.objects.deals.read&"
        f"state={encoded_state}"
    )
    return auth_url

async def oauth2callback_hubspot(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    # Exchange code for access token
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
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    
    token_data = response.json()
    # TODO: Store token_data in Redis using the user/org info from 'state'
    
    # Close the popup window after successful auth
    return HTMLResponse("<html><script>window.close()</script></html>")