// Chip de tecnología o servicio (nombres propios: no se traducen).
export default function Etiqueta({ nombre }) {
  return (
    <li className="etiqueta list-none border border-linea bg-papel px-2 py-0.5 font-mono text-xs leading-5 text-tinta">
      {nombre}
    </li>
  )
}
