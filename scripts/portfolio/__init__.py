"""Generador de datos del portfolio (Fase 2).

Módulos:
- archivo_estandar: lee y valida PORTFOLIO.md (frontmatter + secciones ES/EN).
- bitacora: solo encabezados de BITACORA.md → fecha + título.
- etiquetas: normalización de tecnologías y servicios con config/etiquetas.yml.
- identidad: claves opacas y filtro de redacción de todo lo que sale fuera del sitio.
- api_github: GraphQL + REST de GitHub con el token de solo lectura.
- imagenes: capturas manuales (tipo real, aprobación por hash, sin metadatos, WebP).
- capturas_auto: capturas automáticas con Playwright desde la demo pública.
- proyectos_extra: proyectos sin repo (config/proyectos_extra/).
- salida: armado, orden, versión anterior por proyecto, slugs y escritura estable.
- alertas / telegram: avisos por issue y por Telegram.
"""

from pathlib import Path

# Raíz del repo del portfolio (scripts/portfolio/__init__.py → dos niveles arriba de scripts/).
RAIZ = Path(__file__).resolve().parent.parent.parent
CARPETA_CONFIG = RAIZ / "config"
CARPETA_DATOS = RAIZ / "src" / "datos"
CARPETA_PUBLIC = RAIZ / "public"
