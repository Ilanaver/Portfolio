import { useIdioma } from '../i18n/index.js'
import { anclaDe, rutaInicio, urlVisible } from '../lib/url.js'
import BotonCV from './BotonCV.jsx'
import SelectorIdioma from './SelectorIdioma.jsx'
import { TextoIdioma } from './MarcaSoloEspanol.jsx'

const SECCIONES = ['sobre_mi', 'proyectos', 'problemas', 'estudios', 'stack', 'contacto']

function EnlacesContacto({ perfil }) {
  const { idioma, t } = useIdioma()
  const urlPortfolio = __SITIO_URL__ + rutaInicio(idioma)
  const enlaces = [
    { clave: 'correo', url: 'mailto:' + perfil.contacto.email, visible: perfil.contacto.email },
    { clave: 'github', url: perfil.contacto.github, visible: urlVisible(perfil.contacto.github) },
  ]
  if (perfil.contacto.linkedin) {
    enlaces.push({ clave: 'linkedin', url: perfil.contacto.linkedin, visible: urlVisible(perfil.contacto.linkedin) })
  }
  return (
    <ul aria-label={t('encabezado.enlaces')} className="enlaces-contacto flex flex-wrap gap-x-5 gap-y-1 p-0 text-sm">
      {enlaces.map((enlace) => (
        <li key={enlace.clave} className="list-none">
          <a href={enlace.url} className="inline-flex min-h-tactil items-center">
            <span className="solo-pantalla">{t('encabezado.' + enlace.clave)}</span>
            <span className="solo-impresion">{enlace.visible}</span>
          </a>
        </li>
      ))}
      <li className="solo-impresion list-none">
        <a href={urlPortfolio}>{urlVisible(urlPortfolio)}</a>
      </li>
    </ul>
  )
}

function NavegacionSecciones({ secciones }) {
  const { idioma, t } = useIdioma()
  return (
    <nav aria-label={t('encabezado.navegacion')} className="nav-secciones scroll-horizontal -mx-4 px-4">
      <ul className="flex gap-1 p-0 font-mono text-sm">
        {secciones.map((seccion) => (
          <li key={seccion} className="list-none">
            <a
              href={'#' + anclaDe(seccion, idioma)}
              className="flex min-h-tactil items-center whitespace-nowrap px-2 text-tinta-suave no-underline hover:text-acento"
            >
              {t('secciones.' + seccion)}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

// esInicio: en el inicio el nombre es el <h1>; en la página de proyecto es un link al inicio.
export default function Encabezado({ perfil, esInicio, haySeccionProblemas }) {
  const { idioma, t } = useIdioma()
  const secciones = []
  for (const seccion of SECCIONES) {
    if (seccion === 'problemas' && !haySeccionProblemas) {
      continue
    }
    secciones.push(seccion)
  }

  return (
    <header className="encabezado border-b border-linea pb-2">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-superficie focus:p-3"
      >
        {t('encabezado.saltar')}
      </a>
      <div className="flex flex-col gap-4 pt-6 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {esInicio ? (
            <h1 className="m-0 text-3xl font-semibold leading-tight sm:text-4xl">{perfil.nombre}</h1>
          ) : (
            <p className="m-0 text-2xl font-semibold leading-tight">
              <a href={rutaInicio(idioma)} className="text-tinta no-underline hover:text-acento">
                {perfil.nombre}
              </a>
            </p>
          )}
          <TextoIdioma valor={perfil.titular} como="p" className="titular mt-1 mb-1 text-tinta-suave" />
          <EnlacesContacto perfil={perfil} />
        </div>
        <div className="controles flex shrink-0 items-center gap-3">
          <SelectorIdioma />
          <BotonCV perfil={perfil} />
        </div>
      </div>
      {esInicio ? <NavegacionSecciones secciones={secciones} /> : null}
    </header>
  )
}
