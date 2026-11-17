import { localeDe } from '../i18n/index.js'

// Las fechas de los datos son AAAA-MM-DD o AAAA-MM. Se crean en UTC para que no se corran de día.
function aFechaUtc(texto) {
  const partes = texto.split('-')
  const anio = Number(partes[0])
  const mes = Number(partes[1]) - 1
  const dia = partes.length > 2 ? Number(partes[2]) : 1
  return new Date(Date.UTC(anio, mes, dia))
}

// "17 oct 2026" / "Oct 17, 2026"
export function formatearDia(texto, idioma) {
  const formato = new Intl.DateTimeFormat(localeDe(idioma), {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
  return formato.format(aFechaUtc(texto))
}

// "oct 2026" / "Oct 2026"
export function formatearMes(texto, idioma) {
  const formato = new Intl.DateTimeFormat(localeDe(idioma), {
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
  return formato.format(aFechaUtc(texto))
}

// Fecha de inicio o fin de un proyecto: se muestra a nivel mes aunque traiga día.
export function formatearPeriodo(texto, idioma) {
  return formatearMes(texto, idioma)
}

// Para ordenar: "2026-10" y "2026-10-17" comparan bien como texto.
export function compararFechasDesc(a, b) {
  if (a === b) {
    return 0
  }
  return a < b ? 1 : -1
}
