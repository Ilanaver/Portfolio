import { useIdioma } from '../i18n/index.js'
import { formatearDia } from '../lib/fechas.js'
import { hitosDe, nombreDe } from '../lib/textos.js'
import { rutaProyecto } from '../lib/url.js'
import MarcaSoloEspanol from './MarcaSoloEspanol.jsx'
import Seccion from './Seccion.jsx'

// Todos los hitos de tipo arreglo de todos los proyectos, más nuevos arriba.
export function arreglosDe(proyectos, idioma) {
  const arreglos = []
  for (const proyecto of proyectos) {
    const { hitos, esFallback } = hitosDe(proyecto, idioma)
    for (const hito of hitos) {
      if (hito.tipo !== 'arreglo') {
        continue
      }
      arreglos.push({ hito, proyecto, esFallback })
    }
  }
  arreglos.sort((a, b) => {
    if (a.hito.fecha === b.hito.fecha) {
      return 0
    }
    return a.hito.fecha < b.hito.fecha ? 1 : -1
  })
  return arreglos
}

// "problema → causa → arreglo" se muestra en tres renglones rotulados; si no tiene ese formato, tal cual.
function partesDe(texto) {
  const partes = texto.split('→')
  if (partes.length !== 3) {
    return null
  }
  const limpias = []
  for (const parte of partes) {
    const limpia = parte.trim()
    limpias.push(limpia.charAt(0).toLocaleUpperCase() + limpia.slice(1))
  }
  return limpias
}

function TextoArreglo({ texto }) {
  const { t } = useIdioma()
  const partes = partesDe(texto)
  if (partes === null) {
    return <p className="m-0">{texto}</p>
  }
  const rotulos = ['problemas.problema', 'problemas.causa', 'problemas.arreglo']
  return (
    <dl className="m-0 grid grid-cols-[6rem_1fr] gap-x-3 gap-y-1 max-sm:grid-cols-1">
      {partes.map((parte, indice) => (
        <div key={indice} className="contents">
          <dt className="rotulo pt-0.5">{t(rotulos[indice])}</dt>
          <dd className={'m-0 ' + (indice === 2 ? 'font-medium' : '')}>{parte}</dd>
        </div>
      ))}
    </dl>
  )
}

export default function ProblemasResueltos({ proyectos }) {
  const { idioma, t } = useIdioma()
  const arreglos = arreglosDe(proyectos, idioma)
  if (arreglos.length === 0) {
    return null
  }
  return (
    <Seccion clave="problemas">
      <p className="m-0 mb-5 max-w-prose text-tinta-suave">{t('problemas.intro')}</p>
      <ol className="lista-problemas m-0 flex flex-col gap-4 p-0">
        {arreglos.map(({ hito, proyecto, esFallback }, indice) => {
          const nombre = nombreDe(proyecto, idioma)
          return (
            <li key={indice} className="marco list-none p-4" lang={esFallback ? 'es' : undefined}>
              <p className="m-0 mb-3 flex flex-wrap items-baseline gap-x-3 font-mono text-sm text-tinta-suave">
                <time dateTime={hito.fecha}>{formatearDia(hito.fecha, idioma)}</time>
                <a href={rutaProyecto(idioma, proyecto.slug)} className="inline-flex min-h-tactil items-center" lang={idioma}>
                  {t('problemas.en_proyecto', { nombre })}
                </a>
                {esFallback ? <MarcaSoloEspanol /> : null}
              </p>
              <TextoArreglo texto={hito.texto} />
            </li>
          )
        })}
      </ol>
    </Seccion>
  )
}
