import { useIdioma } from '../i18n/index.js'
import { formatearDia } from '../lib/fechas.js'
import { hitosDe } from '../lib/textos.js'
import { rutaProyecto } from '../lib/url.js'
import MarcaSoloEspanol from './MarcaSoloEspanol.jsx'

// En /es/: hitos + entradas de bitácora juntos, más nuevos arriba (a igual fecha, primero el hito).
// En /en/: Milestones (o Hitos marcados) y, si hay bitácora, un enlace a la versión en español (§3.4).
function itemsDe(proyecto, idioma) {
  const { hitos, esFallback } = hitosDe(proyecto, idioma)
  const items = []
  for (const hito of hitos) {
    items.push({ fecha: hito.fecha, texto: hito.texto, tipo: hito.tipo })
  }
  if (idioma === 'es') {
    for (const entrada of proyecto.bitacora) {
      items.push({ fecha: entrada.fecha, texto: entrada.titulo, tipo: 'bitacora' })
    }
  }
  const ordenTipo = { hito: 0, arreglo: 0, bitacora: 1 }
  const conIndice = []
  for (let indice = 0; indice < items.length; indice += 1) {
    conIndice.push({ item: items[indice], indice })
  }
  conIndice.sort((a, b) => {
    if (a.item.fecha !== b.item.fecha) {
      return a.item.fecha < b.item.fecha ? 1 : -1
    }
    if (ordenTipo[a.item.tipo] !== ordenTipo[b.item.tipo]) {
      return ordenTipo[a.item.tipo] - ordenTipo[b.item.tipo]
    }
    return a.indice - b.indice
  })
  const ordenados = []
  for (const elemento of conIndice) {
    ordenados.push(elemento.item)
  }
  return { items: ordenados, esFallback }
}

const ROTULO_TIPO = { hito: 'proyecto.tipo_hito', arreglo: 'proyecto.tipo_arreglo', bitacora: 'proyecto.tipo_bitacora' }

export default function LineaDeTiempo({ proyecto }) {
  const { idioma, t } = useIdioma()
  const { items, esFallback } = itemsDe(proyecto, idioma)
  const hayBitacora = proyecto.bitacora.length > 0
  const idSeccion = idioma === 'es' && hayBitacora ? 'bitacora' : 'linea-de-tiempo'

  return (
    <section id={idSeccion} aria-labelledby="linea-titulo" className="py-8">
      <h2 id="linea-titulo" className="mb-5 mt-0 text-xl font-semibold">
        {t('proyecto.linea_de_tiempo')}
        {esFallback ? <MarcaSoloEspanol /> : null}
      </h2>
      {items.length === 0 ? (
        <p className="m-0 text-tinta-suave">{t('proyecto.sin_linea_de_tiempo')}</p>
      ) : (
        <ol className="linea-tiempo" lang={esFallback ? 'es' : undefined}>
          {items.map((item, indice) => (
            <li key={indice} className="linea-tiempo__item">
              <span aria-hidden="true" className={'linea-tiempo__marca marca--' + item.tipo} />
              <p className="m-0 flex flex-wrap items-baseline gap-x-2 font-mono text-sm text-tinta-suave">
                <time dateTime={item.fecha}>{formatearDia(item.fecha, idioma)}</time>
                <span className={'rotulo ' + (item.tipo === 'arreglo' ? 'text-acento' : '')}>
                  {t(ROTULO_TIPO[item.tipo])}
                </span>
              </p>
              <p className="m-0 mt-0.5">{item.texto}</p>
            </li>
          ))}
        </ol>
      )}
      {idioma === 'en' && hayBitacora ? (
        <p className="m-0 mt-2 text-sm">
          <a href={rutaProyecto('es', proyecto.slug) + '#bitacora'} hrefLang="es" className="inline-flex min-h-tactil items-center">
            {t('proyecto.bitacora_en_espanol', { cantidad: proyecto.bitacora.length })}
          </a>
        </p>
      ) : null}
    </section>
  )
}
