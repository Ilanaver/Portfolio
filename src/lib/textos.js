// Textos de contenido { es, en }. En /en/, si 'en' es null se usa el español y se marca.

export function elegirTexto(valor, idioma) {
  if (valor === null || valor === undefined) {
    return { texto: '', esFallback: false }
  }
  if (idioma === 'en') {
    if (valor.en) {
      return { texto: valor.en, esFallback: false }
    }
    return { texto: valor.es, esFallback: true }
  }
  return { texto: valor.es, esFallback: false }
}

// Nombre del proyecto: nunca lleva marca (sin traducción repite el español).
export function nombreDe(proyecto, idioma) {
  return idioma === 'en' ? proyecto.nombre.en : proyecto.nombre.es
}

// Hitos según §3.4: en /en/ los Milestones; si no hay, los Hitos en español (marcados).
export function hitosDe(proyecto, idioma) {
  if (idioma === 'en' && proyecto.hitos.en !== null) {
    return { hitos: proyecto.hitos.en, esFallback: false }
  }
  if (idioma === 'en') {
    return { hitos: proyecto.hitos.es, esFallback: true }
  }
  return { hitos: proyecto.hitos.es, esFallback: false }
}
