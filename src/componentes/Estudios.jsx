import { useIdioma } from '../i18n/index.js'
import { formatearPeriodo } from '../lib/fechas.js'
import Seccion from './Seccion.jsx'
import { TextoIdioma } from './MarcaSoloEspanol.jsx'

function periodoDe(estudio, idioma, t) {
  const inicio = formatearPeriodo(estudio.inicio, idioma)
  if (estudio.fin === null) {
    return t('ficha.desde', { inicio })
  }
  return t('ficha.rango', { inicio, fin: formatearPeriodo(estudio.fin, idioma) })
}

export default function Estudios({ perfil }) {
  const { idioma, t } = useIdioma()
  return (
    <Seccion clave="estudios">
      <ul className="m-0 flex flex-col gap-3 p-0">
        {perfil.estudios.map((estudio, indice) => (
          <li key={indice} className="marco list-none p-4">
            <p className="m-0 text-lg font-medium">
              <TextoIdioma valor={estudio.titulo} /> — {estudio.institucion}
            </p>
            <p className="m-0 font-mono text-sm text-tinta-suave">
              {periodoDe(estudio, idioma, t)}
              {estudio.detalle ? (
                <>
                  {' · '}
                  <TextoIdioma valor={estudio.detalle} />
                </>
              ) : null}
            </p>
          </li>
        ))}
      </ul>
    </Seccion>
  )
}
