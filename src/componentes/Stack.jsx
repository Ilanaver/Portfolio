import { useMemo } from 'react'
import { useIdioma } from '../i18n/index.js'
import { etiquetasPorCategoria } from '../lib/filtros.js'
import { anclaDe } from '../lib/url.js'
import Seccion from './Seccion.jsx'

// Stack calculado desde los datos: por categoría, con la cantidad de proyectos de cada etiqueta.
// Cada etiqueta lleva a la lista de proyectos filtrada por ella.
export default function Stack({ proyectos }) {
  const { idioma, t } = useIdioma()
  const grupos = useMemo(() => etiquetasPorCategoria(proyectos), [proyectos])
  const anclaProyectos = anclaDe('proyectos', idioma)
  return (
    <Seccion clave="stack">
      <p className="m-0 mb-5 max-w-prose text-tinta-suave">{t('stack.intro')}</p>
      <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
        {grupos.map((grupo) => (
          <div key={grupo.categoria} className="grupo-stack">
            <h3 className="rotulo m-0 mb-2 font-normal">{t('categorias.' + grupo.categoria)}</h3>
            <ul className="m-0 flex flex-wrap gap-1.5 p-0">
              {grupo.etiquetas.map((etiqueta) => (
                <li key={etiqueta.clave} className="list-none">
                  <a
                    href={'?tag=' + etiqueta.clave + '#' + anclaProyectos}
                    className="etiqueta-stack inline-flex min-h-tactil items-center gap-2 border border-linea bg-superficie px-3 font-mono text-sm text-tinta no-underline hover:border-acento"
                  >
                    {etiqueta.nombre}
                    <span className="text-xs text-acento" aria-hidden="true">
                      {etiqueta.cantidad}
                    </span>
                    <span className="sr-only">({t('stack.cantidad', { cantidad: etiqueta.cantidad })})</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Seccion>
  )
}
