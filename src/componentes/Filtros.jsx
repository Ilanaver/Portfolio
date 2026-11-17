import { useIdioma } from '../i18n/index.js'
import { alternar } from '../lib/filtros.js'

function Chip({ activo, onClick, children }) {
  const clases = activo
    ? 'border-acento bg-acento text-acento-tinta'
    : 'border-linea bg-superficie text-tinta hover:border-acento'
  return (
    <button
      type="button"
      aria-pressed={activo}
      onClick={onClick}
      className={'chip-filtro inline-flex min-h-tactil shrink-0 items-center whitespace-nowrap border px-3 font-mono text-sm ' + clases}
    >
      {children}
    </button>
  )
}

function Grupo({ rotulo, children }) {
  return (
    <div role="group" aria-label={rotulo} className="flex shrink-0 items-center gap-1.5">
      <span className="rotulo shrink-0 pr-1">{rotulo}</span>
      {children}
    </div>
  )
}

// Barra de filtros: estado + etiquetas por categoría (selección múltiple). En celular: barra fija con
// scroll horizontal; en escritorio los chips se acomodan en varias líneas.
export default function Filtros({ estados, grupos, filtros, cambiarFiltros, cantidad }) {
  const { t } = useIdioma()
  const hayFiltros = filtros.estados.length > 0 || filtros.etiquetas.length > 0

  function alternarEstado(estado) {
    cambiarFiltros({ estados: alternar(filtros.estados, estado), etiquetas: filtros.etiquetas })
  }

  function alternarEtiqueta(clave) {
    cambiarFiltros({ estados: filtros.estados, etiquetas: alternar(filtros.etiquetas, clave) })
  }

  return (
    <div
      role="search"
      aria-label={t('filtros.titulo')}
      className="filtros z-20 -mx-4 mb-5 border-y border-linea bg-papel px-4 py-2 max-md:sticky max-md:top-0"
    >
      <div className="scroll-horizontal flex gap-4 pb-1 md:flex-wrap md:gap-y-2 md:overflow-visible">
        <Grupo rotulo={t('filtros.estado')}>
          {estados.map((estado) => (
            <Chip key={estado} activo={filtros.estados.includes(estado)} onClick={() => alternarEstado(estado)}>
              {t('estados.' + estado)}
            </Chip>
          ))}
        </Grupo>
        {grupos.map((grupo) => (
          <Grupo key={grupo.categoria} rotulo={t('categorias.' + grupo.categoria)}>
            {grupo.etiquetas.map((etiqueta) => (
              <Chip
                key={etiqueta.clave}
                activo={filtros.etiquetas.includes(etiqueta.clave)}
                onClick={() => alternarEtiqueta(etiqueta.clave)}
              >
                {etiqueta.nombre}
              </Chip>
            ))}
          </Grupo>
        ))}
      </div>
      <div className="flex min-h-tactil items-center justify-between gap-3">
        <p className="m-0 font-mono text-sm text-tinta-suave" aria-live="polite">
          {t('filtros.resultado', { cantidad })}
        </p>
        {hayFiltros ? (
          <button
            type="button"
            onClick={() => cambiarFiltros({ estados: [], etiquetas: [] })}
            className="inline-flex min-h-tactil items-center px-2 text-sm text-acento underline underline-offset-4"
          >
            {t('filtros.limpiar')}
          </button>
        ) : null}
      </div>
    </div>
  )
}
