import { useIdioma } from '../i18n/index.js'

const COLORES = {
  activo: 'bg-estado-activo',
  pausado: 'bg-estado-pausado',
  terminado: 'bg-estado-terminado',
}

export default function IndicadorEstado({ estado, className = '' }) {
  const { t } = useIdioma()
  return (
    <span className={'inline-flex items-center gap-1.5 font-mono text-xs uppercase tracking-wide ' + className}>
      <span aria-hidden="true" className={'inline-block size-2 rounded-full ' + COLORES[estado]} />
      {t('estados.' + estado)}
    </span>
  )
}
