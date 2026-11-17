import { useIdioma } from '../i18n/index.js'
import { nombreDe } from '../lib/textos.js'
import Captura from './Captura.jsx'
import PlaceholderCaptura from './PlaceholderCaptura.jsx'

// Captura si existe; si no, el placeholder intencional (nunca un ícono de "imagen faltante").
export default function ImagenProyecto({ proyecto, principal = false, sizes, className = '' }) {
  const { idioma } = useIdioma()
  const nombre = nombreDe(proyecto, idioma)
  if (proyecto.imagen) {
    return <Captura imagen={proyecto.imagen} nombre={nombre} principal={principal} sizes={sizes} className={className} />
  }
  return (
    <PlaceholderCaptura
      nombre={nombre}
      tecnologias={proyecto.tecnologias}
      estado={proyecto.estado}
      className={className}
    />
  )
}
