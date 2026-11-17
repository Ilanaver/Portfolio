// Etiquetas, categorías y filtros de proyectos. Los filtros viven en la URL con claves, no con textos:
// /en/?tag=python,react&estado=activo

export const ORDEN_CATEGORIAS = [
  'lenguaje',
  'frontend',
  'backend',
  'datos',
  'infra',
  'automatizacion',
  'mensajeria',
  'ia',
  'otros',
]

export const ORDEN_ESTADOS = ['activo', 'pausado', 'terminado']

// "GitHub Actions" → "github-actions"; "Make.com" → "make-com".
export function claveEtiqueta(nombre) {
  return nombre
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function etiquetasDe(proyecto) {
  const todas = []
  for (const etiqueta of proyecto.tecnologias) {
    todas.push(etiqueta)
  }
  for (const etiqueta of proyecto.servicios) {
    todas.push(etiqueta)
  }
  return todas
}

export function clavesDeProyecto(proyecto) {
  const claves = new Set()
  for (const etiqueta of etiquetasDe(proyecto)) {
    claves.add(claveEtiqueta(etiqueta.nombre))
  }
  return claves
}

// { categoria → [{ clave, nombre, cantidad }] } ordenado por cantidad y nombre.
export function etiquetasPorCategoria(proyectos) {
  const porClave = new Map()
  for (const proyecto of proyectos) {
    const contadasEnEste = new Set()
    for (const etiqueta of etiquetasDe(proyecto)) {
      const clave = claveEtiqueta(etiqueta.nombre)
      if (contadasEnEste.has(clave)) {
        continue
      }
      contadasEnEste.add(clave)
      if (!porClave.has(clave)) {
        porClave.set(clave, { clave, nombre: etiqueta.nombre, categoria: etiqueta.categoria || 'otros', cantidad: 0 })
      }
      porClave.get(clave).cantidad += 1
    }
  }
  const grupos = []
  for (const categoria of ORDEN_CATEGORIAS) {
    const etiquetas = []
    for (const etiqueta of porClave.values()) {
      if (etiqueta.categoria === categoria) {
        etiquetas.push(etiqueta)
      }
    }
    if (etiquetas.length === 0) {
      continue
    }
    etiquetas.sort((a, b) => b.cantidad - a.cantidad || a.nombre.localeCompare(b.nombre))
    grupos.push({ categoria, etiquetas })
  }
  return grupos
}

export function estadosPresentes(proyectos) {
  const presentes = []
  for (const estado of ORDEN_ESTADOS) {
    for (const proyecto of proyectos) {
      if (proyecto.estado === estado) {
        presentes.push(estado)
        break
      }
    }
  }
  return presentes
}

function listaDeParametro(parametros, nombre) {
  const valor = parametros.get(nombre)
  if (!valor) {
    return []
  }
  const lista = []
  for (const parte of valor.split(',')) {
    const limpia = parte.trim()
    if (limpia && !lista.includes(limpia)) {
      lista.push(limpia)
    }
  }
  return lista
}

export function leerFiltros(search) {
  const parametros = new URLSearchParams(search)
  return { estados: listaDeParametro(parametros, 'estado'), etiquetas: listaDeParametro(parametros, 'tag') }
}

// Escribe los filtros en la URL sin recargar ni agregar historial (el ancla y otros parámetros se conservan).
export function escribirFiltros(filtros) {
  const url = new URL(window.location.href)
  if (filtros.estados.length > 0) {
    url.searchParams.set('estado', filtros.estados.join(','))
  } else {
    url.searchParams.delete('estado')
  }
  if (filtros.etiquetas.length > 0) {
    url.searchParams.set('tag', filtros.etiquetas.join(','))
  } else {
    url.searchParams.delete('tag')
  }
  const busqueda = url.searchParams.toString().replace(/%2C/g, ',')
  window.history.replaceState(window.history.state, '', url.pathname + (busqueda ? '?' + busqueda : '') + url.hash)
}

// Estado: cualquiera de los elegidos. Etiquetas: cualquiera de las elegidas.
export function filtrarProyectos(proyectos, filtros) {
  const resultado = []
  for (const proyecto of proyectos) {
    if (filtros.estados.length > 0 && !filtros.estados.includes(proyecto.estado)) {
      continue
    }
    if (filtros.etiquetas.length > 0) {
      const claves = clavesDeProyecto(proyecto)
      let coincide = false
      for (const etiqueta of filtros.etiquetas) {
        if (claves.has(etiqueta)) {
          coincide = true
          break
        }
      }
      if (!coincide) {
        continue
      }
    }
    resultado.push(proyecto)
  }
  return resultado
}

export function alternar(lista, valor) {
  if (lista.includes(valor)) {
    const sinValor = []
    for (const elemento of lista) {
      if (elemento !== valor) {
        sinValor.push(elemento)
      }
    }
    return sinValor
  }
  const conValor = []
  for (const elemento of lista) {
    conValor.push(elemento)
  }
  conValor.push(valor)
  return conValor
}
