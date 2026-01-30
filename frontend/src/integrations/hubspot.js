// hubspot.js

import { useState, useEffect } from 'react'
import { Box, Button, CircularProgress, List, ListItem, ListItemText, Typography } from '@mui/material'
import axios from 'axios'

export const HubSpotIntegration = ({
  user,
  org,
  integrationParams,
  setIntegrationParams
}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [items, setItems] = useState([]) // demo items

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

      const authURL = res.data.auth_url
      if (!authURL) throw new Error('No auth URL returned')

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

      // 🔑 Store only access_token for demo
      const accessToken = res.data?.access_token
      if (!accessToken) throw new Error('Invalid HubSpot credentials')

      setIntegrationParams(prev => ({
        ...prev,
        type: 'HubSpot',
        credentials: accessToken
      }))

      setIsConnected(true)
      setIsConnecting(false)

      // ✅ Fetch demo items after OAuth
      fetchDemoItems()

    } catch (e) {
      setIsConnecting(false)
      alert(e?.response?.data?.detail || e.message)
    }
  }

  const fetchDemoItems = async () => {
    try {
      const res = await axios.get(
        `http://localhost:8000/integrations/hubspot/items?user_id=${encodeURIComponent(user)}&org_id=${encodeURIComponent(org)}`
      )

      setItems(res.data || [])
    } catch (e) {
      console.error('Failed to fetch HubSpot items', e)
    }
  }

  useEffect(() => {
    setIsConnected(Boolean(integrationParams?.credentials))
    if (integrationParams?.credentials) {
      fetchDemoItems()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [integrationParams?.credentials])

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle1">HubSpot Integration</Typography>
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

      {items.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6">HubSpot Items (Demo)</Typography>
          <List>
            {items.map((item, idx) => (
              <ListItem key={idx} divider>
                <ListItemText
                  primary={item.name}
                  secondary={Object.entries(item.parameters)
                    .map(([key, val]) => `${key}: ${val}`)
                    .join(', ')}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  )
}
