# Bitácora

Una entrada por tarea o sesión de trabajo, la más nueva arriba. Fechas de Argentina.
El título de cada entrada es PÚBLICO (aparece en el portfolio en español); el cuerpo no.

---

## 17/11/2026 — Analítica de visitas sin cookies

**Cambios**
- Paso 16: `@vercel/analytics@2.0.1` con `<Analytics />` en la raíz de `App.jsx`, presente en el inicio y en
  las páginas de proyecto. Sin cookies ni banner. En producción carga `/_vercel/insights/script.js`.
- El componente quedó incluido en el commit del paso 12 (`792a81e`), al reescribir `App.jsx`; este paso solo
  verifica el bundle y lo registra.

**Pendiente**
- Activar Web Analytics en el proyecto de Vercel (lo hace Ilán, paso 20). En `npm run preview` el script da
  404: es lo esperado fuera de Vercel.

---

## 17/11/2026 — CV imprimible en A4 desde el inicio, en los dos idiomas

**Cambios**
- Paso 15: `src/impresion.css` (`@media print`, sin capa para ganarle a Tailwind): A4 con márgenes de
  12 × 15 mm, colores en tinta, sin grilla; oculta selector, botones, navegación, filtros, tarjetas,
  capturas y placeholders. Orden del CV: encabezado con correo, GitHub y URL del portfolio en texto; sobre mí;
  estudios; stack en una línea por categoría; proyectos (destacados con descripción y tecnologías, el resto
  en una línea, sin filtros); los 3 problemas más recientes.
- `ProyectosCV` (solo impresión) en `ListaProyectos`; la URL del sitio llega al front con `define`
  (`__SITIO_URL__`).
- Verificado imprimiendo a PDF con Edge headless: ES y EN entran en 1 página A4.

**Problema**
- La primera versión ocupaba 2 páginas (el tercer problema pasaba sola a la segunda).

**Causa**
- Cuerpo a 10 pt con márgenes de 14 × 16 mm.

**Arreglo**
- Cuerpo a 9,5 pt y márgenes de 12 × 15 mm: entra en 1 página en los dos idiomas.

**Pendiente**
- En local la URL del portfolio sale `localhost:4173`; en Vercel toma sola el dominio de producción.

---

## 17/11/2026 — Sección de stack calculada desde los proyectos

**Cambios**
- Paso 14: `Stack` agrupa tecnologías y servicios por categoría (con "Otros" para las que no tienen) y
  muestra cuántos proyectos usan cada una; cada etiqueta lleva a `?tag=<clave>#proyectos` (lista filtrada).
- Chips de filtro más bajos en escritorio (36 px); en celular siguen en 44 px.

---

## 17/11/2026 — Sección "Problemas que resolví" desde los hitos de arreglo

**Cambios**
- Paso 13: `ProblemasResueltos` junta los hitos `arreglo` de todos los proyectos (más nuevos arriba), con el
  proyecto y link a su página. Si el texto tiene la forma "problema → causa → arreglo", se muestra en tres
  renglones rotulados (Problema / Causa / Arreglo, con mayúscula inicial); si no, tal cual. En `/en/` usa los
  Milestones `[fix]` o, si faltan, los Hitos marcados "ES". Si no hay arreglos, la sección y su link en la
  navegación no aparecen.
- Verificado en `/en/`: 6 arreglos de los 3 proyectos, en orden de fecha.

---

## 17/11/2026 — Página propia de cada proyecto con línea de tiempo

**Cambios**
- Paso 12: vista `PaginaProyecto` (volver con el historial si se llegó desde el sitio, captura o placeholder
  grande, ficha técnica, idea original vs. resultado lado a lado en escritorio, línea de tiempo) y
  `LineaDeTiempo` (en `/es/` hitos + bitácora juntos con ancla `#bitacora`; en `/en/` Milestones o Hitos
  marcados, y el enlace "+ N development log entries (in Spanish)").
