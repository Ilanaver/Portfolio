// Entrada del pre-renderizado (se compila con `vite build --ssr` y la usa scripts/paginas_proyecto.mjs).
// Genera el HTML de cada página para que llegue armado; en el navegador, main.jsx lo hidrata.
import { StrictMode } from 'react'
import { renderToString } from 'react-dom/server'
import App from './App.jsx'

export function renderizar(idioma, vista, slug) {
  return renderToString(
    <StrictMode>
      <App idioma={idioma} vista={vista} slug={slug} />
    </StrictMode>,
  )
}
