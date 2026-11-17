// Post-build (P8): por cada proyecto e idioma escribe dist/<idioma>/p/<slug>/index.html con su meta propio y
// contenido básico pre-renderizado; por cada slug anterior, una página de redirección en el mismo idioma.
// Uso: node scripts/paginas_proyecto.mjs  (lo corre `npm run build` después de `vite build`)
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import {
  RAIZ,
  htmlDeProyecto,
  htmlDeRedireccion,
  leerProyectos,
  leerTraducciones,
} from '../plugins/meta-comun.js'

const IDIOMAS = ['es', 'en']
const DIST = resolve(RAIZ, 'dist')

function escribir(rutaRelativa, contenido) {
  const destino = resolve(DIST, rutaRelativa)
  mkdirSync(dirname(destino), { recursive: true })
  writeFileSync(destino, contenido, 'utf8')
}

function leerPlantilla(idioma) {
  const ruta = resolve(DIST, idioma, 'index.html')
  if (!existsSync(ruta)) {
    throw new Error('No existe ' + ruta + ': corré primero `vite build`.')
  }
  return readFileSync(ruta, 'utf8')
}

function main() {
  const traducciones = leerTraducciones()
  const proyectos = leerProyectos()
  let paginas = 0
  let redirecciones = 0
  for (const idioma of IDIOMAS) {
    const plantilla = leerPlantilla(idioma)
    for (const proyecto of proyectos) {
      const html = htmlDeProyecto(plantilla, proyecto, traducciones, idioma, true)
      escribir(idioma + '/p/' + proyecto.slug + '/index.html', html)
      paginas += 1
      for (const slugAnterior of proyecto.slugs_anteriores) {
        escribir(idioma + '/p/' + slugAnterior + '/index.html', htmlDeRedireccion(proyecto, traducciones, idioma))
        redirecciones += 1
      }
    }
  }
  console.log('paginas_proyecto: ' + paginas + ' páginas de proyecto y ' + redirecciones + ' redirecciones')
}

main()
