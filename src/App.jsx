import { useMemo } from 'react'
import { IdiomaContexto, crearTraductor } from './i18n/index.js'
import perfil from './datos/perfil.json'
import datosProyectos from './datos/proyectos.json'
import Inicio from './vistas/Inicio.jsx'

export default function App({ idioma }) {
  const contexto = useMemo(() => ({ idioma, t: crearTraductor(idioma) }), [idioma])
  return (
    <IdiomaContexto.Provider value={contexto}>
      <Inicio perfil={perfil} proyectos={datosProyectos.proyectos} />
    </IdiomaContexto.Provider>
  )
}