- `scripts/paginas_proyecto.mjs` (post-build): `dist/<idioma>/p/<slug>/index.html` con `data-vista`,
  `data-slug`, meta propio (title, descripción, OG con su captura o la imagen por defecto, hreflang,
  canonical) y contenido básico pre-renderizado; páginas de redirección para `slugs_anteriores` (meta refresh +
  canonical + noindex + `location.replace` que conserva `?query` y `#ancla` + link visible).
- En desarrollo, el plugin arma `/<idioma>/p/<slug>/` al vuelo con un middleware.
- `main.jsx`/`App.jsx` eligen la vista según `data-vista`.
- Verificado: el build genera 6 páginas; `/en/p/rivot/` muestra la idea original en español con la marca "ES".

**Pendiente**
- Probar una redirección de slug anterior y la bitácora en la línea de tiempo con datos de prueba (paso 18).

---

## 17/11/2026 — Filtros por estado y etiqueta guardados en la URL

**Cambios**
- Paso 11: `Filtros` (chips con `aria-pressed`, 44 px, agrupados por estado y por categoría; barra fija con
  scroll horizontal en celular, en varias líneas en escritorio; contador con `aria-live`; "Limpiar filtros").
  `ListaProyectos` lee los filtros de la URL al cargar, descarta claves inexistentes y escribe con
  `history.replaceState` (`?tag=telegram,vercel&estado=activo`), conservando el `#ancla`.
- Criterio: dentro de etiquetas y dentro de estados, cualquiera de las elegidas (O); entre estado y
  etiquetas, las dos condiciones (Y).
- Verificado en el navegador: `?tag=telegram,inexistente` → 2 proyectos; + Vercel → 3; los cambios quedan en
  la URL; "Limpiar" vuelve a `/es/#proyectos`.

---

## 17/11/2026 — Tarjetas de proyecto con placeholder de ficha técnica

**Cambios**
- Paso 10: `TarjetaProyecto` (toda la tarjeta lleva a la página del proyecto; los links externos quedan por
  encima), `FichaTecnica` con campos rotulados en mono, `PlaceholderCaptura` (16:10, grilla marcada, nombre
  en Plex Mono que se achica según el largo, hasta 4 tecnologías + "+N", estado en la esquina,
  `aria-hidden`), `Captura` lista para WebP 600/1200 con `width`/`height` fijos, `ImagenProyecto` (captura o
  placeholder), `IndicadorEstado`, `Etiqueta`. Los destacados ocupan dos columnas en escritorio.
- `src/lib/filtros.js`: claves de etiqueta, agrupado por categoría con conteo, filtros en la URL.

**Problema**
- Las clases propias de CSS les ganaban a las utilidades de Tailwind (ej. color de links).
- En el placeholder, el nombre y los chips quedaban corridos y la grilla salía gigante.
- Los párrafos de "Sobre mí" salían pegados.

**Causa**
- Los estilos sin capa tienen prioridad sobre `@layer utilities` de Tailwind v4.
- Las unidades `cqi` de un elemento se resuelven contra su contenedor *ancestro*, no contra sí mismo.
- `space-y-*` pierde contra `m-0` de los hijos.

**Arreglo**
- Estilos propios dentro de `@layer components`. Relleno del placeholder en un hijo `placeholder__interior`
  y grilla con porcentajes (16 × 10). `flex flex-col gap-*` en vez de `space-y-*`.

**Pendiente**
- `Captura` se prueba con la primera captura real en la Fase 2 (según el plan).

---

## 17/11/2026 — Meta por idioma, hreflang y cambio de idioma que conserva filtros y ancla

**Cambios**
- Paso 9: plugin `plugins/meta-idioma.js` (`transformIndexHtml`) con `<title>`, descripción, Open Graph,
  `hreflang` es/en/x-default y `canonical` para `/`, `/es/` y `/en/` (`/` canónica a `/es/`); reemplaza los
  textos `{{es:clave}}` de `404.html` y del `<noscript>` de `/`. Helpers compartidos en
  `plugins/meta-comun.js` (también los usará `paginas_proyecto.mjs`).
