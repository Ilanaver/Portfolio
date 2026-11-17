import Seccion from './Seccion.jsx'
import { TextoIdioma } from './MarcaSoloEspanol.jsx'

export default function SobreMi({ perfil }) {
  return (
    <Seccion clave="sobre_mi">
      <div className="flex max-w-prose flex-col gap-4">
        {perfil.sobre_mi.map((parrafo, indice) => (
          <TextoIdioma key={indice} valor={parrafo} como="p" className="m-0 text-lg leading-relaxed" />
        ))}
      </div>
    </Seccion>
  )
}
