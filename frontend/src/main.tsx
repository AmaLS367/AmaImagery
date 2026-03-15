import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'
import { SettingsProvider } from './providers/SettingsProvider'
import { JobProvider } from './providers/JobProvider'
import { AuthProvider } from './providers/AuthProvider'
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SettingsProvider>
      <AuthProvider>
        <JobProvider>
          <App />
        </JobProvider>
      </AuthProvider>
    </SettingsProvider>
  </React.StrictMode>
)