- La URL del sitio sale de `SITIO_URL` o, en Vercel, de `VERCEL_PROJECT_PRODUCTION_URL` (sin configurar nada).
- Imágenes Open Graph por defecto `public/og-es.png` y `og-en.png` (1200×630), generadas con Edge headless.
- Verificado en el navegador: `/?tag=python#sobre-mi` → `/es/?tag=python#sobre-mi` (navegador en `es-419`);
  el selector lleva a `/en/?tag=python#about` y guarda `idioma=en`.

**Problema**
- El primer build falló: `Falta la clave de traducción: raiz.ir_es`.

**Causa**
- El `<noscript>` de `index.html` usaba claves que no existían en los archivos de traducción.

**Arreglo**
- Pasa a usar `raiz.ir` en cada idioma. El build falla a propósito ante una clave faltante.

---

## 17/11/2026 — Encabezado con selector de idioma, botón de CV y secciones fijas

**Cambios**
- Paso 8: `Encabezado` (nombre, titular, links de correo y GitHub, navegación por secciones con scroll
  horizontal, link "saltar al contenido"), `SelectorIdioma` ES | EN (44 px, `aria-current`), `BotonCV`
  (`window.print()`; si existe `cv_pdf`, descarga el PDF), `SobreMi`, `Estudios`, `Contacto` y `Seccion`
  (anclas por idioma). `TextoIdioma` + `MarcaSoloEspanol` para textos que en `/en/` caen al español.
- `src/lib/textos.js` (texto por idioma con fallback, hitos según §3.4) y `src/lib/url.js` (anclas
  `sobre-mi`↔`about`, etc., ruta en el otro idioma).
- `.claude/launch.json` con los servidores de desarrollo y de vista previa.
- Verificado en el navegador: `/es/` renderiza sin desborde horizontal a 1024 px.

---

## 17/11/2026 — Tokens de diseño de cuaderno de ingeniería, claro y oscuro

**Cambios**
- Paso 7: `src/index.css` con variables de color (papel, tinta, línea, un acento azul, estados) para claro y
  oscuro según el sistema, expuestas a Tailwind con `@theme inline`; IBM Plex Sans (400/500/600) y Mono
  (400/500) auto-hosteadas con Fontsource, solo el subconjunto latino; grilla de fondo de 24 px; clases del
  placeholder 16:10 (tamaños con unidades de contenedor `cqi`), de la línea de tiempo (círculo = hito,
  rombo = arreglo, guion = bitácora) y de la página 404.
- Contraste del texto principal y del acento sobre el fondo ≥ 7:1 en los dos temas.

---

## 17/11/2026 — Datos iniciales: tres proyectos y perfil en ES/EN

**Cambios**
- Paso 5: `src/datos/proyectos.json` a mano con Scanner DCA, Rivot e ibit. Textos ES/EN redactados desde sus
  README y el historial de commits; hitos con arreglos (2 por proyecto); sin imagen (placeholder);
  `slugs_anteriores: []`; claves opacas calculadas local con `gh` (sha256 del id de nodo). Rivot queda a
  propósito sin `Original idea` en inglés para ver el fallback.
- Paso 6: `src/datos/perfil.json` (titular, sobre mí en dos párrafos, estudios, contacto, `cv_pdf: null`).
- `validar_datos.py`: OK.

**Pendiente**
- Para revisar en el checkpoint: todos los textos; las causas de dos arreglos inferidas de los commits (Rivot
  14/10 e ibit 02/08); la fecha de inicio en la UCEMA (puse 2026-03); ibit y Rivot como `activo`; nombre en
  inglés "DCA Scanner".

---

## 17/11/2026 — Esquema de salida y validador de datos

