import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 3800,
        style: {
          background: 'var(--color-paper-bright)',
          border: '1px solid var(--color-line)',
          borderRadius: '12px',
          boxShadow: '0 8px 24px rgb(16 58 40 / 10%)',
          color: 'var(--color-ink)',
          fontSize: '0.9rem',
          padding: '14px 16px',
        },
        success: {
          iconTheme: {
            primary: 'var(--color-green)',
            secondary: 'var(--color-paper-bright)',
          },
        },
      }}
    />
  </StrictMode>,
)
