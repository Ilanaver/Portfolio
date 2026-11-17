// Plugin de Vite: <title>, descripción, Open Graph, hreflang y canonical de /, /es/ y /en/,
// textos {{es:clave}} de 404.html y de /, y (solo en desarrollo) las páginas /<idioma>/p/<slug>/.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  RAIZ,
  htmlDeProyecto,
  leerProyectos,
  leerTraducciones,
  metaDeInicio,
  reemplazarTokens,
} from './meta-comun.js'

function atributo(html, nombre) {
  const coincidencia = html.match(new RegExp(nombre + '="([^"]*)"'))
  return coincidencia ? coincidencia[1] : null
}

function transformar(html) {
  const traducciones = leerTraducciones()
  const vista = atributo(html, 'data-vista')
  const idioma = atributo(html, 'data-idioma') === 'en' ? 'en' : 'es'
  let resultado = reemplazarTokens(html, traducciones)
  if (vista === 'inicio' || vista === 'raiz') {
    resultado = resultado.replace('<!--meta-idioma-->', metaDeInicio(traducciones, idioma, vista === 'raiz'))
  }
  return resultado
}

// En desarrollo no existen los HTML de proyecto (los genera paginas_proyecto.mjs después del build):
// se arman al vuelo desde es/index.html o en/index.html.
function middlewareProyectos(servidor) {
  return async function (pedido, respuesta, siguiente) {
    const coincidencia = (pedido.url || '').match(/^\/(es|en)\/p\/([a-z0-9-]+)\/?(\?.*)?$/)
    if (!coincidencia) {
      siguiente()
      return
    }
    const idioma = coincidencia[1]
    const slug = coincidencia[2]
    const proyecto = leerProyectos().find((candidato) => candidato.slug === slug)
    if (!proyecto) {
      siguiente()
      return
    }
    try {
      const plantilla = readFileSync(resolve(RAIZ, idioma, 'index.html'), 'utf8')
      const conMeta = transformar(plantilla)
      const html = htmlDeProyecto(conMeta, proyecto, leerTraducciones(), idioma)
      const final = await servidor.transformIndexHtml(pedido.url, html, '/' + idioma + '/index.html')
      respuesta.setHeader('Content-Type', 'text/html; charset=utf-8')
      respuesta.end(final)
    } catch (error) {
      siguiente(error)
    }
  }
}

export default function metaIdioma() {
  return {
    name: 'meta-idioma',
    transformIndexHtml: {
      order: 'pre',
      handler(html) {
        return transformar(html)
      },
    },
    configureServer(servidor) {
      servidor.middlewares.use(middlewareProyectos(servidor))
    },
  }
}
