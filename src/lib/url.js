// Rutas, anclas por idioma y cambio de idioma conservando ?filtros y #ancla.

// Ids de las secciones del inicio en cada idioma.
const ANCLAS = {
  sobre_mi: { es: 'sobre-mi', en: 'about' },
  proyectos: { es: 'proyectos', en: 'projects' },
  problemas: { es: 'problemas', en: 'problems' },
  estudios: { es: 'estudios', en: 'education' },
  stack: { es: 'stack', en: 'stack' },
  contacto: { es: 'contacto', en: 'contact' },
}

export function anclaDe(seccion, idioma) {
  return ANCLAS[seccion][idioma]
}

// Traduce el #ancla al otro idioma; si no es una sección conocida, la deja igual.
export function traducirAncla(hash, idiomaDestino) {
  if (!hash || hash === '#') {
    return ''
  }
  const id = hash.slice(1)
  for (const seccion of Object.keys(ANCLAS)) {
    const par = ANCLAS[seccion]
    if (par.es === id || par.en === id) {
      return '#' + par[idiomaDestino]
    }
  }
  return hash
}

// /es/p/x/ → /en/p/x/ ; /es/ → /en/
export function rutaEnIdioma(pathname, idiomaDestino) {
  const sinIdioma = pathname.replace(/^\/(es|en)(\/|$)/, '/')
  return '/' + idiomaDestino + sinIdioma
}

export function urlEnIdioma(ubicacion, idiomaDestino) {
  const ruta = rutaEnIdioma(ubicacion.pathname, idiomaDestino)
  return ruta + ubicacion.search + traducirAncla(ubicacion.hash, idiomaDestino)
}

export function rutaInicio(idioma) {
  return '/' + idioma + '/'
}

export function rutaProyecto(idioma, slug) {
  return '/' + idioma + '/p/' + slug + '/'
}

// "https://github.com/Ilanaver" → "github.com/Ilanaver" (para mostrar en el CV impreso).
export function urlVisible(url) {
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}
