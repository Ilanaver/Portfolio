// Post-build (P8 + pre-renderizado):
// 1. Pre-renderiza con React (renderToString) el inicio de cada idioma: dist/es/index.html y dist/en/index.html.
// 2. Por cada proyecto e idioma escribe dist/<idioma>/p/<slug>/index.html con su meta propio y la página
//    completa pre-renderizada; en el navegador, main.jsx la hidrata con hydrateRoot.
// 3. Por cada slug anterior, una página de redirección en el mismo idioma.
// 4. CSS en línea (<style>) en todas las páginas, para que no bloquee el primer pintado.
// Uso: lo corre `npm run build` después de `vite build` y `vite build --ssr src/entrada-servidor.jsx`.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import {
  RAIZ,
  conContenido,
  htmlDeProyecto,
  htmlDeRedireccion,
  leerProyectos,
  leerTraducciones,
} from '../plugins/meta-comun.js'

const IDIOMAS = ['es', 'en']
const DIST = resolve(RAIZ, 'dist')
const ENTRADA_SERVIDOR = resolve(RAIZ, 'dist-servidor', 'entrada-servidor.js')

function escribir(rutaRelativa, contenido) {
  const destino = resolve(DIST, rutaRelativa)
  mkdirSync(dirname(destino), { recursive: true })
  writeFileSync(destino, contenido, 'utf8')
}

// Reemplaza <link rel="stylesheet" href="/assets/x.css"> por <style> con el contenido: así el CSS no bloquea
// el primer pintado (son pocos kB y las rutas de las fuentes ya son absolutas).
function inlinarCss(html) {
  return html.replace(/<link rel="stylesheet"[^>]*href="(\/assets\/[^"]+\.css)"[^>]*>/g, (completo, ruta) => {
    const css = readFileSync(resolve(DIST, ruta.slice(1)), 'utf8')
    return '<style>' + css + '</style>'
  })
}

function leerPlantilla(idioma) {
  const ruta = resolve(DIST, idioma, 'index.html')
  if (!existsSync(ruta)) {
    throw new Error('No existe ' + ruta + ': corré primero `vite build`.')
  }
  return inlinarCss(readFileSync(ruta, 'utf8'))
}

async function cargarRenderizador() {
  if (!existsSync(ENTRADA_SERVIDOR)) {
    throw new Error('No existe ' + ENTRADA_SERVIDOR + ': corré `vite build --ssr src/entrada-servidor.jsx`.')
  }
  const modulo = await import(pathToFileURL(ENTRADA_SERVIDOR).href)
  return modulo.renderizar
}

async function main() {
  const renderizar = await cargarRenderizador()
  const traducciones = leerTraducciones()
  const proyectos = leerProyectos()
  let paginas = 0
  let redirecciones = 0
  for (const idioma of IDIOMAS) {
    // Se lee la plantilla antes de escribir el inicio pre-renderizado: las páginas de proyecto parten de ella.
    const plantilla = leerPlantilla(idioma)
    escribir(idioma + '/index.html', conContenido(plantilla, renderizar(idioma, 'inicio', null)))
    for (const proyecto of proyectos) {
      const html = htmlDeProyecto(plantilla, proyecto, traducciones, idioma)
      escribir(
        idioma + '/p/' + proyecto.slug + '/index.html',
        conContenido(html, renderizar(idioma, 'proyecto', proyecto.slug)),
      )
      paginas += 1
      for (const slugAnterior of proyecto.slugs_anteriores) {
        escribir(idioma + '/p/' + slugAnterior + '/index.html', htmlDeRedireccion(proyecto, traducciones, idioma))
        redirecciones += 1
      }
    }
  }
  const ruta404 = resolve(DIST, '404.html')
  writeFileSync(ruta404, inlinarCss(readFileSync(ruta404, 'utf8')), 'utf8')
  console.log(
    'paginas_proyecto: 2 inicios y ' + paginas + ' páginas de proyecto pre-renderizados, ' + redirecciones + ' redirecciones',
  )
}

main()
