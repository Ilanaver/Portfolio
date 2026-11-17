# Bitácora

Una entrada por tarea o sesión de trabajo, la más nueva arriba. Fechas de Argentina.
El título de cada entrada es PÚBLICO (aparece en el portfolio en español); el cuerpo no.

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