**Cambios**
- Paso 4: `config/esquema_salida.json` (JSON Schema 2020-12, `additionalProperties: false` en todo): textos
  `{es, en}`, clave opaca, `origen`, `ultima_actividad` mensual, `slugs_anteriores`, imagen opcional
  (`manual`/`auto`, archivos por idioma), hitos `hito`/`arreglo`, bitácora solo fecha + título, `cv_pdf`.
  Reglas extra: `terminado` exige `fecha_fin`, `activo` la prohíbe, un repo privado no puede tener
  `links.repo`, un proyecto extra no tiene repo ni bitácora.
- `scripts/validar_datos.py`: esquema + paridad de claves `es.json`/`en.json` + slugs únicos entre actuales y
  anteriores + claves opacas únicas. `requirements.txt` con `jsonschema==4.26.0`.
- Prueba: 10 casos inválidos armados en memoria (link de repo en privado, `terminado` sin fin, campo extra,
  slug anterior que choca, `http://`, cuerpo de bitácora, etc.): los 10 se detectan.

**Pendiente**
- La clave de repos públicos (`pub-` + 8 hex) no está definida en el plan; el esquema la acepta y se confirma
  en la Fase 2.

---

## 17/11/2026 — Textos de interfaz en archivos de traducción ES/EN

**Cambios**
- Paso 3: `src/i18n/es.json` y `en.json` con todas las claves de la interfaz; `crearTraductor(idioma)` con
  interpolación (`{cantidad}` formateado con `Intl.NumberFormat`) y plural `_uno`/`_otros`; clave faltante →
  `[clave]` en desarrollo y español en producción; `IdiomaContexto` + `useIdioma()`; `guardarIdioma()` con
  try/catch. `src/lib/fechas.js` con `Intl.DateTimeFormat` (`es-AR`/`en-US`) en UTC.
- Prueba rápida con `ssrLoadModule` de Vite: plurales, miles (`3.400` / `3,400`) y fechas correctas.

**Problema**
- El script de prueba no encontraba `vite` al correr desde la carpeta temporal.

**Causa**
- Node resuelve paquetes desde la carpeta del script, no desde el directorio actual.

**Arreglo**
- Import con ruta absoluta `file:///…/node_modules/vite`. Solo afecta al script de prueba (no está en el repo).

---

## 17/11/2026 — Proyecto Vite + React + Tailwind con entradas por idioma

**Cambios**
- Paso 2: Vite 8.3.8, React 19.3.1, Tailwind 4.3.5 (`@tailwindcss/vite`), versiones fijas. Entradas `/`,
  `/es/`, `/en/` y `404.html` (con `appType: 'mpa'`); `npm run build` = `vite build` + `paginas_proyecto.mjs`
  (por ahora vacío). `.gitattributes` con `eol=lf` para que Windows no convierta los finales de línea.
- `/` elige idioma con un script en línea (elección guardada → idioma del navegador) y, sin JS, va a `/es/`.

**Pendiente**
- Plugin `meta-idioma` y textos del 404 desde i18n (pasos 3 y 9).

---

## 17/11/2026 — Capturas automáticas desactivadas por defecto en repos privados

**Cambios**
- `PLAN.md` pasa a v5.1: en repos privados `captura_auto` es `false` por defecto. Las capturas de privados
  pasan siempre por la aprobación de Ilán por hash. Actualizados §2.1 (esquema), §2.3 (template), §2.4
  (reglas de capturas), §4.2 (paso 6 del Action) y §7.2 (instrucción para el `CLAUDE.md` global).

**Pendiente**
- ibit es privado y el plan (§7.1, paso 43) prevé su captura automática desde la demo: con el default nuevo
  queda en placeholder salvo que Ilán decida `captura_auto: true` en la Fase 3.

---

## 17/11/2026 — Arranque del repo del portfolio

**Cambios**
- Paso 1 de la Fase 1: `git init` (rama `main`), `.gitignore`, `README.md`, `CLAUDE.md` del repo con las
  convenciones y esta bitácora en formato único.

---
