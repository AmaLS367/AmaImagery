import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'
import { SettingsProvider } from './providers/SettingsProvider'
import { JobProvider } from './providers/JobProvider'
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SettingsProvider>
      <JobProvider>
        <App />
      </JobProvider>
    </SettingsProvider>
  </React.StrictMode>
)
