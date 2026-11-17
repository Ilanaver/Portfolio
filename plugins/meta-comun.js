// Helpers compartidos por el plugin meta-idioma (build y dev) y scripts/paginas_proyecto.mjs.
// Todo texto visible sale de src/i18n/*.json.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

export const RAIZ = resolve(import.meta.dirname, '..')

// Dominio de producción en Vercel. Si algún día hay dominio propio, se cambia acá (en el mismo commit).
export const URL_PRODUCCION = 'https://portfolio-eight-blond-udezm8x9wj.vercel.app'

// URL pública del sitio para canonical, hreflang y Open Graph (y la URL que muestra el CV impreso).
// Es la misma en local, en previews y en producción: los links canónicos siempre apuntan al sitio publicado.
// Se puede forzar con la variable SITIO_URL (por ejemplo, para probar un dominio nuevo).
export function urlSitio() {
  if (process.env.SITIO_URL) {
    return process.env.SITIO_URL.replace(/\/$/, '')
  }
  return URL_PRODUCCION
}

export function leerJson(rutaRelativa) {
  return JSON.parse(readFileSync(resolve(RAIZ, rutaRelativa), 'utf8'))
}

export function leerTraducciones() {
  return { es: leerJson('src/i18n/es.json'), en: leerJson('src/i18n/en.json') }
}

export function leerProyectos() {
  return leerJson('src/datos/proyectos.json').proyectos
}

