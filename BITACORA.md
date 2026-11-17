# Bitácora

Una entrada por tarea o sesión de trabajo, la más nueva arriba. Fechas de Argentina.
El título de cada entrada es PÚBLICO (aparece en el portfolio en español); el cuerpo no.

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
