import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const raizHtml = document.documentElement
const idioma = raizHtml.dataset.idioma === 'en' ? 'en' : 'es'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App idioma={idioma} />
  </StrictMode>,
)
