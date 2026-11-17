import { useIdioma } from '../i18n/index.js'
import { elegirTexto } from '../lib/textos.js'

// Chip "ES" para contenido que en /en/ solo está en español.
export default function MarcaSoloEspanol() {
  const { t } = useIdioma()
  const titulo = t('solo_espanol.titulo')
  return (
    <span
      className="ml-1.5 inline-block border border-linea px-1 align-middle font-mono text-[0.6875rem] leading-4 text-tinta-suave"
      title={titulo}
    >
      <span aria-hidden="true">{t('solo_espanol.chip')}</span>
      <span className="sr-only">({titulo})</span>
    </span>
  )
}

// Texto traducible con lang="es" y la marca cuando cae al español.
export function TextoIdioma({ valor, como = 'span', className = '' }) {
  const { idioma } = useIdioma()
  const { texto, esFallback } = elegirTexto(valor, idioma)
  const Etiqueta = como
  if (!esFallback) {
    return <Etiqueta className={className}>{texto}</Etiqueta>
  }
  return (
    <Etiqueta className={className}>
      <span lang="es">{texto}</span>
      <MarcaSoloEspanol />
    </Etiqueta>
  )
}
