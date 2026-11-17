// Plugin de Vite: meta, hreflang y canonical de las páginas de inicio (se completa en el paso 9).
export default function metaIdioma() {
  return {
    name: 'meta-idioma',
    transformIndexHtml(html) {
      return html
    },
  }
}
