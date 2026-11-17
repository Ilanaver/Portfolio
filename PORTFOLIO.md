---
# Ficha pública de este repo en el portfolio (formato versión 1, ver plantillas/PORTFOLIO.md).
version: 1
visible: true
# Se publican fecha + título de las entradas de BITACORA.md (solo en /es/). El cuerpo nunca.
mostrar_bitacora: true
nombre: Portfolio y CV
nombre_en: Portfolio and CV
slug: portfolio
slugs_anteriores: []
descripcion: Este sitio. Bilingüe y estático; se actualiza solo leyendo un archivo estándar de cada repo, con capturas y CV en PDF automáticos.
descripcion_en: This site. Bilingual and static; it updates itself by reading a standard file from each repo, with automatic screenshots and a PDF CV.
estado: activo
fecha_inicio: 2026-11-17
destacado: false
tecnologias: [React, Vite, Tailwind, JavaScript, Python, Playwright, pytest]
servicios: [GitHub Actions, Vercel, Telegram]
links:
  # La demo es el propio sitio: el Action saca la captura automática en ES y EN (repo público).
  demo: https://portfolio-eight-blond-udezm8x9wj.vercel.app/
  repo: auto
  otros: []
bitacora:
  archivo: BITACORA.md
  max_entradas: 10
---

## Idea original
Un sitio con mis proyectos y mi CV que no haya que actualizar a mano: cada repo describe su propio proyecto en un
archivo estándar y el sitio se arma solo a partir de eso.

## Original idea
A site with my projects and my CV that doesn't need manual updates: each repo describes its own project in a
standard file and the site builds itself from that.

## Resultado
Un sitio estático en español e inglés, con una página por proyecto, una sección de problemas resueltos y el CV
listo para imprimir. Un GitHub Action lee cada pocas horas el PORTFOLIO.md de cada repo con un token de solo
lectura, saca capturas de las demos, genera el CV en PDF y publica solo si algo cambió. Los repos privados nunca
aparecen por nombre en logs ni avisos.

## Outcome
A static site in Spanish and English, with a page per project, a section on problems I solved and a print-ready
CV. A GitHub Action reads every repo's PORTFOLIO.md every few hours with a read-only token, takes screenshots of
the demos, builds the PDF CV and publishes only when something changed. Private repos never show up by name in
logs or alerts.

## Hitos
- 2026-11-17 — Primera versión publicada: sitio bilingüe con tres proyectos cargados a mano.
- 2026-11-17 — [arreglo] Inicio lento en celular (Lighthouse 91) → el contenido se dibujaba recién al cargar React → páginas pre-renderizadas en el build y CSS en línea: 98–100.

## Milestones
- 2026-11-17 — First version live: bilingual site with three projects loaded by hand.
- 2026-11-17 — [fix] Slow home page on mobile (Lighthouse 91) → content only rendered once React loaded → pages pre-rendered at build time and inline CSS: 98–100.
