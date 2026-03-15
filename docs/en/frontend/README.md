# Frontend Documentation

## Overview

The frontend is a React application built with TypeScript and Vite. The frontend covers generation, history, settings, auth, and informational product pages.

## Key Features

### 🎨 User Interface
- responsive product UI
- Tailwind CSS styling
- light/dark theme support
- accessible UI primitives

### 🌐 Internationalization
- i18next-based multi-language support
- English and Russian
- additional languages planned

### 🔄 State Management
- React Context API
- custom hooks
- route-based page composition

### 📡 API Integration
- auth flows
- generation submission and polling
- history/settings integration
- error handling

## Route Surface

Routes:

- `/`
- `/generate`
- `/history`
- `/settings`
- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/about`
- `/faq`
- `/prompt-guide`
- `/privacy`
- `/404`

Legacy redirects:
- `/gen`
- `/guide`
- `/reset`

## Documentation Sections

| Topic | Status |
|------|--------|
| Architecture page | 🚧 Coming soon |
| Setup page | 🚧 Coming soon |
| Components deep-dive | 🚧 Coming soon |
| Pages deep-dive | 🚧 Coming soon |
| State management deep-dive | 🚧 Coming soon |
| API integration deep-dive | 🚧 Coming soon |
| i18n deep-dive | 🚧 Coming soon |
| Styling guide | 🚧 Coming soon |
| Build & deploy guide | 🚧 Coming soon |
| Frontend testing guide | 🚧 Coming soon |

## Quick Start

```bash
cd frontend
npm ci
npm run dev
```

## Technology Stack

- **Framework:** React 18
- **Language:** TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **i18n:** i18next
- **Routing:** React Router
