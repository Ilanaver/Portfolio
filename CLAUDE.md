# CLAUDE.md — repo del portfolio

Convenciones de este repo (ver el diseño completo en `PLAN.md`).

## Código
- Variables, funciones y comentarios en castellano.
- Funciones helper chicas, una responsabilidad cada una.
- Python: siempre `python -X utf8` (nunca `python3`); `for` explícitos, sin list/dict comprehensions.
- Front: React + Vite + Tailwind, JavaScript (JSX).

## Textos
- Ningún texto visible queda escrito en un componente: etiquetas, `aria-label`, `alt`, `<title>`, botones y el
  texto de las páginas de redirección salen de `src/i18n/es.json` y `src/i18n/en.json`.
- `es.json` y `en.json` tienen siempre exactamente las mismas claves (`scripts/validar_datos.py` lo verifica).
- Contenido de proyectos: todo texto traducible es `{ "es": "...", "en": "..." | null }`.

## Seguridad y privacidad
- El token de lectura de GitHub vive solo como secret del Action (`GH_TOKEN_LECTURA`), nunca en `src/` ni en
  ningún archivo del repo.
- Repos privados: nunca se publican su nombre de repo, su URL ni texto leído de ellos fuera de lo que Ilán
  aprobó en su `PORTFOLIO.md`. En logs, issues y mensajes se nombran solo por su clave opaca (`priv-xxxxxxxx`).
- Capturas manuales de repos privados: solo con aprobación de Ilán (hash en `imagen.aprobada`). En privados,
  `captura_auto` es `false` por defecto y no se cambia sin su OK.

## Bitácora
- `BITACORA.md` en formato único: `## DD/MM/AAAA — Título` (guion largo), la más nueva arriba, separadas por `---`.
- El título es público: ≤ 100 caracteres, sin nombres de terceros, montos, URLs, secretos ni datos personales.
- Bloques del cuerpo: **Cambios**, **Problema**, **Causa**, **Arreglo**, **Pendiente** (los que correspondan).
- La entrada va en el mismo commit que el cambio.

## Git
- Todo push necesita el OK explícito de Ilán.
