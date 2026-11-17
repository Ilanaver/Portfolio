import { IDIOMAS, guardarIdioma, useIdioma } from '../i18n/index.js'
import { rutaEnIdioma, urlEnIdioma } from '../lib/url.js'

// Selector ES | EN: va a la misma página en el otro idioma, con ?filtros y #ancla.
export default function SelectorIdioma() {
  const { idioma, t } = useIdioma()

  function cambiar(evento, destino) {
    guardarIdioma(destino)
    if (destino === idioma) {
      evento.preventDefault()
      return
    }
    evento.preventDefault()
    window.location.assign(urlEnIdioma(window.location, destino))
  }

  return (
    <nav aria-label={t('idioma.selector')} className="selector-idioma flex border border-linea font-mono text-sm">
      {IDIOMAS.map((opcion) => {
        const actual = opcion === idioma
        const clases = actual
          ? 'bg-acento text-acento-tinta'
          : 'text-tinta hover:bg-acento-suave'
        return (
          <a
            key={opcion}
            href={rutaEnIdioma(window.location.pathname, opcion)}
            hrefLang={opcion}
            lang={opcion}
            aria-current={actual ? 'page' : undefined}
            onClick={(evento) => cambiar(evento, opcion)}
            className={'flex min-h-tactil min-w-tactil items-center justify-center px-3 no-underline ' + clases}
          >
            {t('idioma.' + opcion + '_corto')}
            <span className="sr-only"> ({t('idioma.' + opcion + '_nombre')})</span>
          </a>
        )
      })}
    </nav>
  )
}
