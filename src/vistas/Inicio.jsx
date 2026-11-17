import { useIdioma } from '../i18n/index.js'
import Encabezado from '../componentes/Encabezado.jsx'
import SobreMi from '../componentes/SobreMi.jsx'
import ListaProyectos from '../componentes/ListaProyectos.jsx'
import ProblemasResueltos, { arreglosDe } from '../componentes/ProblemasResueltos.jsx'
import Estudios from '../componentes/Estudios.jsx'
import Stack from '../componentes/Stack.jsx'
import Contacto from '../componentes/Contacto.jsx'

export default function Inicio({ perfil, proyectos }) {
  const { idioma } = useIdioma()
  const hayProblemas = arreglosDe(proyectos, idioma).length > 0
  return (
    <div className="pagina mx-auto max-w-5xl px-4">
      <Encabezado perfil={perfil} esInicio haySeccionProblemas={hayProblemas} />
      <main id="contenido" className="contenido-inicio flex flex-col">
        <SobreMi perfil={perfil} />
        <ListaProyectos proyectos={proyectos} />
        <ProblemasResueltos proyectos={proyectos} />
        <Estudios perfil={perfil} />
        <Stack proyectos={proyectos} />
        <Contacto perfil={perfil} />
      </main>
    </div>
  )
}
