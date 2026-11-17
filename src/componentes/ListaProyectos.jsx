import { useMemo, useState } from 'react'
import { useIdioma } from '../i18n/index.js'
import {
  escribirFiltros,
  estadosPresentes,
  etiquetasPorCategoria,
  filtrarProyectos,
  leerFiltros,
} from '../lib/filtros.js'
import Filtros from './Filtros.jsx'
import Seccion from './Seccion.jsx'
import TarjetaProyecto from './TarjetaProyecto.jsx'

// Descarta claves de la URL que no existen en los datos (links viejos o mal escritos).
function filtrosValidos(filtros, estados, grupos) {
  const clavesExistentes = new Set()
  for (const grupo of grupos) {
    for (const etiqueta of grupo.etiquetas) {
      clavesExistentes.add(etiqueta.clave)
    }
  }
  const resultado = { estados: [], etiquetas: [] }
  for (const estado of filtros.estados) {
    if (estados.includes(estado)) {
      resultado.estados.push(estado)
    }
  }
  for (const clave of filtros.etiquetas) {
    if (clavesExistentes.has(clave)) {
      resultado.etiquetas.push(clave)
    }
  }
  return resultado
}

export default function ListaProyectos({ proyectos }) {
  const { t } = useIdioma()
  const estados = useMemo(() => estadosPresentes(proyectos), [proyectos])
  const grupos = useMemo(() => etiquetasPorCategoria(proyectos), [proyectos])
  const [filtros, setFiltros] = useState(() => filtrosValidos(leerFiltros(window.location.search), estados, grupos))
  const visibles = filtrarProyectos(proyectos, filtros)

  function cambiarFiltros(nuevos) {
    setFiltros(nuevos)
    escribirFiltros(nuevos)
  }

  return (
    <Seccion clave="proyectos">
      <Filtros
        estados={estados}
        grupos={grupos}
        filtros={filtros}
        cambiarFiltros={cambiarFiltros}
        cantidad={visibles.length}
      />
      {visibles.length === 0 ? (
        <p className="marco m-0 p-4 text-tinta-suave">{t('filtros.sin_resultados')}</p>
      ) : (
        <div className="grilla-proyectos grid grid-cols-1 gap-5 md:grid-cols-2">
          {visibles.map((proyecto) => (
            <TarjetaProyecto key={proyecto.clave} proyecto={proyecto} />
          ))}
        </div>
      )}
    </Seccion>
  )
}
