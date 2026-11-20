---
version: 1
visible: true
mostrar_bitacora: false
nombre: Videos faceless
nombre_en: Faceless videos
slug: videos-faceless
slugs_anteriores: []
descripcion: Convierte un guion en un video vertical animado con voz, subtítulos y música, y arma cada semana un lote de Shorts con agentes de IA.
descripcion_en: Turns a script into an animated vertical video with voice, captions and music, and builds a weekly batch of Shorts with AI agents.
estado: activo
fecha_inicio: 2026-11-04
ultima_actividad: 2026-11
destacado: false
tecnologias: [Python, TypeScript, React, Remotion, FFmpeg, faster-whisper, edge-tts, Kokoro, pytest]
servicios: [YouTube Data API, Claude Code]
links:
  demo: null
  repo: null
  otros: []
---

## Idea original
Un comando que convierta un guion en un video vertical listo para subir, sin mostrar la cara y sin editar a mano.

## Original idea
A single command that turns a script into a vertical video ready to upload, without showing my face or editing by hand.

## Resultado
Quedó un pipeline local: voz generada o grabada, recorte de silencios, transcripción con faster-whisper para
sincronizar los subtítulos palabra por palabra, render con Remotion y audio normalizado a -14 LUFS. Encima corre un
lote semanal de Shorts en inglés y en español: agentes que investigan, escriben y revisan cada guion con fuentes,
controles automáticos sobre el video renderizado y publicación programada en YouTube después de mi aprobación.

## Outcome
It became a local pipeline: generated or recorded voice, silence trimming, faster-whisper transcription to sync
captions word by word, rendering with Remotion and audio normalized to -14 LUFS. On top of it runs a weekly batch of
Shorts in English and Spanish: agents that research, write and review each script with sources, automatic checks on
the rendered video and scheduled publishing on YouTube after my approval.

## Hitos
- 2026-11-04 — Primera versión: de un guion JSON a un video vertical 1080×1920 con voz, subtítulos y música.
- 2026-11-05 — Lote semanal con agentes de investigación, guion y revisión, con aprobación antes de producir.
- 2026-11-06 — Publicador de YouTube: los videos aprobados se suben y se programan solos.
- 2026-11-08 — [arreglo] Datos falsos en guiones → la hoja de fuentes citaba de más (un año de nota como año del estudio) → el investigador no puede afirmar más que la fuente.
- 2026-11-15 — Control de la voz antes del render: se transcribe y se compara con el guion, y si no coincide, frena.

## Milestones
- 2026-11-04 — First version: from a JSON script to a 1080×1920 vertical video with voice, captions and music.
- 2026-11-05 — Weekly batch with research, scriptwriting and review agents, with approval before production.
- 2026-11-06 — YouTube publisher: approved videos are uploaded and scheduled automatically.
- 2026-11-08 — [fix] False facts in scripts → the source sheet overstated its sources (an article's year taken as the study's year) → the researcher can't claim more than the source.
- 2026-11-15 — Voice check before rendering: it is transcribed and compared with the script, and it stops if they don't match.
