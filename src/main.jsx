import { StrictMode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import './index.css'
import './impresion.css'
import App from './App.jsx'

const raizHtml = document.documentElement
const idioma = raizHtml.dataset.idioma === 'en' ? 'en' : 'es'
const vista = raizHtml.dataset.vista === 'proyecto' ? 'proyecto' : 'inicio'
const slug = raizHtml.dataset.slug || null

const contenedor = document.getElementById('root')
const aplicacion = (
  <StrictMode>
    <App idioma={idioma} vista={vista} slug={slug} />
  </StrictMode>
)

// En el build el HTML viene pre-renderizado: se hidrata. En desarrollo el contenedor está vacío: se renderiza.
if (contenedor.firstElementChild) {
  hydrateRoot(contenedor, aplicacion)
} else {
  createRoot(contenedor).render(aplicacion)
}
