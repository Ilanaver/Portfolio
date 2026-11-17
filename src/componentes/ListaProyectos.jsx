import { useMemo, useState } from 'react'
import { useIdioma } from '../i18n/index.js'
import {
  escribirFiltros,
  estadosPresentes,
  etiquetasPorCategoria,
  filtrarProyectos,
  leerFiltros,
} from '../lib/filtros.js'
import { nombreDe } from '../lib/textos.js'
import { urlVisible } from '../lib/url.js'
import Filtros from './Filtros.jsx'
import Seccion from './Seccion.jsx'
import TarjetaProyecto, { periodoDeProyecto } from './TarjetaProyecto.jsx'
import { TextoIdioma } from './MarcaSoloEspanol.jsx'

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

// Versión del CV impreso: todos los proyectos (sin filtros); destacados con descripción y tecnologías,
// el resto en una línea.
function ProyectosCV({ proyectos }) {
  const { idioma, t } = useIdioma()
  const destacados = []
  const otros = []
  for (const proyecto of proyectos) {
    if (proyecto.destacado) {
      destacados.push(proyecto)
    } else {
      otros.push(proyecto)
    }
  }
  return (
    <div className="cv-proyectos solo-impresion">
      {destacados.length > 0 ? <h3>{t('impresion.proyectos_destacados')}</h3> : null}
      {destacados.map((proyecto) => {
        const etiquetas = []
        for (const etiqueta of proyecto.tecnologias) {
          etiquetas.push(etiqueta.nombre)
        }
        for (const etiqueta of proyecto.servicios) {
          etiquetas.push(etiqueta.nombre)
        }
        return (
          <div key={proyecto.clave} className="cv-proyecto">
            <p>
              <span className="cv-proyecto__nombre">{nombreDe(proyecto, idioma)}</span>
              {' · '}
              <span className="cv-proyecto__meta">
                {t('estados.' + proyecto.estado)} · {periodoDeProyecto(proyecto, idioma, t)}
              </span>
            </p>
            <TextoIdioma valor={proyecto.descripcion} como="p" />
            <p className="cv-proyecto__meta">{etiquetas.join(', ')}</p>
            {proyecto.links.demo ? <p className="cv-proyecto__meta">{urlVisible(proyecto.links.demo)}</p> : null}
          </div>
        )
      })}
      {otros.length > 0 ? <h3>{t('impresion.otros_proyectos')}</h3> : null}
      <ul className="cv-otros m-0 p-0">
        {otros.map((proyecto) => (
          <li key={proyecto.clave}>
            <span className="cv-proyecto__nombre">{nombreDe(proyecto, idioma)}</span>
            {' — '}
            <TextoIdioma valor={proyecto.descripcion} />
          </li>
        ))}
      </ul>
    </div>
  )
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
      <ProyectosCV proyectos={proyectos} />
    </Seccion>
  )
}
