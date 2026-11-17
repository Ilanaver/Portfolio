# Bitácora

Una entrada por tarea o sesión de trabajo, la más nueva arriba. Fechas de Argentina.
El título de cada entrada es PÚBLICO (aparece en el portfolio en español); el cuerpo no.

---

## 17/11/2026 — Catálogo de etiquetas y normalización de tecnologías

**Cambios**
- Paso 26: `config/etiquetas.yml` con 43 etiquetas (las 19 publicadas hoy más el stack de los repos de §7.1:
  C#, SQL, Next.js, Node.js, Neon, Playwright, etc.), cada una con categoría y alias. `categoria: null` =
  conocida pero sin categoría (Google Calendar y pytest, como hoy en el sitio).
- `scripts/portfolio/etiquetas.py`: comparación sin mayúsculas ni espacios repetidos, sin repetidos por nombre
  canónico; fuera del catálogo → tal cual y sin categoría, y se devuelve aparte para la advertencia. El catálogo
  falla si un alias se repite o una categoría no existe.
- Test de que las 19 etiquetas publicadas hoy salen idénticas al normalizarlas. `pytest`: 51 OK.

---

## 17/11/2026 — Parser de bitácoras que solo lee fecha y título

**Cambios**
- Paso 25: `scripts/portfolio/bitacora.py`. Solo mira encabezados `##`/`###` (fuera de bloques de código) que
  empiezan con fecha válida: formato único `DD/MM/AAAA — Título`, A `DD/MM/AAAA (día)` (sin título → no se
  publica), B `AAAA-MM-DD — Título` y C `### AAAA-MM-DD — Título`. Al título solo se le quita el formato
  Markdown y se recorta a 100 caracteres. Más nuevas primero, hasta `max_entradas`. Bitácora sin títulos →
  advertencia `bitacora_sin_titulos`.
- Fixtures inventados de los 4 formatos con marcas `CUERPO_*`, un token falso, una URL y un monto en el cuerpo;
  test de que nada de eso aparece en la salida. `pytest`: 46 OK.

---

## 17/11/2026 — Plantillas bilingües de PORTFOLIO.md y BITACORA.md

**Cambios**
- Paso 24: `plantillas/PORTFOLIO.md` con los comentarios de §2.3 (`visible: false`, `mostrar_bitacora: false`,
  `slugs_anteriores: []`, `captura_auto` comentado con la regla de privados, `imagen` comentada con el aviso de
  aprobación por hash) y las secciones en inglés incluidas y vacías. `plantillas/BITACORA.md` en formato único.
- `test_plantillas.py`: el template completado valida con los defaults seguros; sin completar también parsea; el
  template de bitácora no produce entradas.

---

## 17/11/2026 — Lectura y validación del archivo estándar PORTFOLIO.md

**Cambios**
- Paso 23: `scripts/portfolio/archivo_estandar.py`. Frontmatter YAML con un cargador que deja las fechas como
  texto; validación contra `esquema_portfolio.json`; secciones `## Idea original`/`## Original idea`,
  `## Resultado`/`## Outcome`, `## Hitos`/`## Milestones` (cualquier otra se ignora); hitos
  `- AAAA-MM-DD — texto` con marca `[arreglo]`/`[fix]`, más nuevos primero; comentarios HTML fuera.
- Defaults: `slug` desde el nombre del repo (minúsculas, lo que no sea `[a-z0-9]` → guion), `fecha_inicio` =
  `createdAt`, `nombre_en` = `nombre`; repo privado → `links.repo` null y `captura_auto` false salvo valor
  explícito.
- Inglés faltante = advertencia por tipo (`falta_ingles:descripcion_en`, etc.), sin texto del repo. Errores con
  tipo `no_valida` y detalle aparte (el detalle solo se muestra en local o en repos públicos).
- Tests: válido completo, sin inglés, privado, los 7 inválidos del plan y 5 más (sin frontmatter, sin cierre,
  fecha imposible, sin idea original, YAML roto). `pytest`: 34 OK.

---

## 17/11/2026 — Esquema del archivo estándar PORTFOLIO.md y de proyectos sin repo

**Cambios**
- Paso 22: `config/esquema_portfolio.json` (JSON Schema 2020-12) con dos definiciones: `portfolio_repo` y
  `proyecto_extra`. `additionalProperties: false` en todo (un campo mal escrito es error, no se ignora). Campos
  `_en` opcionales, `captura_auto`, `imagen.*` opcional (`aprobada` = 12 hex), `slugs_anteriores`, `bitacora.*`;
  `terminado` exige `fecha_fin` y `activo` la prohíbe; rutas relativas sin `/` inicial ni `..`.
- Proyectos sin repo (§2.5): `slug`, `fecha_inicio` y `ultima_actividad` obligatorios, `links.repo` solo `null`,
  `mostrar_bitacora` solo `false`, sin `bitacora` y con la imagen dentro de `imagenes/`.
- Las reglas que dependen del contexto (privado/público, slug actual dentro de `slugs_anteriores`, `aprobada`
  obligatoria en privados) quedan para `archivo_estandar.py`.
- `test_esquema_portfolio.py`: 2 válidos y 17 inválidos. `pytest`: 20 OK.

---

## 17/11/2026 — Arranque de la Fase 2: paquete de scripts y pytest

**Cambios**
- Paso 21: paquete `scripts/portfolio/` (rutas base del repo), `scripts/tests/` con una prueba mínima y
  `pytest.ini` (`pythonpath = scripts`). `requirements.txt` completo con versiones fijas (jsonschema, PyYAML,
  requests, Pillow, playwright) y `requirements-dev.txt` que suma pytest (para `verificar.yml`).
- `pytest`: 1 test OK.

---

## 17/11/2026 — Fase 1 verificada en producción

**Cambios**
- Deploy de `a20a8db` en READY. En producción: `/es/` y `/en/p/rivot/` sirven title, descripción, Open Graph
  (con imagen 1200×630), `twitter:card`, canonical y hreflang es/en/x-default con la URL definitiva, y el HTML
  pre-renderizado (`<h1>` presente sin JS). `/_vercel/insights/script.js` responde 200 y registra la vista
  (`/_vercel/insights/view` 200); consola del navegador sin mensajes.
- Rutas: `/` 200, `/es` → 308 a `/es/`, páginas de proyecto 200, imágenes OG y favicon 200, ruta inexistente →
  404 bilingüe, `/README.md` y `src/datos/…` 404 (no se publican). `/assets/` con
  `Cache-Control: public, max-age=31536000, immutable`.
- Lighthouse móvil sobre producción: performance `/` 99, `/es/` 99, `/en/` 98, `/es/p/scanner-dca/` 100,
  `/en/p/rivot/` 98; accesibilidad, buenas prácticas y SEO 100 en las cinco.
- CV impreso desde producción: 1 página A4 en ES y en EN, con la URL del sitio.

**Pendiente**
- Revisión de Ilán del checkpoint antes de arrancar la Fase 2. Esta entrada sube en el próximo push.

---

## 17/11/2026 — Sitio publicado en Vercel con su URL definitiva

**Cambios**
- Paso 20 cerrado: Ilán conectó el repo a Vercel y activó Web Analytics (incluido en Hobby sin costo). El
  primer deploy de producción (`ae8dc98`) quedó en estado READY.
- URL base fija en `plugins/meta-comun.js` (`URL_PRODUCCION`), usada en canonical, hreflang, Open Graph y en la
  URL que muestra el CV impreso. Se confirmó con la API de Vercel que es el dominio de producción del proyecto
  (no la URL de un deploy). Se puede forzar otra con `SITIO_URL`. Antes se tomaba de
  `VERCEL_PROJECT_PRODUCTION_URL` y en local salía `localhost:4173`.
- README con el link al sitio.
- `validar_datos.py` OK; `npm run build` OK, sin `localhost` en el HTML generado.

---

## 17/11/2026 — Primer push del portfolio a GitHub

**Cambios**
- Paso 20 (parte de Claude): remote `origin` y primer push de `main` al repo público (raíz..`ae8dc98`,
  21 commits). Antes del push: `validar_datos.py` OK y `npm run build` OK (2 inicios y 6 páginas de proyecto
  pre-renderizados).

**Pendiente**
- Ilán: conectar Vercel y activar Web Analytics (paso 20). Después, checkpoint de la Fase 1 con el link.
- Esta entrada sube en el próximo push.

---

## 17/11/2026 — Repo preparado para publicarse: plan solo local y autor sin mail personal

**Problema**
- El repo de GitHub es público y `PLAN.md` (commiteado desde el primer commit) nombra repos privados y
  detalles internos. Los commits tenían como autor un mail personal.

**Causa**
- El plan se escribió como documento interno y se versionó junto con el código; el autor salía de la
  configuración global de git.

**Arreglo**
- Con OK de Ilán, antes del primer push: `PLAN.md` sale de todo el historial (`git filter-branch
  --index-filter`), queda en `.gitignore` y sigue en la copia local. Autor y committer de los 20 commits pasan
  a la dirección noreply de GitHub, que queda configurada solo en este repo. README y CLAUDE.md aclaran que el
  plan es local. Respaldo del historial anterior en un bundle fuera del repo.

---

## 17/11/2026 — Inicio y páginas de proyecto pre-renderizados en el build

**Cambios**
- Desvío aprobado por Ilán (PLAN v5.2): `src/entrada-servidor.jsx` con `renderToString`; `npm run build` suma
  `vite build --ssr src/entrada-servidor.jsx` (salida en `dist-servidor/`, ignorada por git) y
  `paginas_proyecto.mjs` escribe el HTML completo del inicio (ES y EN) y de las 6 páginas de proyecto dentro de
  `<div id="root">`. `main.jsx` hidrata con `hydrateRoot` si hay HTML previo y usa `createRoot` en desarrollo.
- Para que servidor y cliente coincidan: el selector de idioma toma sus rutas del contexto (antes leía
  `window.location`) y la lista de proyectos arranca sin filtros y aplica los de la URL en un `useEffect`.
- `vite.config.js` separa las opciones del build del cliente y del de servidor.
- Se quitó el contenido básico pre-renderizado de las páginas de proyecto: ahora va la página entera.
- CSS en línea (`<style>`) en el inicio, las páginas de proyecto y el 404.
- Verificado sobre `dist/`: sin errores de hidratación en consola en `/es/`, `/en/` (también con
  `?estado=activo&tag=python`) y en páginas de proyecto de los dos idiomas; las fechas de `Intl` salen iguales
  en Node y en el navegador ("sept 2026", "Sep 2026"); los filtros de la URL se aplican después de hidratar. El
  modo desarrollo sigue funcionando.
- Lighthouse móvil (vista previa local): `/` 95–96 (tres corridas), `/es/` 97, `/en/` 98, `/es/p/scanner-dca/`
  97, `/en/p/rivot/` 97 en performance; accesibilidad 100 y SEO 100 en todas.

**Problema**
- Solo con el pre-renderizado, `/` daba 93 y el resto 95–96.

**Causa**
- Dos hojas CSS bloqueaban el primer pintado (~1 s estimado) y `/` suma el salto por idioma a `/es/` o `/en/`
  (~0,6 s), que el plan pide así.

**Arreglo**
- CSS en línea en el post-build. El salto de `/` queda como está.

**Pendiente**
- La única consola con errores es el 404 de `/_vercel/insights/script.js`, esperado fuera de Vercel.

---

## 17/11/2026 — Sitio revisado desde un Android real

**Cambios**
- Paso 19 cerrado: Ilán probó el sitio desde su Android por el túnel HTTPS y anda bien.
- Túnel de Cloudflare y vista previa de `127.0.0.1:4174` apagados (los procesos `cloudflared` y `vite preview`
  quedaban vivos al cortar la tarea; se cerraron a mano y se verificó que no queda nada escuchando).

---

## 17/11/2026 — Túnel HTTPS temporal para probar el sitio desde el celular

**Problema**
- Desde el Android no abría `http://10.201.1.189:5174/es/`.

**Causa**
- No era el servidor ni el firewall: Vite escuchaba en `::` (IPv4 e IPv6), respondía 200 por la IP de LAN
  desde la PC, y el Firewall de Windows permite Node.js en red Pública sin reglas de bloqueo. La red es el
  Wi-Fi de la facultad, que casi seguro aísla a los clientes entre sí (AP isolation).

**Arreglo**
- Túnel temporal de Cloudflare (`npx cloudflared tunnel --url …`, sin cuenta) hacia `vite preview` de `dist/`
  en `127.0.0.1:4174`, **no** hacia el servidor de desarrollo: ese sirve cualquier archivo del proyecto
  (`/PLAN.md`, `/BITACORA.md`, `.revision/` daban 200) y el túnel lo habría hecho público. Por el túnel,
  `/es/` y `/en/p/rivot/` dan 200; `/PLAN.md`, `/BITACORA.md`, `.revision/…` y `src/datos/…` dan 404.
- `vite.config.js`: `preview.allowedHosts: ['.trycloudflare.com']` para que la vista previa acepte ese host.

**Pendiente**
- El túnel muestra el último `npm run build`, no los cambios en vivo. Se apaga cuando termine la prueba.

---

## 17/11/2026 — Servidor de desarrollo accesible desde la red local para probar en celular

**Cambios**
- Paso 19 (preparación): configuración `portfolio-dev-red` en `.claude/launch.json` (`vite --host`, puerto
  5174) para abrir el sitio desde un Android en la misma red Wi-Fi. Material de revisión del checkpoint
  (capturas, CV impreso, textos) en `.revision/`, fuera del repo.

**Pendiente**
- Que Ilán pruebe desde su Android y confirme (el paso 19 queda abierto hasta entonces).

---

## 17/11/2026 — Caché por carpeta en Vercel y build completo verificado

**Cambios**
- Paso 18: `vercel.json` con framework Vite, `npm run build`, salida `dist`, `trailingSlash: true` y caché por
  carpeta: `/assets/` 1 año inmutable; `/proyectos/` 1 día + `stale-while-revalidate` de 7 días; `/cv/` sin
  caché (revalida siempre).
- Verificación del build servido desde `dist/` con un slug anterior de prueba (`slug-de-prueba`) y 2 entradas
  de bitácora de prueba en Scanner DCA: `/es/p/slug-de-prueba/?tag=x#bitacora` → `/es/p/scanner-dca/?tag=x#bitacora`
  y `/en/p/slug-de-prueba/?a=1#y` → `/en/p/scanner-dca/?a=1#y`; en `/es/` la línea de tiempo mezcla hitos y
  bitácora con ancla `#bitacora`; en `/en/` aparece "+ 2 development log entries (in Spanish)" con link a
  `/es/p/scanner-dca/#bitacora`; una ruta inexistente da 404 y `404.html` tiene los dos idiomas. Los datos de
  prueba se sacaron y se volvió a generar `dist/` (0 redirecciones).
- Lighthouse móvil (vista previa local): accesibilidad 100, SEO 100 y buenas prácticas 96 en `/es/`, `/en/` y
  `/es/p/scanner-dca/`; performance 91 / 92 / 98.
- Selector de idioma: el nombre accesible pasa a "ES (Español)" en vez de `aria-label="Español"`
  (Lighthouse marcaba que no coincidía con el texto visible).

**Problema**
- Performance del inicio en 91–92, debajo del objetivo de 95 del plan (§5.8).

**Causa**
- El inicio se dibuja recién cuando carga el JS (~84 kB gzip con React): primer pintado en 2,2 s con la red
  móvil simulada.

**Pendiente**
- Decisión de Ilán: pre-renderizar el inicio y las páginas de proyecto en el build (`react-dom/server`) para
  que el HTML llegue armado. Es un desvío del plan (§5.1 pide solo contenido básico en las páginas de
  proyecto), así que no se hizo sin su OK.

---

## 17/11/2026 — Ajustes de celular y accesibilidad en inicio y páginas de proyecto

**Cambios**
- Paso 17: revisión a 360 y 412 px en `/es/`, `/en/` y tres páginas de proyecto en los dos idiomas: sin scroll
  horizontal (`scrollWidth` = 360) y sin elementos que se salgan, salvo la barra de filtros, que scrollea a
  propósito.
- Táctiles: el nombre en el encabezado de las páginas de proyecto pasa a 44 px (medía 31). Los nombres de las
  tarjetas miden menos, pero el área táctil es la tarjeta entera.
- Placeholder con nombres largos: piso de letra 14 px (era 18); con 48 y 63 caracteres entra en 2 líneas sin
  cortarse.
- Accesibilidad: un `h1` por página y `h2`/`h3` en orden; foco visible de 2 px; `lang="es"` en todo texto que
  cae al español en `/en/`; `aria-pressed` en filtros, `aria-current` en el idioma activo, `aria-live` en el
  contador; placeholder y marcadores decorativos con `aria-hidden`; contraste ≥ 7:1 en texto principal.

**Problema**
- Las capturas de Edge headless a 360/412 px salían cortadas a la derecha y una salió en blanco.

**Causa**
- Edge headless no baja de ~500 px de ancho de ventana. La captura en blanco coincidió con el servidor de
  desarrollo recargando por un cambio de datos.

**Arreglo**
- Capturas con la página dentro de un iframe del ancho pedido; las mediciones se hicieron en el navegador
  integrado con el viewport emulado a 360 px.

**Pendiente**
- Prueba real desde el Android de Ilán (paso 19).

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
