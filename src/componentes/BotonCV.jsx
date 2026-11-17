import { useIdioma } from '../i18n/index.js'

const CLASES =
  'boton-cv inline-flex min-h-tactil items-center gap-2 border border-acento bg-acento px-4 font-medium text-acento-tinta no-underline hover:opacity-90'

// Fase 1: imprime con la hoja de CV. Desde la Fase 2, si hay PDF, lo descarga.
export default function BotonCV({ perfil }) {
  const { idioma, t } = useIdioma()
  const pdf = perfil.cv_pdf ? perfil.cv_pdf[idioma] : null

  if (pdf) {
    return (
      <a href={pdf} download className={CLASES} title={t('cv.descargar_titulo_pdf')}>
        {t('cv.descargar')}
      </a>
    )
  }
  return (
    <button type="button" onClick={() => window.print()} className={CLASES} title={t('cv.descargar_titulo_imprimir')}>
      {t('cv.descargar')}
    </button>
  )
}
