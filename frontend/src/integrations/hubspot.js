import { Button } from '@mui/material'

export const HubSpotIntegration = ({ user, org, setIntegrationParams }) => {
  const onConnect = async () => {
    try {
      const formData = new FormData()
      formData.append('user_id', user)
      formData.append('org_id', org)

      const res = await fetch(
        'http://localhost:8000/integrations/hubspot/authorize',
        {
          method: 'POST',
          body: formData,
        }
      )

      // ✅ parse JSON correctly
      const data = await res.json()
      const authUrl = data.auth_url
      if (!authUrl) throw new Error('No auth URL returned')

      const popup = window.open(authUrl, 'HubSpot Auth', 'width=600,height=600')

      // poll popup closure
      const timer = setInterval(async () => {
        if (popup?.closed) {
          clearInterval(timer)

          const credForm = new FormData()
          credForm.append('user_id', user)
          credForm.append('org_id', org)

          const credRes = await fetch(
            'http://localhost:8000/integrations/hubspot/credentials',
            { method: 'POST', body: credForm }
          )

          const creds = await credRes.json()
          setIntegrationParams({
            type: 'HubSpot',
            credentials: creds.access_token,
          })
        }
      }, 300)
    } catch (e) {
      console.error(e)
      alert(e.message || 'Failed to connect to HubSpot')
    }
  }

  return <Button variant="contained" onClick={onConnect}>Connect to HubSpot</Button>
}