export function escaparHtml(texto) {
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// Traducción simple para HTML generado: clave anidada + {valores}. Sin traducción → español.
export function traducir(traducciones, idioma, clave, valores = {}) {
  let texto = buscar(traducciones[idioma], clave)
  if (typeof texto !== 'string') {
    texto = buscar(traducciones.es, clave)
  }
  if (typeof texto !== 'string') {
    throw new Error('Falta la clave de traducción: ' + clave)
  }
  return texto.replace(/\{(\w+)\}/g, (completo, nombre) => {
    if (valores[nombre] === undefined) {
      return completo
    }
    return String(valores[nombre])
  })
}

function buscar(diccionario, clave) {
  let actual = diccionario
  for (const parte of clave.split('.')) {
    if (actual === null || typeof actual !== 'object') {
      return undefined
    }
    actual = actual[parte]
  }
  return actual
}

// Reemplaza {{es:clave}} / {{en:clave}} (usado en 404.html y en el <noscript> de /).
export function reemplazarTokens(html, traducciones) {
  return html.replace(/\{\{(es|en):([a-zA-Z0-9_.]+)\}\}/g, (completo, idioma, clave) =>
    escaparHtml(traducir(traducciones, idioma, clave)),
  )
}

function textoEnIdioma(valor, idioma) {
  if (idioma === 'en' && valor.en) {
    return valor.en
  }
  return valor.es
}

function etiqueta(nombre, atributos) {
  const partes = []
  for (const clave of Object.keys(atributos)) {
    partes.push(clave + '="' + escaparHtml(atributos[clave]) + '"')
  }
  return '<' + nombre + ' ' + partes.join(' ') + ' />'
}

// Bloque <head> con title, descripción, Open Graph, hreflang y canonical.
export function bloqueMeta(datos) {
  const sitio = urlSitio()
  const lineas = []
  lineas.push('<!--meta:inicio-->')
  lineas.push('<title>' + escaparHtml(datos.titulo) + '</title>')
  lineas.push(etiqueta('meta', { name: 'description', content: datos.descripcion }))
  lineas.push(etiqueta('link', { rel: 'canonical', href: sitio + datos.rutaCanonica }))
  lineas.push(etiqueta('link', { rel: 'alternate', hreflang: 'es', href: sitio + datos.rutaEs }))
  lineas.push(etiqueta('link', { rel: 'alternate', hreflang: 'en', href: sitio + datos.rutaEn }))
  lineas.push(etiqueta('link', { rel: 'alternate', hreflang: 'x-default', href: sitio + datos.rutaXDefault }))
  lineas.push(etiqueta('meta', { property: 'og:type', content: 'website' }))
  lineas.push(etiqueta('meta', { property: 'og:site_name', content: datos.nombreSitio }))
  lineas.push(etiqueta('meta', { property: 'og:title', content: datos.titulo }))
  lineas.push(etiqueta('meta', { property: 'og:description', content: datos.descripcion }))
  lineas.push(etiqueta('meta', { property: 'og:url', content: sitio + datos.rutaCanonica }))
  lineas.push(etiqueta('meta', { property: 'og:locale', content: datos.localeOg }))
  lineas.push(etiqueta('meta', { property: 'og:locale:alternate', content: datos.localeOgAlternativo }))
  lineas.push(etiqueta('meta', { property: 'og:image', content: sitio + datos.imagen.ruta }))
  lineas.push(etiqueta('meta', { property: 'og:image:width', content: String(datos.imagen.ancho) }))
  lineas.push(etiqueta('meta', { property: 'og:image:height', content: String(datos.imagen.alto) }))
  lineas.push(etiqueta('meta', { property: 'og:image:alt', content: datos.imagen.alt }))
  lineas.push(etiqueta('meta', { name: 'twitter:card', content: 'summary_large_image' }))
  lineas.push('<!--meta:fin-->')
  return lineas.join('\n    ')
}

function otro(idioma) {
  return idioma === 'es' ? 'en' : 'es'
}

function imagenPorDefecto(traducciones, idioma) {
  return {
    ruta: '/og-' + idioma + '.png',
    ancho: 1200,
    alto: 630,
    alt: traducir(traducciones, idioma, 'meta.imagen_og_alt'),
  }
}

function nombreSitio(traducciones, idioma) {
  return traducir(traducciones, idioma, 'meta.titulo_inicio')
}

// Meta del inicio (/es/, /en/) y de la raíz (/ → canónica /es/).
export function metaDeInicio(traducciones, idioma, esRaiz) {
  return bloqueMeta({
    titulo: traducir(traducciones, idioma, 'meta.titulo_inicio'),
    descripcion: traducir(traducciones, idioma, 'meta.descripcion_inicio'),
    nombreSitio: nombreSitio(traducciones, idioma),
    rutaCanonica: esRaiz ? '/es/' : '/' + idioma + '/',
    rutaEs: '/es/',
    rutaEn: '/en/',
    rutaXDefault: '/',
    localeOg: traducir(traducciones, idioma, 'meta.locale_og'),
    localeOgAlternativo: traducir(traducciones, otro(idioma), 'meta.locale_og'),
    imagen: imagenPorDefecto(traducciones, idioma),
  })
}

function imagenDeProyecto(proyecto, traducciones, idioma) {
  if (proyecto.imagen === null) {
    return imagenPorDefecto(traducciones, idioma)
  }
  const nombre = textoEnIdioma(proyecto.nombre, idioma)
  let alt = traducir(traducciones, idioma, 'captura.alt_auto', { nombre })
  if (proyecto.imagen.alt !== null) {
    alt = textoEnIdioma(proyecto.imagen.alt, idioma)
  }
  return {
    ruta: proyecto.imagen.archivos[idioma]['1200'],
    ancho: proyecto.imagen.ancho,
    alto: proyecto.imagen.alto,
    alt,
  }
}

export function rutaDeProyecto(idioma, slug) {
  return '/' + idioma + '/p/' + slug + '/'
}

// Meta propio de la página de un proyecto (P8).
export function metaDeProyecto(proyecto, traducciones, idioma) {
  const nombre = textoEnIdioma(proyecto.nombre, idioma)
  return bloqueMeta({
    titulo: traducir(traducciones, idioma, 'meta.titulo_proyecto', { nombre }),
    descripcion: textoEnIdioma(proyecto.descripcion, idioma),
    nombreSitio: nombreSitio(traducciones, idioma),
    rutaCanonica: rutaDeProyecto(idioma, proyecto.slug),
    rutaEs: rutaDeProyecto('es', proyecto.slug),
    rutaEn: rutaDeProyecto('en', proyecto.slug),
    rutaXDefault: rutaDeProyecto('es', proyecto.slug),
    localeOg: traducir(traducciones, idioma, 'meta.locale_og'),
    localeOgAlternativo: traducir(traducciones, otro(idioma), 'meta.locale_og'),
    imagen: imagenDeProyecto(proyecto, traducciones, idioma),
  })
}

// Ajusta un HTML de inicio (/es/ o /en/) para que sea la página de un proyecto (atributos y meta).
export function htmlDeProyecto(plantilla, proyecto, traducciones, idioma) {
  let html = plantilla.replace(
    /data-vista="inicio"/,
    'data-vista="proyecto" data-slug="' + escaparHtml(proyecto.slug) + '"',
  )
  html = html.replace(/<!--meta:inicio-->[\s\S]*?<!--meta:fin-->/, metaDeProyecto(proyecto, traducciones, idioma))
  return html
}

// Inserta el HTML pre-renderizado por React en <div id="root">.
export function conContenido(html, contenido) {
  if (!html.includes('<!--contenido-previo-->')) {
    throw new Error('La plantilla no tiene el marcador <!--contenido-previo-->')
  }
  return html.replace('<!--contenido-previo-->', () => contenido)
}

// Página mínima de redirección de un slug anterior al actual, en el mismo idioma.
export function htmlDeRedireccion(proyecto, traducciones, idioma) {
  const sitio = urlSitio()
  const destino = rutaDeProyecto(idioma, proyecto.slug)
  const nombre = textoEnIdioma(proyecto.nombre, idioma)
  const titulo = traducir(traducciones, idioma, 'redireccion.titulo')
  const texto = traducir(traducciones, idioma, 'redireccion.texto', { nombre })
  const enlace = traducir(traducciones, idioma, 'redireccion.enlace')
  return [
    '<!doctype html>',
    '<html lang="' + idioma + '">',
    '<head>',
    '<meta charset="UTF-8" />',
    '<meta name="viewport" content="width=device-width, initial-scale=1" />',
    '<meta name="robots" content="noindex" />',
    '<meta http-equiv="refresh" content="0; url=' + escaparHtml(destino) + '" />',
    '<link rel="canonical" href="' + escaparHtml(sitio + destino) + '" />',
    '<title>' + escaparHtml(titulo) + '</title>',
    '<script>window.location.replace(' + JSON.stringify(destino) + ' + window.location.search + window.location.hash)</script>',
    '</head>',
    '<body>',
    '<p>' + escaparHtml(texto) + '</p>',
    '<p><a href="' + escaparHtml(destino) + '">' + escaparHtml(enlace) + '</a></p>',
    '</body>',
    '</html>',
    '',
  ].join('\n')
}
