import { AppProvider, useApp } from './context/AppContext'
import LandingScreen from './screens/LandingScreen'
import DestinationScreen from './screens/DestinationScreen'
import ProfileQuestionsScreen from './screens/ProfileQuestionsScreen'
import EligibilityScreen from './screens/EligibilityScreen'
import PriceScreen from './screens/PriceScreen'
import ChecklistScreen from './screens/ChecklistScreen'
import StatusTimelineScreen from './screens/StatusTimelineScreen'
import ResultScreen from './screens/ResultScreen'

function Router() {
  const { screen } = useApp()

  switch (screen) {
    case 'landing':            return <LandingScreen />
    case 'destination':        return <DestinationScreen />
    case 'profile-questions':  return <ProfileQuestionsScreen />
    case 'eligibility-loading': return <EligibilityScreen />
    case 'price':              return <PriceScreen />
    case 'checklist':          return <ChecklistScreen />
    case 'status-timeline':    return <StatusTimelineScreen />
    case 'result':             return <ResultScreen />
    default:                   return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        Màn hình &ldquo;{screen}&rdquo; chưa được xây dựng
      </div>
    )
  }
}

export default function App() {
  return (
    <AppProvider>
      <Router />
    </AppProvider>
  )
}
