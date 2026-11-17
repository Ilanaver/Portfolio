import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './impresion.css'
import App from './App.jsx'

const raizHtml = document.documentElement
const idioma = raizHtml.dataset.idioma === 'en' ? 'en' : 'es'
const vista = raizHtml.dataset.vista === 'proyecto' ? 'proyecto' : 'inicio'
const slug = raizHtml.dataset.slug || null

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App idioma={idioma} vista={vista} slug={slug} />
  </StrictMode>,
)
