# Portfolio / CV web de Ilán

Sitio estático bilingüe (ES/EN) con los proyectos de Ilán, hecho con React + Vite + Tailwind.
En producción: https://portfolio-eight-blond-udezm8x9wj.vercel.app

- `/es/` y `/en/`: inicio con proyectos, problemas resueltos, estudios, stack y contacto.
- `/es/p/<slug>/` y `/en/p/<slug>/`: página propia de cada proyecto.
- El botón "Descargar CV" imprime el inicio como CV (A4).

Los datos viven en `src/datos/` (en la Fase 1 se cargan a mano; desde la Fase 2 los genera un GitHub Action
leyendo el `PORTFOLIO.md` de cada repo). El diseño completo está en `PLAN.md`, que vive solo en la copia local (no se publica), y el historial en
[BITACORA.md](BITACORA.md).

## Correr en local

```bash
npm install
npm run dev            # http://localhost:5173/es/
npm run dev -- --host  # para abrirlo desde el celular en la misma red Wi-Fi
npm run build          # genera dist/ (incluye las páginas de proyecto)
npm run preview        # sirve dist/
```

Validación de datos (Python):

```bash
python -X utf8 -m venv .venv
.venv/Scripts/python -X utf8 -m pip install -r requirements.txt
.venv/Scripts/python -X utf8 scripts/validar_datos.py
```
