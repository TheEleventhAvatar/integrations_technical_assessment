# ---------------- HubSpot ----------------

from fastapi import FastAPI, Form, Request
import logging
from fastapi.middleware.cors import CORSMiddleware
from integrations.hubspot import authorize_hubspot, oauth2callback_hubspot, get_hubspot_credentials, get_items_hubspot

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HubSpot Routes ----------------

@app.post("/integrations/hubspot/authorize")
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Returns the HubSpot OAuth URL
    """
    # return a JSON object with auth_url to match the frontend expectation
    auth_url = await authorize_hubspot(user_id, org_id)
    return {"auth_url": auth_url}

@app.get("/integrations/hubspot/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request):
    return await oauth2callback_hubspot(request)

@app.post("/integrations/hubspot/credentials")
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_hubspot_credentials(user_id, org_id)

@app.post("/integrations/hubspot/load")
async def get_hubspot_items_compat(request: Request, credentials: str = Form(...)):
    logger = logging.getLogger('integrations.hubspot.main')
    try:
        origin = request.headers.get('origin')
        logger.info('Incoming /integrations/hubspot/load request origin=%s', origin)
        logger.debug('Form keys: %s', list((await request.form()).keys()))
        # Call the underlying loader and return JSON; ensure exceptions become JSON errors
        items = await get_items_hubspot(credentials)
        return items
    except Exception as exc:
        import traceback

        logger.exception('Error handling hubspot load')
        # If str(exc) is empty, provide repr and a short traceback to aid debugging
        error_text = str(exc) or repr(exc)
        tb = traceback.format_exc()
        # Return structured info (development-only helper)
        return {
            'error': error_text,
            'type': type(exc).__name__,
            'traceback': tb,
        }
    """
    Real credential-based fetching (future use)
    """
    return await get_items_hubspot(credentials)

# Optional: demo endpoint if you want hardcoded items
@app.get("/integrations/hubspot/items")
async def get_demo_hubspot_items(user_id: str, org_id: str):
    items = await get_items_hubspot(credentials=None)
    return [{"name": item.name, "parameters": item.parameters} for item in items]
