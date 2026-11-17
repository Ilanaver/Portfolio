import Encabezado from '../componentes/Encabezado.jsx'
import SobreMi from '../componentes/SobreMi.jsx'
import Estudios from '../componentes/Estudios.jsx'
import Contacto from '../componentes/Contacto.jsx'

export default function Inicio({ perfil }) {
  return (
    <div className="pagina mx-auto max-w-5xl px-4">
      <Encabezado perfil={perfil} esInicio haySeccionProblemas={false} />
      <main id="contenido" className="contenido-inicio flex flex-col">
        <SobreMi perfil={perfil} />
        <Estudios perfil={perfil} />
        <Contacto perfil={perfil} />
      </main>
    </div>
  )
}
