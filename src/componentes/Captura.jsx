import { useIdioma } from '../i18n/index.js'
import { elegirTexto } from '../lib/textos.js'

// Alt: el de la captura manual; para las automáticas lo arma i18n.
function altDe(imagen, nombre, idioma, t) {
  if (imagen.alt !== null) {
    return elegirTexto(imagen.alt, idioma).texto
  }
  return t('captura.alt_auto', { nombre })
}

// Captura WebP (600/1200) con tamaño fijo para no mover el layout. principal = se carga sin lazy.
export default function Captura({ imagen, nombre, principal = false, sizes, className = '' }) {
  const { idioma, t } = useIdioma()
  const archivos = imagen.archivos[idioma]
  return (
    <img
      src={archivos['1200']}
      srcSet={archivos['600'] + ' 600w, ' + archivos['1200'] + ' 1200w'}
      sizes={sizes || '(min-width: 768px) 50vw, 100vw'}
      width={imagen.ancho}
      height={imagen.alto}
      loading={principal ? 'eager' : 'lazy'}
      fetchPriority={principal ? 'high' : 'auto'}
      decoding="async"
      alt={altDe(imagen, nombre, idioma, t)}
      className={'marco block aspect-[16/10] h-auto w-full object-cover object-top ' + className}
    />
  )
}
