import { useIdioma } from '../i18n/index.js'
import { nombreDe } from '../lib/textos.js'
import { rutaInicio } from '../lib/url.js'
import Encabezado from '../componentes/Encabezado.jsx'
import ImagenProyecto from '../componentes/ImagenProyecto.jsx'
import IndicadorEstado from '../componentes/IndicadorEstado.jsx'
import LineaDeTiempo from '../componentes/LineaDeTiempo.jsx'
import { FichaTecnica } from '../componentes/TarjetaProyecto.jsx'
import { TextoIdioma } from '../componentes/MarcaSoloEspanol.jsx'

// "Volver" usa el historial si se llegó desde este mismo sitio (así se conservan los filtros de la URL).
function volver(evento) {
  const vieneDelSitio = document.referrer.startsWith(window.location.origin)
  if (vieneDelSitio && window.history.length > 1) {
    evento.preventDefault()
    window.history.back()
  }
}

function BloqueTexto({ titulo, valor }) {
  return (
    <section className="marco p-4">
      <h2 className="rotulo m-0 mb-2">{titulo}</h2>
      <TextoIdioma valor={valor} como="p" className="m-0 leading-relaxed" />
    </section>
  )
}

function NoEncontrado() {
  const { idioma, t } = useIdioma()
  return (
    <div className="py-16">
      <p className="m-0 text-xl">{t('proyecto.no_encontrado')}</p>
      <p className="m-0 mt-2">
        <a href={rutaInicio(idioma)} className="inline-flex min-h-tactil items-center">
          {t('proyecto.ir_al_inicio')}
        </a>
      </p>
    </div>
  )
}

export default function PaginaProyecto({ perfil, proyecto }) {
  const { idioma, t } = useIdioma()
  return (
    <div className="pagina mx-auto max-w-5xl px-4">
      <Encabezado perfil={perfil} esInicio={false} />
      <main id="contenido" className="pb-12">
        {proyecto ? (
          <article className="pagina-proyecto">
            <p className="m-0 pt-4">
              <a
                href={rutaInicio(idioma) + '#' + (idioma === 'es' ? 'proyectos' : 'projects')}
                onClick={volver}
                aria-label={t('proyecto.volver_aria')}
                className="inline-flex min-h-tactil items-center font-mono text-sm no-underline hover:underline"
              >
                ← {t('proyecto.volver')}
              </a>
            </p>
            <div className="grid gap-6 pt-2 md:grid-cols-[1.15fr_1fr]">
              <ImagenProyecto proyecto={proyecto} principal sizes="(min-width: 768px) 540px, 100vw" />
              <div className="flex min-w-0 flex-col gap-3">
                <IndicadorEstado estado={proyecto.estado} className="text-tinta-suave" />
                <h1 className="m-0 font-mono text-3xl font-medium leading-tight">{nombreDe(proyecto, idioma)}</h1>
                <TextoIdioma valor={proyecto.descripcion} como="p" className="m-0 text-lg" />
                <FichaTecnica proyecto={proyecto} />
              </div>
            </div>
            <div className="grid gap-4 pt-8 md:grid-cols-2">
              <BloqueTexto titulo={t('proyecto.idea_original')} valor={proyecto.idea_original} />
              <BloqueTexto titulo={t('proyecto.resultado')} valor={proyecto.resultado} />
            </div>
            <LineaDeTiempo proyecto={proyecto} />
          </article>
        ) : (
          <NoEncontrado />
        )}
      </main>
    </div>
  )
}
