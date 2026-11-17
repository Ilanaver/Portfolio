import { useIdioma } from '../i18n/index.js'
import IndicadorEstado from './IndicadorEstado.jsx'

const MAX_CHIPS = 4

// Tamaño del nombre en unidades del contenedor: los nombres largos se achican y parten en dos líneas.
function tamanoNombre(nombre) {
  const largo = nombre.length
  if (largo <= 8) {
    return 11
  }
  if (largo <= 14) {
    return 8.5
  }
  if (largo <= 22) {
    return 6.5
  }
  if (largo <= 34) {
    return 5.2
  }
  return 4.2
}

// Portada de ficha técnica cuando no hay captura. Decorativa: el nombre y las tecnologías ya están en la tarjeta.
export default function PlaceholderCaptura({ nombre, tecnologias, estado, className = '' }) {
  const { t } = useIdioma()
  const visibles = tecnologias.slice(0, MAX_CHIPS)
  const resto = tecnologias.length - visibles.length
  return (
    <div className={'placeholder marco ' + className} aria-hidden="true">
      <span className="placeholder__estado z-10">
        <IndicadorEstado estado={estado} />
      </span>
      <div className="placeholder__interior">
        <p className="placeholder__nombre" style={{ fontSize: 'clamp(1.125rem, ' + tamanoNombre(nombre) + 'cqi, 4rem)' }}>
          {nombre}
        </p>
        <ul className="placeholder__chips">
          {visibles.map((tecnologia) => (
            <li key={tecnologia.nombre} className="placeholder__chip">
              {tecnologia.nombre}
            </li>
          ))}
          {resto > 0 ? <li className="placeholder__chip">{t('ficha.mas_tecnologias', { cantidad: resto })}</li> : null}
        </ul>
      </div>
    </div>
  )
}
