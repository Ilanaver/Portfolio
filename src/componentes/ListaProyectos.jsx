import Seccion from './Seccion.jsx'
import TarjetaProyecto from './TarjetaProyecto.jsx'

export default function ListaProyectos({ proyectos }) {
  return (
    <Seccion clave="proyectos">
      <div className="grilla-proyectos grid grid-cols-1 gap-5 md:grid-cols-2">
        {proyectos.map((proyecto) => (
          <TarjetaProyecto key={proyecto.clave} proyecto={proyecto} />
        ))}
      </div>
    </Seccion>
  )
}
