import { createContext, useContext, useState, useEffect } from 'react'

const AppContext = createContext(null)

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export function AppProvider({ children }) {
  const [applicationId, setApplicationId] = useState(() => localStorage.getItem('visa_application_id'))
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('visa_session_id'))
  const [destination, setDestination] = useState(null)
  const [profile, setProfile] = useState({})
  const [eligibilityResult, setEligibilityResult] = useState(null)
  const [resultStatus, setResultStatus] = useState(null)
  const [checklist, setChecklist] = useState([])
  const [itineraryJson, setItineraryJson] = useState(null)
  const [extractedInfo, setExtractedInfo] = useState({})
  const [tripFormData, setTripFormData] = useState({})
  const [screen, setScreen] = useState('landing')
  const [formInfoSaved, setFormInfoSaved] = useState(false)

  async function startApplication() {
    const res = await fetch(`${API_BASE}/api/application/start`, { method: 'POST' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    setApplicationId(data.application_id)
    setSessionId(data.session_id)
    localStorage.setItem('visa_session_id', data.session_id)
    localStorage.setItem('visa_application_id', data.application_id)
    return data
  }

  async function updateDestination(appId, dest) {
    const res = await fetch(`${API_BASE}/api/application/${appId}/destination`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: dest }),
    })
    if (!res.ok) throw new Error('Failed to save destination')
    setDestination(dest)
  }

  function navigate(to) {
    setScreen(to)
  }

  return (
    <AppContext.Provider value={{
      applicationId, sessionId, destination, setDestination,
      profile, setProfile,
      eligibilityResult, setEligibilityResult,
      resultStatus, setResultStatus,
      checklist, setChecklist,
      itineraryJson, setItineraryJson,
      extractedInfo, setExtractedInfo,
      tripFormData, setTripFormData,
      formInfoSaved, setFormInfoSaved,
      screen, navigate, startApplication,
      updateDestination, API_BASE,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  return useContext(AppContext)
}
