// hubspot.js

import { useState, useEffect } from 'react'
import { Box, Button, CircularProgress } from '@mui/material'
import axios from 'axios'

export const HubSpotIntegration = ({
  user,
  org,
  integrationParams,
  setIntegrationParams
}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)

  const handleConnectClick = async () => {
    try {
      setIsConnecting(true)

      const formData = new FormData()
      formData.append('user_id', user)
      formData.append('org_id', org)

      const res = await axios.post(
        'http://localhost:8000/integrations/hubspot/authorize',
        formData
      )

      const authURL = res.data
      const popup = window.open(authURL, 'HubSpot Auth', 'width=600,height=600')

      const timer = setInterval(() => {
        if (popup?.closed) {
          clearInterval(timer)
          handleWindowClosed()
        }
      }, 300)
    } catch (e) {
      setIsConnecting(false)
      alert(e?.response?.data?.detail || e.message)
    }
  }

  const handleWindowClosed = async () => {
    try {
      const formData = new FormData()
      formData.append('user_id', user)
      formData.append('org_id', org)

      const res = await axios.post(
        'http://localhost:8000/integrations/hubspot/credentials',
        formData
      )

      /**
       * 🔑 IMPORTANT
       * Store ONLY access_token as credentials
       */
      const accessToken = res.data?.access_token
      if (!accessToken) {
        throw new Error('Invalid HubSpot credentials')
      }

      setIntegrationParams(prev => ({
        ...prev,
        type: 'HubSpot',
        credentials: accessToken
      }))

      setIsConnected(true)
      setIsConnecting(false)
    } catch (e) {
      setIsConnecting(false)
      alert(e?.response?.data?.detail || e.message)
    }
  }

  /**
   * ✅ Correct dependency
   * React + runtime both fixed
   */
  useEffect(() => {
    setIsConnected(Boolean(integrationParams?.credentials))
  }, [integrationParams?.credentials])

  return (
    <Box sx={{ mt: 2 }}>
      Parameters
      <Box display="flex" justifyContent="center" sx={{ mt: 2 }}>
        <Button
          variant="contained"
          color={isConnected ? 'success' : 'primary'}
          disabled={isConnecting || isConnected}
          onClick={handleConnectClick}
        >
          {isConnected
            ? 'HubSpot Connected'
            : isConnecting
            ? <CircularProgress size={20} />
            : 'Connect to HubSpot'}
        </Button>
      </Box>
    </Box>
  )
}
