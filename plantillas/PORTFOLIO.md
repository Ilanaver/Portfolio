---
# PORTFOLIO.md — ficha pública de este proyecto en el portfolio de Ilán (formato versión 1).
# Todo lo que está en este frontmatter y en las secciones reconocidas de abajo es PÚBLICO.
# Nunca poner secretos, URLs internas, nombres de terceros, montos ni datos personales.
version: 1

# visible: false = no se publica nada de este repo. Pasar a true solo con OK de Ilán.
visible: false

# mostrar_bitacora: true = se publican FECHA + TÍTULO de las entradas de BITACORA.md (solo en /es/).
#   El cuerpo de las entradas nunca se publica. Pasar a true solo con OK de Ilán.
mostrar_bitacora: false

nombre: COMPLETAR nombre del proyecto (1–60 caracteres)
# nombre_en: solo si el nombre se traduce (si falta, se usa `nombre`).

# slug: define la URL /es/p/<slug>/ y /en/p/<slug>/. Default: nombre del repo en minúsculas.
#   Solo a-z, 0-9 y guiones. Único entre todos los proyectos.
# slug: mi-proyecto

# slugs_anteriores: []
#   Si cambiás el slug, agregá acá el anterior (nunca borres entradas): los links viejos
#   redirigen a la página nueva en el mismo idioma.
slugs_anteriores: []

descripcion: COMPLETAR qué hace, en una línea (1–160 caracteres).
descripcion_en: TO DO what it does, in one line (1–160 characters).

# estado: activo | terminado | pausado
estado: activo
# fecha_inicio: AAAA-MM-DD o AAAA-MM (default: fecha de creación del repo).
# fecha_inicio: 2026-01
# fecha_fin: obligatoria si estado es terminado; prohibida si es activo.
# fecha_fin: 2026-06

# destacado: true = arriba, más grande y primero en el CV en PDF.
destacado: false

# tecnologias: 1–15. Nombres propios (no se traducen). Las primeras 4 se ven en el placeholder.
tecnologias: [Python]
# servicios: 0–15 (GitHub Actions, Vercel, Telegram, …).
servicios: []

links:
  # demo: solo https://. Si es pública, se usa para la captura automática.
  demo: null
  # repo: auto = link al repo SOLO si es público (en privados se fuerza null).
  repo: auto
  # otros: máximo 3, solo https://
  #   - texto: Artículo
  #     texto_en: Article
  #     url: https://…
  otros: []

# captura_auto:  (default: true en repos públicos; false en repos PRIVADOS)
#   Si hay links.demo público, el Action saca la captura solo (una vez por día, ES y EN).
#   Ponelo en false si la página no sale bien (banner, pantalla de carga, login).
#   REPOS PRIVADOS: queda en false. Las capturas de privados pasan por la aprobación de Ilán
#   por hash (ver `imagen`). Ponerlo en true en un privado solo con OK explícito de Ilán.

# imagen:  (OPCIONAL, solo capturas manuales: repos privados o sin interfaz)
#   REPOS PRIVADOS: la captura la revisa Ilán antes de publicarse. Tiene que estar libre de
#   montos, posiciones, nombres y datos personales (también en pestañas, barras y notificaciones
#   que se vean en la captura). Recién después de su OK se completa `aprobada` con el hash que
#   da `python -X utf8 scripts/auditar_repos.py --hash-imagen <repo>`.
#   PNG, JPG o WebP, ≤ 5 MB, ancho ≥ 800 px.
# imagen:
#   archivo: docs/portfolio/captura.png
#   alt: Qué se ve en la captura.
#   alt_en: What the screenshot shows.
#   aprobada: null

# bitacora:  (opcional; solo se usa con mostrar_bitacora: true)
#   archivo: BITACORA.md
#   max_entradas: 10
---

<!--
Secciones reconocidas (título exacto). Las de español son obligatorias salvo Hitos; las de inglés
son opcionales pero se esperan: si faltan, /en/ muestra el español con una marca "ES".
Cualquier otra sección (por ejemplo "## Notas internas") NO se publica.
-->

## Idea original
COMPLETAR: qué se quería hacer al arrancar (máx. ~600 caracteres).

## Original idea
<!-- TO DO: what the goal was when it started. -->

## Resultado
COMPLETAR: qué quedó de verdad y qué cambió respecto de la idea (máx. ~900 caracteres).

## Outcome
<!-- TO DO: what actually came out of it and what changed from the idea. -->

## Hitos
<!--
Una línea por hito: - AAAA-MM-DD — texto
Arreglos (van a "Problemas que resolví"): - AAAA-MM-DD — [arreglo] problema → causa → arreglo (≤ 220 caracteres)
-->

## Milestones
<!--
One line per milestone: - AAAA-MM-DD — text
Fixes: - AAAA-MM-DD — [fix] problem → cause → fix (≤ 220 characters)
-->
