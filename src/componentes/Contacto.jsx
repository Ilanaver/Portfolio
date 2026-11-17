import { useIdioma } from '../i18n/index.js'
import { urlVisible } from '../lib/url.js'
import Seccion from './Seccion.jsx'

export default function Contacto({ perfil }) {
  const { t } = useIdioma()
  return (
    <Seccion clave="contacto">
      <p className="m-0">{t('contacto.texto')}</p>
      <p className="m-0 mt-1 text-xl">
        <a href={'mailto:' + perfil.contacto.email} className="inline-flex min-h-tactil items-center font-mono">
          {perfil.contacto.email}
        </a>
      </p>
      <p className="m-0">
        <a href={perfil.contacto.github} className="inline-flex min-h-tactil items-center font-mono text-sm">
          {urlVisible(perfil.contacto.github)}
        </a>
      </p>
    </Seccion>
  )
}
