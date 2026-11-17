import { useMemo } from 'react'
import { Analytics } from '@vercel/analytics/react'
import { IdiomaContexto, crearTraductor } from './i18n/index.js'
import { rutaInicio, rutaProyecto } from './lib/url.js'
import perfil from './datos/perfil.json'
import datosProyectos from './datos/proyectos.json'
import Inicio from './vistas/Inicio.jsx'
import PaginaProyecto from './vistas/PaginaProyecto.jsx'

function buscarProyecto(slug) {
  for (const proyecto of datosProyectos.proyectos) {
    if (proyecto.slug === slug) {
      return proyecto
    }
  }
  return null
}

// Ruta de esta misma página en cada idioma (para el selector).
function rutasDeLaPagina(vista, slug) {
  if (vista === 'proyecto' && slug) {
    return { es: rutaProyecto('es', slug), en: rutaProyecto('en', slug) }
  }
  return { es: rutaInicio('es'), en: rutaInicio('en') }
}

// La vista sale de data-vista / data-slug del <html> (cada ruta es un HTML estático).
// Se usa igual en el navegador (main.jsx) y en el pre-renderizado del build (entrada-servidor.jsx).
export default function App({ idioma, vista, slug }) {
  const contexto = useMemo(
    () => ({ idioma, t: crearTraductor(idioma), rutas: rutasDeLaPagina(vista, slug) }),
    [idioma, vista, slug],
  )
  return (
    <IdiomaContexto.Provider value={contexto}>
      {vista === 'proyecto' ? (
        <PaginaProyecto perfil={perfil} proyecto={buscarProyecto(slug)} />
      ) : (
        <Inicio perfil={perfil} proyectos={datosProyectos.proyectos} />
      )}
      <Analytics />
    </IdiomaContexto.Provider>
  )
}
