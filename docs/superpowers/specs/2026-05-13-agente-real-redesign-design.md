# Rediseño visual del Agente Real (Agente_Real_CRM.html)

**Fecha:** 2026-05-13
**Autor:** Pablo Tapias (con asistencia de Claude Code)
**Estado:** Spec aprobado, pendiente de plan de implementación
**Repo base:** [`encuentra-tu-primer-empleado-ia`](https://github.com/ptapias/encuentra-tu-primer-empleado-ia)
**Commit validado de partida:** `ec1d312`

---

## 1. Objetivo

Rehacer el frontend público (`Agente_Real_CRM.html`) con el sistema editorial dark de la marca **IA al Día**, manteniendo lógica, endpoints, persistencia y backend intactos. La meta es elevar la sensación de producto (estética premium, animaciones contenidas, claridad jerárquica) sin tocar la lógica del agente conversacional ni el CRM.

Lo que cambia: tokens visuales, tipografía, layout, starter, superficie de chat, sidebar, email-gate, render del informe, y todos los estados de espera/error.

Lo que no cambia: prompts del agente, fases del discovery, scoring, persistencia SQLite/JSONL, webhook CRM, despliegue VPS, prototipos antiguos, dashboard interno, página de privacidad.

## 2. Constraints (decisiones ya cerradas)

| Decisión | Valor |
|---|---|
| Alcance de archivos frontend | Solo `Agente_Real_CRM.html`. Quedan fuera: `CRM_Dashboard.html`, `PRIVACY_BETA.html`, `Prototipo_Conversacional.html`, `Prototipo_Diagnostico.html`. |
| Ambición de animaciones | Editorial restraint: CSS transitions + IntersectionObserver. Sin librería de motion. Sin spring physics. |
| Profundidad de cambio | Re-skin completo + reorganización del starter. El resto del markup conserva IDs cuando es posible; cuando no, se actualizan los tests. |
| Marca visible | "IA AL DÍA" en top frame y footer. Cero referencias a "TPEIA · S2" del CSS original. |
| Tests | Se actualizan los tests de navegador del repo (`test_public_ui_flow.py`, `test_public_report_flow.py`, `test_session_restore_flow.py`) cuando un selector o texto cambia. No se ocultan bloques solo para preservarlos. |
| Arquitectura | Mantiene single-file vanilla HTML/CSS/JS. Sin build step. Sin framework. |
| Cambios al backend | Aditivos solamente. Exponer `queue_position` y `eta_seconds` en respuestas 503. Endpoint opcional `POST /api/notify-when-free`. |

## 3. Sistema de diseño

### 3.1 Paleta

Mapeo de la paleta de IA al Día sobre el sistema editorial dark:

| Token CSS | Hex | Origen | Uso |
|---|---|---|---|
| `--bg-deep` | `#06081A` | Slide system (sin cambios) | Lienzo más profundo, fondo del `<body>` antes de hidratar |
| `--bg` | `#0A0E26` | Slide system | Lienzo principal del shell |
| `--bg-warm` | `#0E1331` | Slide system | Variante para mensajes del usuario y card de "agente ocupado" |
| `--bg-elev` | `#15214B` | **Brand IA al Día** | Cards, chat bubbles del agente, composer |
| `--bg-card` | `#161E45` | Slide system | Variante elevada para overlays puntuales |
| `--ink` | `#F4EFE3` | Slide system (cream) | Texto principal y display |
| `--ink-soft` | `#D9D3C2` | Slide system | Body largo (contraste 13:1 sobre `--bg`, AAA) |
| `--ink-muted` | `#75747E` | **Brand IA al Día** | Texto secundario ≥18px y labels mono |
| `--ink-faint` | `#555C82` | Slide system | Watermarks, counters, ancla temporal |
| `--rule` | `rgba(160,170,210,0.14)` | Slide system | Bordes de cards, separadores tenues |
| `--rule-strong` | `rgba(160,170,210,0.28)` | Slide system | Reglas activas, separadores prominentes |
| `--rule-warm` | `#938582` (alpha 0.20) | **Brand IA al Día** | Reglas cálidas ocasionales y watermark de marca |
| `--rule-cyan` | `rgba(4,151,225,0.45)` | Slide system | Slash-motif diagonal |
| `--cyan` | `#0497E1` | **Brand IA al Día** (idéntico al slide) | Acento primario, focus rings, barras de progreso |
| `--cyan-deep` | `#048BCD` | **Brand IA al Día** | Hover/active de CTAs |
| `--cyan-2` | `#38C0FF` | Slide system | Highlights tipográficos y estados activos |
| `--cyan-ink` | `#7CD7FF` | Slide system | Texto sobre superficie cyan |
| `--proceed` | `#5EE39A` | Slide system | Verde de "trust" y trust-signals positivos |
| `--refine` | `#F4C141` | Slide system | Avisos amarillos (cola, rate-limit) |
| `--park` | `#F08484` | Slide system | Errores críticos (IA caída, email inválido) |

**Reglas de contraste:**
- `--cyan-2` solo en tipografía ≥18px o iconografía. Nunca para body largo.
- `--ink-muted` (`#75747E`) solo en texto ≥18px o mono labels. Para body uso `--ink-soft`.
- Focus ring: `outline: 2px solid var(--cyan-2); outline-offset: 2px`.

### 3.2 Tipografía

Tres familias vía Google Fonts con `font-display: swap`:

- **Libre Baskerville** — display (hero, titulares de informe, frases-fuerza del agente cortas).
- **IBM Plex Sans** — UI y body por defecto.
- **IBM Plex Mono** — eyebrows, labels, counters, kbd, statuses técnicos.

**Anti-FOUT:** subset crítico (glifos del hero) de Libre Baskerville inline como `@font-face` base64 woff2 dentro del `<head>`. Permite que el primer paint ya renderice el título con la fuente correcta. El resto carga con swap normal.

**Escala fluida** (reescritura de los tokens `--t-*` del CSS slide a `clamp()`):

| Token | Slide deck | Web app |
|---|---|---|
| `--t-mega` | 132px | `clamp(56px, 9vw, 132px)` |
| `--t-cover` | 118px | `clamp(48px, 8vw, 96px)` |
| `--t-title` | 96px | `clamp(40px, 6vw, 72px)` |
| `--t-h2` | 64px | `clamp(32px, 4.5vw, 48px)` |
| `--t-sub` | 44px | `clamp(22px, 2.6vw, 32px)` |
| `--t-lead` | 38px | `clamp(18px, 2.2vw, 22px)` |
| `--t-body` | 30px | `clamp(15px, 1.6vw, 18px)` |
| `--t-small` | 26px | `clamp(13px, 1.4vw, 15px)` |
| `--t-eyebrow` | 18px | `clamp(11px, 1vw, 13px)` |

### 3.3 Motivos visuales

- **Slash diagonal** (`.slash-motif` del CSS, opacidad 0.5): ambient detrás del título del starter y como decoración del separador entre fases. Se anima opacity 0→0.5 con delay 600ms al cargar; sin movimiento continuo.
- **Counters** estilo deck en footers de sección (`01 / 02 / 03 / 04`) — corresponden a las cuatro fases UI: starter, chat, email-gate, informe.
- **Marca "IA AL DÍA / "** en footer-right de cada vista, con slash final como mini-mark de marca.

### 3.4 Anti-flash

```html
<style>body{background:#06081A;color:#F4EFE3;margin:0;}</style>
```
inline en `<head>` antes del bloque principal de CSS. Garantiza canvas dark desde el frame 1, evita destello blanco en navegadores que retrasan el CSS principal.

## 4. Layout macro

Estructura general que se mantiene a través de todas las fases (starter → chat → email-gate → informe):

```
┌────────────────────────────────────────────────────────────────┐
│ IA AL DÍA · DISCOVERY · 13 MAY · 14:32   FASE 02 / 04 │ GUARDADO HACE 8s │
├────────────────────────┬───────────────────────────────────────┤
│                        │                                       │
│   [sidebar contextual] │   [main: cambia según fase]           │
│                        │                                       │
├────────────────────────┴───────────────────────────────────────┤
│  01                                                IA AL DÍA / │
└────────────────────────────────────────────────────────────────┘
```

**Top frame:**
- Izquierda mono `--ink-faint`: `IA AL DÍA · DISCOVERY · DD MMM · HH:MM` (anclaje temporal fijo al iniciar sesión, no actualiza).
- Centro: `progress-line` horizontal de 4 nodos con la fase activa en `--cyan-2`.
- Derecha: status de guardado `GUARDADO HACE Ns` mono `--ink-faint` opacity 0.6 cuando hay sync con backend; o `RECONECTANDO ▍` mono `--cyan` cuando hay reconexión silenciosa.

**Footer fijo en cada vista:**
- Izquierda: counter `01 / 02 / 03 / 04` según la fase visible (decimal-leading-zero).
- Derecha: `IA AL DÍA /` mono `--ink-faint`.

**Sidebar izquierdo** (~420px en desktop):
- Eyebrow mono (cambia por fase).
- Título display (cambia por fase).
- Subtítulo italic `lead`.
- Contenido contextual a la fase (CTA en starter; panel "Lo que estoy entendiendo" en chat; preview de informe en email-gate; índice del informe en fase de informe).

**Mobile (<800px):**
- Sidebar colapsa a tira superior de 2 líneas (eyebrow + título corto).
- Panel "Lo que estoy entendiendo" se convierte en bottom sheet con tira de 1 línea siempre visible (eyebrow mono + FOCO actual). Tap para expandir.
- Composer usa `dvh` (no `vh`) para gestionar correctamente el teclado virtual de iOS.
- Tap targets ≥ 44×44px.
- Voz promovida: el botón mic se vuelve primario y ENVIAR secundario.

## 5. Fase 01 — Starter

Composición editorial de tres beats verticales en una sola pantalla (sin scroll obligado en desktop):

1. Eyebrow mono cyan: `DISCOVERY GRATUITO · 7-10 MIN`.
2. Título-fuerza display Libre Baskerville (~3 líneas, `--t-cover`): *"¿Dónde se te escapa tiempo, dinero o clientes?"*
3. Lead italic `--ink-soft`: *"Una sesión consultiva con un agente que escucha, repregunta y separa automatizaciones útiles de ideas bonitas que todavía no toca construir."*
4. CTA primaria `.chip.cyan` agrandada con flecha: **"Empezar conversación →"**. Junto al CTA, mini-tag mono *"MEJOR CON MICRO"* con dot cyan.
5. Bajo el CTA, link mono pequeño: *"ver un informe de muestra (2 min)"* → abre un sample del informe en modal editorial.
6. Regla `.hr.strong` horizontal.
7. `progress-line` horizontal de 3 nodos en segunda persona:
   - `01 / CUÉNTAME UNA ESCENA` — *"Una situación reciente donde algo se acumuló, se retrasó o se quedó sin responder."*
   - `02 / YO EXTRAIGO EL PATRÓN` — *"Convierto tu relato en señales y procesos repetibles."*
   - `03 / TE ENTREGO UN PLAN` — *"Empleado IA recomendado, riesgos, primer paso, plan de 7 y 30 días."*

**Sidebar en starter:**
- Eyebrow: `01 / DISCOVERY`.
- Título: *"Encuentra tu primer empleado IA"* (display).
- Lead italic.
- CTA secundaria (espejo del primario, opcional para mobile).
- Panel "Qué recibirás" como `.card.hollow` con 3 ítems.

**Bloques eliminados** vs. versión actual:
- `diagnostic-preview` (preview de diálogo en 3 turnos).
- `live-map` (mapa de 3 filas Entrada/Decisión/IA viable).
- `signal-line` (3 líneas numeradas con análisis del agente).
- `starter-pill` triplo horizontal.
- `process-strip` (3 cards de Detecta/Prioriza/Entrega).

**Animación de entrada:**
- t=0: top frame fade-up (200ms).
- t=120: eyebrow fade-up.
- t=240: título split por línea, cada línea fade-up + slide-up 8px, 60ms stagger.
- t=600: lead fade.
- t=800: CTA + micro-tag fade.
- t=1000: `.hr.strong` se expande de 0% a 100% width (400ms).
- t=1100: 3 nodos del progress-line con stagger 80ms.
- t=1300: slash-motif aparece detrás (opacity 0→0.5 en 400ms).

Toda la curva: `cubic-bezier(0.2, 0.8, 0.2, 1)`, duración 400-500ms. Si `prefers-reduced-motion: reduce`, solo opacity, sin transforms.

## 6. Fase 02 — Chat

### 6.1 Mensajes

**Cambio fundamental respecto al diseño anterior:** los mensajes normales no llevan card con borde. Solo tipografía y aire los separa.

- **Agente:** tipografía dual.
  - Respuestas cortas (≤120 chars): Libre Baskerville 19px en `--ink`, alineado al margen izquierdo, line-height 1.3.
  - Respuestas largas: IBM Plex Sans 17px en `--ink-soft`, line-height 1.5.
  - Sin borde, sin caja.
- **Usuario:** IBM Plex Sans 17px `--ink-soft`, alineado a la derecha, max-width 70%, sin caja.
- **Separador entre turnos:** `--rule` 1px horizontal de 32px de ancho, centrado.
- **Etiquetas:** mono `--ink-muted` 13px letterspaced (`AGENTE` / `TÚ`) solo en el primer turno de cada interlocutor. Después, el patrón visual basta.

**Estados especiales con card (única excepción):** "agente pensando", "agente en cola", error de IA, restauración de sesión. Estos sí llevan `.card` con borde para destacar del flujo normal.

### 6.2 Edit de respuesta del usuario

- Desktop: hover sobre un mensaje propio → `.kbd` "REESCRIBIR" aparece en la esquina superior derecha del mensaje.
- Mobile: long-press 400ms.
- Click → ese mensaje vuelve al composer; el chat hace rewind hasta ese punto; la sesión backend se trunca aceptando un campo opcional `rewind_to_turn` (entero, índice del turno a conservar inclusive) en el body de `/api/chat`. El servidor descarta turnos posteriores antes de generar la respuesta. Aditivo: si el campo no llega, el comportamiento actual no cambia.

### 6.3 Composer

- `<textarea>` sin borde, fondo `--bg-elev`, placeholder italic en `--ink-muted`.
- Icono mic a la derecha del textarea (SVG inline).
- Botón ENVIAR como `.chip.cyan` grande abajo-derecha de la card composer.
- Ghost text mono `--ink-muted` 12px debajo del composer **solo en el primer turno**: *"⏎ enviar · ⇧⏎ línea nueva"*. Se autodestruye tras el primer mensaje del usuario.
- Mientras envía: textarea `disabled`, mic `disabled`, ENVIAR → "ENVIANDO ▍" en `--cyan-2`.
- Mic grabando: rellena de cyan; micro-status mono `--cyan-2` debajo *"Grabando · 0:08 · suelta para enviar"*.

### 6.4 Sidebar "Lo que estoy entendiendo"

**Tres bloques, no cinco:**
- **FOCO**: label mono + texto display 20px con el foco actual del agente.
- **SEÑALES**: label mono + lista compacta mono con 2-4 señales detectadas.
- **PRÓXIMO**: label mono + lista de 1-2 ítems que el agente necesita aclarar.

Sustituye "Claridad %" por un mini `progress-line` **vertical** de 4 fases (las mismas del top frame: Contexto · Proceso · Decisión · Cierre) con el nodo activo en `--cyan-2`. Refleja la posición sin métrica abstracta.

**Throttle de updates:** solo entre turnos, nunca durante streaming. Un solo refresh coherente por turno.

**Animación de update:** slide-in 8px desde la derecha + fade 250ms. Sin blink cyan (eliminado para no parecer alerta).

`aria-live="polite"` en el bloque FOCO.

## 7. Fase 03 — Email-gate con preview parcial

Cuando el backend confirma que tiene suficiente para informe:

1. Las secciones `01 / Resumen de acción` y `03 / Por qué empezar aquí` del informe se renderizan **inline en el flujo del chat**, no en modal. Ungated.
2. Debajo aparece la card del email-gate (esta sí con borde, es estado especial):

```
── EL AGENTE TIENE UNA RECOMENDACIÓN

He convertido tu caso en un primer
empleado IA viable.

  ─ Dime a qué email te lo envío y te
    abro el informe completo. Una sola vez.
    Sin newsletter automática.

  ┌────────────────────────────────┐
  │ EMAIL                          │
  │ ─────────────────────────────  │
  │ tu@email.com                   │
  └────────────────────────────────┘

  [ RECIBIR INFORME COMPLETO  → ]

  ── Una sola vez. Sin newsletter automática.   ← --proceed verde tenue
  ── ¿Por qué pido el email? ▸                  ← <details> colapsado
```

- Validación email solo `onblur`, nunca `oninput`. En error: `border-bottom` pasa a `--park`, mensaje en `--ink-muted` debajo.
- `<details>` colapsado por defecto con 2 frases de explicación de privacidad.
- Trust signal "Sin newsletter automática" en `--proceed` tenue, no `--ink-muted` (es señal positiva, no nota al pie).

Transición de fase 02 → 03: top frame avanza al nodo 3 del `progress-line`, la conexión se rellena cyan en 400ms ease-out.

## 8. Fase 04 — Informe editorial

Render **inline en el flujo del main**, no modal. 9 secciones editoriales con ancho completo, scroll vertical natural.

Estructura (mapeo del JSON del backend a componentes del CSS slide):

| # | Sección | Componente CSS |
|---|---|---|
| 01 | Resumen de acción | `statement.smaller` + chips de confianza/evidencia/siguiente paso |
| 02 | Lo que he entendido | eyebrow + body |
| 03 | Por qué empezar aquí | eyebrow + body con palabra clave en italic `--cyan-2` |
| 04 | Señales detectadas | `.areamap` 3×N (num + h4 + p) |
| 05 | Oportunidades prioritarias | `.lanes` de 3 columnas (PROCEED / REFINE / PARK, border-color del CSS) |
| 06 | No automatizar todavía | `.card.park` con lista editorial |
| 07 | Plan de 7 días | `.timeline` 4 nodos |
| 08 | Plan de 30 días | `.timeline` 4 nodos |
| 09 | Siguiente paso | `.beforeafter` o card grande con CTA cyan + checklist |

**Top sticky:**
- `LECTURA · N MIN` mono `--ink-muted` (estimado a 200 wpm sobre el texto del JSON).
- Índice horizontal con etiquetas (no números): `Resumen · Por qué · Señales · Lanes · Plan · Próximo`. Mono `--ink-muted`, activo en `--cyan-2`. Click → scroll suave.
- Chip `COPIAR ENLACE PRIVADO` → usa `/r/<lead_id>/<token>` (endpoint existente). Inline `ENLACE COPIADO ✓` sin toast.
- Feedback mini-pills `ÚTIL · REGULAR · POCO ÚTIL` siempre visibles. Click → slide-up text *"¿Qué faltó?"* → enter → `GRACIAS`. No corta lectura.
- `.kbd` "⌘ P" para imprimir / guardar PDF. El CSS ya tiene `@media print` que conserva colores dark.

**Animación de entrada del informe:**
- Cada sección numerada hace fade-up cuando entra en viewport via `IntersectionObserver` (threshold 0.2).
- No se revela todo de golpe — el informe se construye a medida que el usuario lee.
- Sticky frame fade-in al cargar el informe.

## 9. Estados de espera y error (lenguaje unificado)

Principio: el agente nunca grita ni te culpa, y la UI prefiere desaparecer a llamar la atención.

### 9.1 Espera del agente (3-15s)

Card del agente vacía con cursor lento `▍` (1.2s blink) + barra asintótica + ETA mono:

```
AGENTE ▍
──────────────────────────────────────  62%
respondiendo · ~5s
```

- Barra 1px de `--rule-strong` a `--cyan` que crece de 0 → 90% con curva asintótica (nunca llega a 100% antes de la respuesta).
- ETA mono se autocorrige con media rodante de los últimos 3 turnos (arranca en 10s).
- Si supera 25s: aparece **una sola línea** `--ink-muted` debajo: *"Está pensando una buena pregunta. Aguanta un momento."* Cero rotación de mensajes técnicos.

### 9.2 Cola transparente (`MAX_AI_CONCURRENCY=1` saturado)

```
AGENTE — en cola

Posición 2 · espera estimada ~3 min
No te muevas: sigo tu sesión.

  ┌─────────────────────────────────────┐
  │ Avísame por email cuando esté libre │
  │ tu@email.com           ENVIAR  →    │
  └─────────────────────────────────────┘
```

- Backend expone `queue_position` y `eta_seconds` en respuestas 503. Si no los tiene, el cliente estima desde la media rodante.
- Composer accesible: el usuario puede redactar su próxima respuesta mientras espera; cuando se libera el slot, se envía sola.
- Captura email opcional → endpoint nuevo `POST /api/notify-when-free` registra email + token y notifica vía `CRM_WEBHOOK_URL` cuando el slot se libere. Doble función: alivia ansiedad + captura lead pasivo.

### 9.3 Error temporal de red

**Cero card.** Solo micro-línea en el top frame:

```
IA AL DÍA · DISCOVERY                  RECONECTANDO ▍
```

Reintento silencioso cada 3s. Desaparece sola al recuperar. Solo escala a card si fallan 3 intentos seguidos.

### 9.4 Error de IA (proveedor caído, beta sin fallback)

Card editorial con borde `--park`, dos salidas:

```
EL AGENTE NO ESTÁ DISPONIBLE AHORA

No te entrego un diagnóstico mediocre.
Cuando vuelva, te aviso yo mismo —
o puedes leer un informe de muestra
mientras tanto.

[ AVISARME CUANDO VUELVA  → ]      VER MUESTRA →
```

### 9.5 Errores del usuario

- **Email inválido:** `border-bottom` pasa a `--park` solo `onblur`. Mensaje pequeño debajo en `--ink-muted`: *"Ese email no parece válido."* Sin shake, sin modal.
- **Audio incomprensible:** mic-status mono `--refine`: *"No te he entendido bien. Prueba a hablar más cerca o escríbelo."* El audio no se pierde — mini-control para reintentar el blob.
- **Rate limit (429):** card amarilla compacta `--refine` dentro del chat: *"Estás yendo muy rápido. Sigo en 30s."* Composer `disabled` con contador mono.

### 9.6 Restauración de sesión

```
── BIENVENIDO DE VUELTA

Seguíamos en:

  AGENTE
  "¿En qué momento del día se acumulan más
   esos mensajes sin responder?"

  [ CONTINUAR  → ]      [ EMPEZAR DE CERO ]
```

El usuario ve la última pregunta del agente antes de comprometerse a continuar. Opción explícita de reset.

### 9.7 Sin toasts ni modales en el flujo normal

Todo error, todo aviso, todo estado vive en la conversación o en el sidebar. Excepciones permitidas: la única modal del flujo es el "informe de muestra" desde el starter.

## 10. Accesibilidad

- `prefers-reduced-motion: reduce` → todas las animaciones se reducen a `opacity` (sin transforms ni slash-motif animado).
- Focus ring consistente: `outline: 2px solid var(--cyan-2); outline-offset: 2px`.
- `aria-live="polite"` en región de chat (nuevos turnos del agente) y en bloque FOCO del sidebar.
- Tap targets ≥ 44×44px en mobile.
- Mic con keyboard equivalent (textarea siempre es source of truth; mic transcribe dentro).
- Contraste auditado: body con `--ink-soft` sobre `--bg` = 13:1 (AAA). `--cyan-2` solo en ≥18px.

## 11. Performance

- Imágenes / iconos: SVG inline. Cero requests adicionales.
- Google Fonts con `font-display: swap` + subset crítico inline para Libre Baskerville hero.
- `body{background:#06081A}` inline en `<head>` → cero flash blanco.
- IntersectionObserver con `threshold: 0.2` y `rootMargin: "0px 0px -10% 0px"` para reveals.
- Animaciones solo sobre `opacity` y `transform` (no layout-triggering).

## 12. Cambios al backend (aditivos)

| Cambio | Endpoint / mecanismo | Compatibilidad |
|---|---|---|
| Exponer `queue_position` y `eta_seconds` | Respuestas 503 de `/api/chat` cuando el semáforo `MAX_AI_CONCURRENCY` esté saturado | Aditivo. Cuidar que la aserción existente en `test_ai_concurrency.py` no falle por la presencia de campos nuevos. |
| Aceptar `rewind_to_turn` (entero) en body de `/api/chat` | Si llega, el servidor trunca el historial de la sesión a ese índice (inclusive) antes de generar la respuesta. | Aditivo. Sin el campo, comportamiento idéntico al actual. |
| Captura "avísame cuando libere" | Nuevo `POST /api/notify-when-free` con `{email, session_id}`. Registra en CRM como lead parcial + dispara `CRM_WEBHOOK_URL` cuando el slot se libere. | Endpoint nuevo, sin tocar los existentes. |

Cualquier otro cambio al backend queda fuera de este spec.

## 13. Tests a actualizar

| Archivo | Cambio esperado |
|---|---|
| `test_public_ui_flow.py` | CTA renombrada ("Empezar conversación" en lugar de "Empezar diagnóstico"). Bloques `diagnostic-preview`, `live-map`, `signal-line`, `process-strip` eliminados — actualizar las aserciones que los referencien. Estado de espera ahora con barra, no rotación de texto. |
| `test_public_report_flow.py` | Email-gate ahora aparece tras preview parcial inline (sections 01 + 03 visibles antes del email). Informe render es inline, no modal. Selectores de feedback movidos al sticky frame. |
| `test_session_restore_flow.py` | Texto de bienvenida cambia a `BIENVENIDO DE VUELTA` + bloque con última pregunta del agente + 2 botones explícitos. |
| `test_ai_concurrency.py` | Verificar que el nuevo shape de respuesta 503 con `queue_position`/`eta_seconds` no rompe la aserción existente. |

`test_public_beta_gate.py`, `test_transcription_local.py`, `test_discovery_flow.py`, `test_agent_quality_guard.py`, `test_server_guards.py`, `test_private_report_link.py`, `test_crm_webhook_sync.py`, `test_backup_crm.py` → no se tocan (lógica backend, no UI).

## 14. Orden de implementación

Doce commits atómicos. Cada uno deja la app funcionando.

1. **Tokens base + tipografías** — reemplazar `:root`, inline `body{background}`, subset crítico de Libre Baskerville, escala fluida `clamp()`.
2. **Layout macro + top frame + footer** — shell, ancla temporal, progress-line de 4 fases, footer con counter + "IA AL DÍA /".
3. **Starter slim** — eliminar bloques sobrantes, montar hero + lead + CTA + 3-node progress-line + link de muestra. Animaciones de entrada.
4. **Chat surface limpio + backend rewind** — quitar bordes de cards en mensajes normales, tipografía dual del agente, labels solo primer turno, ghost text del primer turno. En el mismo commit: añadir aceptación de `rewind_to_turn` en `/api/chat` y conectar el hover/long-press "REESCRIBIR" del cliente.
5. **Sidebar 3 bloques + bottom sheet mobile** — FOCO/SEÑALES/PRÓXIMO, mini progress-line vertical, throttle de updates entre turnos.
6. **Estado de espera limpio** — barra asintótica + ETA + cursor lento.
7. **Cola transparente + endpoint `/api/notify-when-free`** — backend primero, frontend después.
8. **Errores honestos** — red silenciosa en top frame, IA muerta con dos salidas, email-gate validación on-blur, rate-limit chip.
9. **Restauración de sesión** — render de última pregunta + CONTINUAR/EMPEZAR DE CERO.
10. **Email-gate con preview parcial** — secciones 01 y 03 inline antes del email, `<details>` privacidad, trust signal verde tenue.
11. **Informe editorial** — render inline, 9 secciones, sticky con etiquetas, compartir privado, feedback en sticky, `LECTURA · N MIN`.
12. **Accesibilidad transversal** — `prefers-reduced-motion`, focus rings, `aria-live`, tap targets, auditoría de contraste final.

**Estimación de esfuerzo:** 6-10 horas de trabajo realista. Cada commit se valida con `./run_local_beta.sh` + tests del repo relevantes.

## 15. Fuera de scope

- `CRM_Dashboard.html`, `PRIVACY_BETA.html`, `Prototipo_Conversacional.html`, `Prototipo_Diagnostico.html`.
- Lógica del agente (prompts, fases, scoring, JSON del informe).
- CRM (SQLite, JSONL, webhook).
- Despliegue VPS (Caddy, systemd, scripts).
- Tests de backend que no toquen UI.
- Cualquier feature nueva del agente (memoria persistente, perfiles, multi-sesión, etc.).

## 16. Preguntas abiertas

Ninguna conocida al momento de cerrar el spec. Cualquier ambigüedad que aparezca durante la implementación se resuelve consultando este documento; si no está cubierta, se pregunta antes de inventar.
