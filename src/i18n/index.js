import { createContext, useContext } from 'react'
import es from './es.json'
import en from './en.json'

export const IDIOMAS = ['es', 'en']

const diccionarios = { es, en }

// Busca una clave anidada tipo "ficha.estado" en un diccionario.
function buscarClave(diccionario, clave) {
  const partes = clave.split('.')
  let actual = diccionario
  for (const parte of partes) {
    if (actual === null || typeof actual !== 'object') {
      return undefined
    }
    actual = actual[parte]
  }
  return actual
}

// Reemplaza {nombre} por su valor; los números se formatean según el idioma.
function interpolar(texto, valores, idioma) {
  return texto.replace(/\{(\w+)\}/g, (completo, nombre) => {
    const valor = valores[nombre]
    if (valor === undefined || valor === null) {
      return completo
    }
    if (typeof valor === 'number') {
      return new Intl.NumberFormat(localeDe(idioma)).format(valor)
    }
    return String(valor)
  })
}

// Plural simple: si hay {cantidad} y existen clave_uno / clave_otros, elige una.
function claveConPlural(diccionario, clave, valores) {
  if (typeof valores.cantidad !== 'number') {
    return clave
  }
  const sufijo = valores.cantidad === 1 ? '_uno' : '_otros'
  if (typeof buscarClave(diccionario, clave + sufijo) === 'string') {
    return clave + sufijo
  }
  return clave
}

export function localeDe(idioma) {
  return idioma === 'en' ? 'en-US' : 'es-AR'
}

// t(clave, valores). Clave faltante: [clave] en desarrollo, español en producción.
export function crearTraductor(idioma) {
  const diccionario = diccionarios[idioma] || es
  return function t(clave, valores = {}) {
    const claveFinal = claveConPlural(diccionario, clave, valores)
    let texto = buscarClave(diccionario, claveFinal)
    if (typeof texto !== 'string') {
      if (import.meta.env && import.meta.env.DEV) {
        return '[' + claveFinal + ']'
      }
      texto = buscarClave(es, claveFinal)
      if (typeof texto !== 'string') {
        return ''
      }
    }
    return interpolar(texto, valores, idioma)
  }
}

export const IdiomaContexto = createContext({
  idioma: 'es',
  t: crearTraductor('es'),
  rutas: { es: '/es/', en: '/en/' },
})

export function useIdioma() {
  return useContext(IdiomaContexto)
}

export function otroIdioma(idioma) {
  return idioma === 'es' ? 'en' : 'es'
}

// Guarda la elección del selector (para la redirección de "/"). Nunca rompe si no hay storage.
export function guardarIdioma(idioma) {
  try {
    window.localStorage.setItem('idioma', idioma)
  } catch (error) {
    // sin localStorage (modo privado, bloqueado): la elección no se recuerda
  }
}
