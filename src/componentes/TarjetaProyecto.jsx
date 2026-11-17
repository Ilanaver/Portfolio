import { useIdioma } from '../i18n/index.js'
import { formatearMes, formatearPeriodo } from '../lib/fechas.js'
import { nombreDe } from '../lib/textos.js'
import { rutaProyecto } from '../lib/url.js'
import Etiqueta from './Etiqueta.jsx'
import ImagenProyecto from './ImagenProyecto.jsx'
import IndicadorEstado from './IndicadorEstado.jsx'
import { TextoIdioma } from './MarcaSoloEspanol.jsx'

export function periodoDeProyecto(proyecto, idioma, t) {
  const inicio = formatearPeriodo(proyecto.fecha_inicio, idioma)
  if (proyecto.fecha_fin === null) {
    return t('ficha.desde', { inicio })
  }
  return t('ficha.rango', { inicio, fin: formatearPeriodo(proyecto.fecha_fin, idioma) })
}

// Links externos del proyecto (demo, repo si es público, otros).
export function LinksProyecto({ proyecto, className = '' }) {
  const { t } = useIdioma()
  const enlaces = []
  if (proyecto.links.demo) {
    enlaces.push({ clave: 'demo', url: proyecto.links.demo, texto: <>{t('ficha.demo')}</> })
  }
  if (proyecto.links.repo) {
    enlaces.push({ clave: 'repo', url: proyecto.links.repo, texto: <>{t('ficha.repo')}</> })
  }
  let indice = 0
  for (const otro of proyecto.links.otros) {
    enlaces.push({ clave: 'otro-' + indice, url: otro.url, texto: <TextoIdioma valor={otro.texto} /> })
    indice += 1
  }
  if (enlaces.length === 0) {
    return null
  }
  return (
    <ul className={'relative z-10 flex flex-wrap gap-x-4 p-0 ' + className}>
      {enlaces.map((enlace) => (
        <li key={enlace.clave} className="list-none">
          <a href={enlace.url} className="inline-flex min-h-tactil items-center text-sm" rel="noopener">
            {enlace.texto}
          </a>
        </li>
      ))}
    </ul>
  )
}

function FilaFicha({ rotulo, children }) {
  return (
    <div className="grid grid-cols-[9rem_1fr] gap-x-3 gap-y-1 border-t border-linea py-2 max-sm:grid-cols-1">
      <dt className="rotulo pt-0.5">{rotulo}</dt>
      <dd className="m-0 min-w-0">{children}</dd>
    </div>
  )
}

export function FichaTecnica({ proyecto, conLinks = true }) {
  const { idioma, t } = useIdioma()
  return (
    <dl className="ficha m-0">
      <FilaFicha rotulo={t('ficha.periodo')}>
        <span className="font-mono text-sm">{periodoDeProyecto(proyecto, idioma, t)}</span>
      </FilaFicha>
      <FilaFicha rotulo={t('ficha.ultima_actividad')}>
        <span className="font-mono text-sm">{formatearMes(proyecto.ultima_actividad, idioma)}</span>
      </FilaFicha>
      <FilaFicha rotulo={t('ficha.tecnologias')}>
        <ul className="flex flex-wrap gap-1.5 p-0">
          {proyecto.tecnologias.map((etiqueta) => (
            <Etiqueta key={etiqueta.nombre} nombre={etiqueta.nombre} />
          ))}
        </ul>
      </FilaFicha>
      {proyecto.servicios.length > 0 ? (
        <FilaFicha rotulo={t('ficha.servicios')}>
          <ul className="flex flex-wrap gap-1.5 p-0">
            {proyecto.servicios.map((etiqueta) => (
              <Etiqueta key={etiqueta.nombre} nombre={etiqueta.nombre} />
            ))}
          </ul>
        </FilaFicha>
      ) : null}
      {conLinks && (proyecto.links.demo || proyecto.links.repo || proyecto.links.otros.length > 0) ? (
        <FilaFicha rotulo={t('ficha.links')}>
          <LinksProyecto proyecto={proyecto} className="-my-2" />
        </FilaFicha>
      ) : null}
    </dl>
  )
}

// Tarjeta: toda la tarjeta lleva a la página del proyecto (link del nombre estirado);
// los links externos quedan por encima y se pueden tocar aparte.
export default function TarjetaProyecto({ proyecto }) {
  const { idioma, t } = useIdioma()
  const nombre = nombreDe(proyecto, idioma)
  const destacado = proyecto.destacado
  const disposicion = destacado ? 'md:col-span-2 md:grid md:grid-cols-[1.1fr_1fr] md:gap-6' : ''
  return (
    <article
      className={
        'tarjeta relative flex flex-col gap-4 border border-linea bg-superficie p-4 transition-colors hover:border-acento ' +
        disposicion
      }
    >
      <ImagenProyecto proyecto={proyecto} sizes={destacado ? '(min-width: 768px) 520px, 100vw' : '(min-width: 768px) 460px, 100vw'} />
      <div className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <IndicadorEstado estado={proyecto.estado} className="text-tinta-suave" />
          {destacado ? <span className="rotulo text-acento">{t('ficha.destacado')}</span> : null}
        </div>
        <h3 className={'m-0 font-mono font-medium leading-tight ' + (destacado ? 'text-2xl' : 'text-xl')}>
          <a
            href={rutaProyecto(idioma, proyecto.slug)}
            aria-label={t('ficha.ver_proyecto_aria', { nombre })}
            className="text-tinta no-underline after:absolute after:inset-0 after:content-[''] hover:text-acento"
          >
            {nombre}
          </a>
        </h3>
        <TextoIdioma valor={proyecto.descripcion} como="p" className="m-0 text-tinta" />
        <FichaTecnica proyecto={proyecto} />
        <span aria-hidden="true" className="mt-auto font-mono text-sm text-acento">
          {t('ficha.ver_proyecto')} →
        </span>
      </div>
    </article>
  )
}
