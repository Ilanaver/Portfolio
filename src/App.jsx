import { useMemo } from 'react'
import { Analytics } from '@vercel/analytics/react'
import { IdiomaContexto, crearTraductor } from './i18n/index.js'
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

// La vista sale de data-vista / data-slug del <html> (cada ruta es un HTML estático).
export default function App({ idioma, vista, slug }) {
  const contexto = useMemo(() => ({ idioma, t: crearTraductor(idioma) }), [idioma])
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
