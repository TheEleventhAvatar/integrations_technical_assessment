# Integrations Technical Assessment — Local Run & HubSpot Setup

This repository contains a small React frontend and a FastAPI backend that demonstrate integration to HubSpot

This README documents how to run the project locally and how to test the HubSpot OAuth flow and data load.

## Prerequisites
- Python 3.11 (the project uses a venv created with python3.11)
- Node.js (tested with Node 22.x) and npm
- Redis server (or use the ephemeral Redis the instructions show)

## Backend — prepare and run
1. Create a Python 3.11 venv and install dependencies:

```bash
cd backend
python3.11 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

2. Configure HubSpot credentials

- By default the backend stores CLIENT_ID and CLIENT_SECRET in `backend/integrations/hubspot.py` as
  constants. If you've already added your HubSpot `CLIENT_ID`, `CLIENT_SECRET`, and ensured the
  Redirect URI in your HubSpot app is set to:

```
http://localhost:8000/integrations/hubspot/oauth2callback
```

then the backend is already configured.

Optional: You can instead modify the code to read credentials from environment variables (recommended for production).

3. Start Redis (example, persistent):

```bash
redis-server
```

Or start an ephemeral Redis on a different port (non-persistent):

```bash
redis-server --port 6380 --save "" --appendonly no --daemonize yes
# then point the app at it:
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6380
```

4. Start the backend (from `backend/`):

```bash
. .venv/bin/activate
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend exposes these relevant endpoints:
- POST /integrations/hubspot/authorize  — returns an authorization URL
- GET /integrations/hubspot/oauth2callback — HubSpot will redirect here after authorization
- POST /integrations/hubspot/credentials — used by the frontend to fetch the stored credentials after the popup closes
- POST /integrations/hubspot/get_hubspot_items — accepts `credentials` form field (JSON string) and returns a list of integration items (contacts by default)

## Frontend — prepare and run
1. Install dependencies and start the dev server:

```bash
cd frontend
npm install
npm start
```

2. Open http://localhost:3000/ in your browser. In the Integration Type dropdown choose "HubSpot" and click **Connect to HubSpot**.

3. The frontend opens a popup with the HubSpot consent page. Complete the consent. When the popup closes the frontend will POST to `/integrations/hubspot/credentials` to fetch the credentials stored temporarily in Redis.

4. After credentials are retrieved the UI will show a **Load Data** button (in the Parameters area). Click that to POST the credentials to the backend and fetch HubSpot items (contacts). The results will display in the "Loaded Data" field (the UI currently prints the response).

## Manual test with curl
If you prefer to test the final fetch with curl after the OAuth flow completed and credentials are stored in Redis, do:

1. After the popup closed, the frontend calls `/integrations/hubspot/credentials` which returns the stored token JSON. If you have that JSON (or the frontend shows it), you can call:

```bash
curl -X POST -F "credentials=$(cat token.json)" http://127.0.0.1:8000/integrations/hubspot/get_hubspot_items
```

This returns a JSON array of `IntegrationItem` objects (contacts by default).

## Notes & Next steps

- For production, move client secrets to environment variables and protect Redis.
- If you'd like, I can push these changes to the remote repo or add instructions into a CONTRIBUTING.md / developer script to automate venv creation.

If you want me to push the commits to origin, run a simulated OAuth flow, or extend item fetching to additional HubSpot object types, say which and I'll continue.
