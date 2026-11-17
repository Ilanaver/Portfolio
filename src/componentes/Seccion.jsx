import { useIdioma } from '../i18n/index.js'
import { anclaDe } from '../lib/url.js'

// Sección del inicio con su ancla por idioma y título rotulado.
export default function Seccion({ clave, children, className = '' }) {
  const { idioma, t } = useIdioma()
  const id = anclaDe(clave, idioma)
  return (
    <section id={id} aria-labelledby={id + '-titulo'} className={'seccion seccion--' + clave + ' py-10 ' + className}>
      <h2 id={id + '-titulo'} className="mb-5 mt-0 flex items-baseline gap-3 text-2xl font-semibold leading-tight">
        <span aria-hidden="true" className="font-mono text-sm font-normal text-acento">
          §
        </span>
        {t('secciones.' + clave)}
      </h2>
      {children}
    </section>
  )
}
