import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'node:path'
import metaIdioma from './plugins/meta-idioma.js'
import { urlSitio } from './plugins/meta-comun.js'

const raiz = import.meta.dirname

// Cada ruta es un HTML estático que carga el mismo bundle (sin router de cliente).
const entradas = {
  raiz: resolve(raiz, 'index.html'),
  es: resolve(raiz, 'es/index.html'),
  en: resolve(raiz, 'en/index.html'),
  error404: resolve(raiz, '404.html'),
}

export default defineConfig({
  appType: 'mpa',
  plugins: [react(), tailwindcss(), metaIdioma()],
  // URL pública del sitio (se muestra en el CV impreso).
  define: { __SITIO_URL__: JSON.stringify(urlSitio()) },
  // Vista previa de dist/ por túnel HTTPS temporal (pruebas desde el celular en redes con aislamiento).
  preview: { allowedHosts: ['.trycloudflare.com'] },
  build: {
    rollupOptions: { input: entradas },
  },
})
