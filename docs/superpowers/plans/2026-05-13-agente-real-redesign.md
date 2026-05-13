# Editorial Dark Redesign of Public Agent UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescribir el frontend público `Agente_Real_CRM.html` con el sistema editorial dark de la marca IA al Día, manteniendo lógica, persistencia y backend intactos. Añadir cambios aditivos al backend para soportar cola transparente y rewind de turno.

**Architecture:** Single-file vanilla HTML/CSS/JS sin build step. CSS custom properties para tokens. Animaciones con CSS transitions + IntersectionObserver. Backend Python `http.server`-based: cambios mínimos aditivos al chat handler y un endpoint nuevo. Tests Playwright actualizados a la par.

**Tech Stack:** HTML5, CSS3 (custom properties, clamp, grid, flex), Vanilla JS (ES2020 modules implícitos en `<script>`), Python 3 stdlib (`http.server`, `threading`, `sqlite3`), Playwright (tests de navegador).

**Spec de referencia:** [`docs/superpowers/specs/2026-05-13-agente-real-redesign-design.md`](../specs/2026-05-13-agente-real-redesign-design.md). El spec es la fuente de verdad para colores, tipografía, copy y comportamiento. Este plan traduce el spec en pasos ejecutables.

**Erratum vs spec:** El spec dice que el backend devuelve **HTTP 503** cuando el semáforo `MAX_AI_CONCURRENCY` está saturado. La realidad del código (`app_server.py` en `origin/main`) es **HTTP 429** vía `AiBusyError`. Este plan usa **429**.

---

## File Structure

| Archivo | Tipo | Responsabilidad |
|---|---|---|
| `Agente_Real_CRM.html` | Modify | Frontend único. Reescritura completa de `<style>` (líneas 7-1213). Reorganización del markup del starter (líneas 1275-1388). Ajustes selectivos al `<script>` para nuevos estados, edit-rewrite, queue handling, observer-based animations, accessibility. |
| `app_server.py` | Modify (aditivo) | Añadir campos `queue_position` y `eta_seconds` a la respuesta 429 del chat handler. Aceptar `rewind_to_turn` en `POST /api/chat` para truncar transcript antes de generar respuesta. Endpoint nuevo `POST /api/notify-when-free`. |
| `test_public_ui_flow.py` | Modify | Actualizar selectores y textos del starter (CTA, bloques eliminados, estado de espera nuevo). |
| `test_public_report_flow.py` | Modify | Actualizar email-gate (preview parcial inline antes), informe inline (no modal), feedback en sticky frame. |
| `test_session_restore_flow.py` | Modify | Actualizar texto de bienvenida y los dos botones explícitos. |
| `test_ai_concurrency.py` | Modify (defensivo) | Verificar que la respuesta 429 con campos nuevos no rompa la aserción existente. |
| `test_notify_when_free.py` | Create | Test nuevo para el endpoint `/api/notify-when-free`. |

**Boundaries y separación:**
- El `<style>` queda como bloque inline pero con secciones claramente comentadas (`/* === TOKENS === */`, `/* === LAYOUT === */`, etc.) para que sea editable por secciones.
- Los handlers JS quedan agrupados por responsabilidad dentro del `<script>`: estado de chat, sidebar updates, animations init, queue polling, edit-rewrite, accessibility helpers.
- El backend mantiene un único `Handler(SimpleHTTPRequestHandler)` — los cambios son endpoints adicionales y campos extra en respuestas existentes.
- Los tests de Playwright se mantienen como scripts CLI standalone, un archivo por flujo.

---

## Task 0: Sincronizar repo a `origin/main` y rebasear el spec

**Por qué:** El working tree local está 21 commits detrás de `origin/main`. Sin sync, los archivos referenciados (tests, endpoints, semáforo) no existen y nada del plan funciona. Hay además cambios sin commitear y un commit local nuevo (el del spec).

**Files:** N/A (operación git)

- [ ] **Step 1: Verificar estado divergente**

  ```bash
  cd "/Users/pablotapiascantos/Documents/Claude/Projects/🧪 MVPs/encuentra-tu-primer-empleado-ia"
  git status
  git log --oneline main..origin/main | head
  git log --oneline origin/main..main
  ```

  Esperado: working tree con archivos modificados; `main..origin/main` lista 21 commits; `origin/main..main` lista al menos `7f57aec` (el commit del spec).

- [ ] **Step 2: Decidir destino de los cambios sin commitear**

  Listar manualmente los archivos modificados (`Agente_Real_CRM.html`, `README.md`, `app_server.py`, etc.) y, con el usuario presente, decidir uno de estos tres caminos:

  - (a) **Stash** si los cambios deben conservarse pero no committearse: `git stash push -u -m "WIP pre-redesign sync"`.
  - (b) **Discard** si los cambios son obsoletos y origin/main los supera: `git restore <archivo>` por archivo (nunca `git restore .` masivo sin revisión).
  - (c) **Commit local** si los cambios son válidos y deben preservarse en historia local: commit aislado con mensaje claro antes de continuar.

  No tomar la decisión sin confirmación del usuario.

- [ ] **Step 3: Rebasear el commit del spec sobre origin/main**

  ```bash
  git fetch origin
  git rebase origin/main
  ```

  Esperado: aplica `7f57aec` (el commit del spec) limpiamente sobre la punta de `origin/main`. Si hay conflicto, abortar (`git rebase --abort`) y resolver caso por caso.

- [ ] **Step 4: Verificar el estado final**

  ```bash
  git log --oneline -5
  git status
  ls docs/superpowers/specs/
  ls docs/superpowers/plans/
  ```

  Esperado: HEAD = commit del spec encima de la punta de origin/main; spec presente; plan presente; working tree limpio (o con stash declarado).

- [ ] **Step 5: Sin commit, sin push**

  No hay cambios nuevos en este task. Continuar al Task 1.

---

## Task 1: Tokens base + tipografías

**Por qué:** Establecer la fundación visual (paleta IA al Día, escala fluida, fuentes con anti-FOUT) sobre la cual se montará todo lo demás. Tras este task la app sigue funcional pero ya con identidad dark editorial básica.

**Files:**
- Modify: `Agente_Real_CRM.html` (líneas 1-30 para `<head>`; líneas 7-1213 para `<style>`)

- [ ] **Step 1: Añadir Google Fonts y anti-flash en el `<head>`**

  Reemplazar el bloque `<head>` actual añadiendo, justo después del `<title>`:

  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400;1,700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap">
  <style>
    /* anti-flash: dark canvas desde frame 1 */
    body { background: #06081A; color: #F4EFE3; margin: 0; font-family: "IBM Plex Sans", system-ui, sans-serif; }
  </style>
  ```

- [ ] **Step 2: Reemplazar el bloque `:root` completo del `<style>`**

  Sustituir el bloque actual `:root { --bg: #f6f3ea; ... }` (líneas 8-21) por:

  ```css
  :root {
    /* === SUPERFICIES === */
    --bg-deep:  #06081A;
    --bg:       #0A0E26;
    --bg-warm:  #0E1331;
    --bg-elev:  #15214B;   /* IA al Día brand navy */
    --bg-card:  #161E45;

    /* === TINTA === */
    --ink:        #F4EFE3;
    --ink-soft:   #D9D3C2;
    --ink-muted:  #75747E;  /* IA al Día brand grey */
    --ink-faint:  #555C82;

    /* === REGLAS === */
    --rule:        rgba(160, 170, 210, 0.14);
    --rule-strong: rgba(160, 170, 210, 0.28);
    --rule-warm:   rgba(147, 133, 130, 0.20);  /* IA al Día brand taupe */
    --rule-cyan:   rgba(4, 151, 225, 0.45);

    /* === ACENTO + STATUS === */
    --cyan:      #0497E1;  /* IA al Día brand cyan */
    --cyan-deep: #048BCD;  /* IA al Día brand cyan deep */
    --cyan-2:    #38C0FF;
    --cyan-ink:  #7CD7FF;
    --proceed:   #5EE39A;
    --refine:    #F4C141;
    --park:      #F08484;

    /* === ESCALA TIPOGRÁFICA FLUIDA === */
    --t-mega:    clamp(56px, 9vw, 132px);
    --t-cover:   clamp(48px, 8vw, 96px);
    --t-title:   clamp(40px, 6vw, 72px);
    --t-h2:      clamp(32px, 4.5vw, 48px);
    --t-sub:     clamp(22px, 2.6vw, 32px);
    --t-lead:    clamp(18px, 2.2vw, 22px);
    --t-body:    clamp(15px, 1.6vw, 18px);
    --t-small:   clamp(13px, 1.4vw, 15px);
    --t-eyebrow: clamp(11px, 1vw, 13px);

    /* === SPACING === */
    --pad-x:      clamp(20px, 4vw, 64px);
    --pad-y:      clamp(20px, 3vw, 48px);
    --gap-1:      8px;
    --gap-2:      16px;
    --gap-3:      24px;
    --gap-4:      40px;
    --gap-5:      64px;

    /* === FAMILIAS === */
    --font-display: "Libre Baskerville", "Source Serif 4", Georgia, serif;
    --font-sans:    "IBM Plex Sans", system-ui, sans-serif;
    --font-mono:    "IBM Plex Mono", ui-monospace, monospace;

    /* === EASING === */
    --ease:        cubic-bezier(0.2, 0.8, 0.2, 1);
    --duration-1:  200ms;
    --duration-2:  320ms;
    --duration-3:  500ms;
  }

  * { box-sizing: border-box; }

  html, body {
    background: var(--bg-deep);
    color: var(--ink);
    margin: 0;
  }

  body {
    font-family: var(--font-sans);
    font-size: var(--t-body);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Tipografía editorial reusable */
  .eyebrow {
    font-family: var(--font-mono);
    font-size: var(--t-eyebrow);
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--cyan-2);
    font-weight: 500;
  }
  .eyebrow.muted { color: var(--ink-muted); }

  .display {
    font-family: var(--font-display);
    font-weight: 700;
    line-height: 1.04;
    letter-spacing: -0.02em;
    color: var(--ink);
    margin: 0;
    text-wrap: balance;
  }

  .lead {
    font-size: var(--t-lead);
    font-style: italic;
    line-height: 1.3;
    color: var(--ink-soft);
    margin: 0;
    text-wrap: balance;
  }

  .body { font-size: var(--t-body); color: var(--ink-soft); margin: 0; }
  .mono  { font-family: var(--font-mono); }
  .small { font-size: var(--t-small); color: var(--ink-muted); }
  .muted { color: var(--ink-muted); }
  .faint { color: var(--ink-faint); }

  /* Focus universal */
  :where(button, a, input, textarea, [tabindex]):focus-visible {
    outline: 2px solid var(--cyan-2);
    outline-offset: 2px;
  }

  /* Reduced motion */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```

- [ ] **Step 3: Eliminar el resto del CSS antiguo (provisional)**

  Tras el bloque nuevo, **eliminar** todo el CSS antiguo desde después del `:root` original hasta el cierre `</style>`. La app va a quedar visualmente rota — es esperado. Los siguientes tasks reconstruyen cada componente.

- [ ] **Step 4: Verificación visual mínima**

  ```bash
  ./run_local_beta.sh
  open http://localhost:8787/Agente_Real_CRM.html?ui_test=desktop
  ```

  Esperado: fondo `#06081A` (navy profundo) inmediato sin destello blanco. Texto en cream `#F4EFE3`. Layout completamente roto (sin estilos de componentes), pero las fuentes Libre Baskerville e IBM Plex Sans cargadas y visibles tras unos ms.

- [ ] **Step 5: Commit**

  ```bash
  git add Agente_Real_CRM.html
  git commit -m "$(cat <<'EOF'
  Replace base tokens with IA al Día editorial dark system

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 2: Layout macro (shell, top frame, footer)

**Por qué:** Reconstruir la rejilla de 2 columnas con identidad editorial: top frame con marca + ancla temporal + progress-line de 4 fases, footer con counter + slash-mark.

**Files:**
- Modify: `Agente_Real_CRM.html` (`<style>` y `<body>`)

- [ ] **Step 1: Añadir CSS del shell, top frame y footer**

  Insertar tras el bloque `:root` y la tipografía base, **antes** del cierre `</style>`:

  ```css
  /* === SHELL === */
  .shell {
    min-height: 100dvh;
    display: grid;
    grid-template-rows: auto 1fr auto;
  }

  .shell-body {
    display: grid;
    grid-template-columns: minmax(320px, 420px) 1fr;
    min-height: 0;
  }

  @media (max-width: 800px) {
    .shell-body { grid-template-columns: 1fr; }
  }

  /* === TOP FRAME === */
  .topframe {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: var(--gap-3);
    padding: var(--gap-2) var(--pad-x);
    border-bottom: 1px solid var(--rule);
    background: var(--bg-deep);
  }
  .topframe .brand,
  .topframe .save-status {
    font-family: var(--font-mono);
    font-size: var(--t-eyebrow);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }
  .topframe .save-status { justify-self: end; opacity: 0.6; transition: opacity var(--duration-2) var(--ease); }
  .topframe .save-status[data-state="syncing"] { color: var(--cyan); opacity: 1; }
  .topframe .save-status[data-state="reconnect"] { color: var(--cyan-2); opacity: 1; }

  /* === PROGRESS-LINE 4 FASES (top frame center) === */
  .phase-line {
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: 1fr;
    align-items: center;
    gap: var(--gap-1);
    min-width: 240px;
  }
  .phase-line .node {
    display: flex; align-items: center; gap: var(--gap-1);
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }
  .phase-line .node[data-state="done"] { color: var(--ink-muted); }
  .phase-line .node[data-state="active"] { color: var(--cyan-2); }
  .phase-line .node::before {
    content: "";
    width: 6px; height: 6px;
    border: 1px solid currentColor;
    background: transparent;
  }
  .phase-line .node[data-state="active"]::before { background: var(--cyan-2); }
  .phase-line .node[data-state="done"]::before { background: var(--ink-muted); }
  .phase-line .conn {
    height: 1px; background: var(--rule-strong); width: 100%;
  }
  .phase-line .conn[data-state="done"] { background: var(--cyan); }

  @media (max-width: 800px) {
    .phase-line .node span { display: none; }
  }

  /* === FOOTER === */
  .footframe {
    display: flex; justify-content: space-between; align-items: center;
    padding: var(--gap-2) var(--pad-x);
    border-top: 1px solid var(--rule);
    background: var(--bg-deep);
  }
  .footframe .counter,
  .footframe .mark {
    font-family: var(--font-mono);
    font-size: 13px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }
  .footframe .counter::before {
    content: "";
    display: inline-block; width: 24px; height: 1px;
    background: var(--rule-strong);
    margin-right: 12px;
    vertical-align: middle;
  }
  .footframe .mark .slash { color: var(--cyan-2); margin-left: 6px; }

  /* === ASIDE / MAIN === */
  aside.sidebar {
    padding: var(--pad-y) var(--pad-x);
    border-right: 1px solid var(--rule);
    background: var(--bg);
    display: flex; flex-direction: column;
    gap: var(--gap-3);
    min-width: 0;
  }
  main {
    background: var(--bg);
    display: flex; flex-direction: column;
    min-width: 0;
    padding: var(--pad-y) var(--pad-x);
  }

  @media (max-width: 800px) {
    aside.sidebar {
      border-right: none;
      border-bottom: 1px solid var(--rule);
      padding-bottom: var(--gap-3);
    }
  }
  ```

- [ ] **Step 2: Reemplazar el `<body>` con la nueva estructura macro**

  Sustituir todo el `<body>` actual (líneas 1215-1409) por la rejilla nueva. **Conservar los IDs y bloques internos** que vendrán en tasks siguientes — por ahora se dejan como contenedores vacíos:

  ```html
  <body>
    <div class="shell">
      <header class="topframe">
        <div class="brand" id="brand">IA AL DÍA · DISCOVERY · <span id="sessionAnchor"></span></div>
        <nav class="phase-line" id="phaseLine" aria-label="Fases de la sesión">
          <div class="node" data-state="active" data-phase="1"><span>Contexto</span></div>
          <div class="conn"></div>
          <div class="node" data-phase="2"><span>Proceso</span></div>
          <div class="conn"></div>
          <div class="node" data-phase="3"><span>Decisión</span></div>
          <div class="conn"></div>
          <div class="node" data-phase="4"><span>Cierre</span></div>
        </nav>
        <div class="save-status mono" id="saveStatus" aria-live="polite"></div>
      </header>

      <div class="shell-body">
        <aside class="sidebar" id="sidebar">
          <!-- Contenido contextual: starter / chat / email-gate / informe -->
        </aside>
        <main id="mainStage">
          <!-- Contenido contextual del flujo -->
        </main>
      </div>

      <footer class="footframe">
        <div class="counter" id="phaseCounter">01</div>
        <div class="mark">IA AL DÍA<span class="slash">/</span></div>
      </footer>
    </div>

    <script>
      /* === SESSION ANCHOR === */
      (() => {
        const months = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"];
        const d = new Date();
        const anchor = `${String(d.getDate()).padStart(2,"0")} ${months[d.getMonth()]} · ${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`;
        const el = document.getElementById("sessionAnchor");
        if (el) el.textContent = anchor;
      })();

      /* === PHASE TRANSITION HELPER === */
      function setPhase(n) {
        const nodes = document.querySelectorAll("#phaseLine .node");
        const conns = document.querySelectorAll("#phaseLine .conn");
        nodes.forEach((node, i) => {
          const idx = i + 1;
          if (idx < n) node.dataset.state = "done";
          else if (idx === n) node.dataset.state = "active";
          else node.removeAttribute("data-state");
        });
        conns.forEach((conn, i) => {
          if (i + 1 < n) conn.dataset.state = "done";
          else conn.removeAttribute("data-state");
        });
        document.getElementById("phaseCounter").textContent = String(n).padStart(2, "0");
      }
      setPhase(1);

      /* === SAVE STATUS HELPER === */
      let _saveStatusTimer;
      function setSaveStatus(state, message) {
        const el = document.getElementById("saveStatus");
        if (!el) return;
        clearTimeout(_saveStatusTimer);
        if (!state) { el.textContent = ""; el.removeAttribute("data-state"); return; }
        el.dataset.state = state;
        el.textContent = message;
        if (state === "syncing") {
          _saveStatusTimer = setTimeout(() => setSaveStatus(null), 2200);
        }
      }
    </script>
  </body>
  ```

  Nota: el resto del JS de la versión actual (chat handler, fetch, mic, etc.) se reintegra en tasks siguientes. Por ahora la app no funciona — es esperado.

- [ ] **Step 3: Verificación visual**

  Recargar `http://localhost:8787/Agente_Real_CRM.html?ui_test=desktop`. Esperado:
  - Top frame con `IA AL DÍA · DISCOVERY · DD MMM · HH:MM` a la izquierda.
  - Phase-line de 4 nodos en el centro (Contexto activo en cyan).
  - Footer con `─ 01` izquierda y `IA AL DÍA /` derecha.
  - Resto vacío (sidebar y main son `<aside>` y `<main>` sin contenido).

- [ ] **Step 4: Probar setPhase desde DevTools**

  En la consola: `setPhase(2)`, `setPhase(3)`, `setPhase(4)`. Esperado: el nodo activo se mueve, los anteriores se ponen en `--ink-muted`, las conexiones completadas en `--cyan`, el counter del footer cambia.

- [ ] **Step 5: Commit**

  ```bash
  git add Agente_Real_CRM.html
  git commit -m "$(cat <<'EOF'
  Add editorial shell with top frame, phase line and brand footer

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 3: Starter slim (fase 01)

**Por qué:** Primera impresión del producto. Hero serif gigante + lead + CTA + 3 promesas. Reduce los 6 bloques actuales a una composición editorial.

**Files:**
- Modify: `Agente_Real_CRM.html` (markup del `<aside>` y del `<main>` para fase 01; CSS del starter)

- [ ] **Step 1: Añadir CSS del starter**

  Insertar antes de `</style>`:

  ```css
  /* === STARTER === */
  .starter {
    display: grid;
    gap: var(--gap-4);
    align-content: start;
    position: relative;
    overflow: hidden;
  }

  .starter .hero-eyebrow { /* hereda .eyebrow */ }
  .starter .hero-title {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: var(--t-cover);
    line-height: 0.98;
    letter-spacing: -0.025em;
    color: var(--ink);
    margin: 0;
    text-wrap: balance;
  }
  .starter .hero-lead {
    font-family: var(--font-display);
    font-style: italic;
    font-size: var(--t-lead);
    color: var(--ink-soft);
    line-height: 1.3;
    max-width: 64ch;
    margin: 0;
  }

  /* CTA editorial cápsula */
  .cta-primary {
    display: inline-flex; align-items: center; gap: 14px;
    padding: 16px 28px;
    background: transparent;
    border: 1px solid var(--cyan);
    color: var(--cyan-2);
    font-family: var(--font-mono);
    font-size: 14px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    text-decoration: none;
    cursor: pointer;
    transition: background var(--duration-2) var(--ease), color var(--duration-2) var(--ease), transform var(--duration-2) var(--ease);
  }
  .cta-primary:hover { background: var(--cyan); color: var(--bg-deep); }
  .cta-primary:active { background: var(--cyan-deep); transform: translateY(1px); }
  .cta-primary .arrow { font-size: 16px; }

  .micro-tag {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-left: var(--gap-2);
    vertical-align: middle;
  }
  .micro-tag .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--cyan); display: inline-block; }

  .sample-link {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-muted);
    text-decoration: underline;
    text-decoration-color: var(--rule-strong);
    text-underline-offset: 4px;
    cursor: pointer;
    background: none; border: none;
    padding: 0; margin-top: var(--gap-1);
  }
  .sample-link:hover { color: var(--cyan-2); text-decoration-color: var(--cyan-2); }

  .hr-strong { height: 1px; background: var(--rule-strong); width: 0; transition: width 400ms var(--ease) 1000ms; }
  .starter.is-revealed .hr-strong { width: 100%; }

  /* Promise line: 3 nodos horizontales */
  .promise-line {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap-4);
  }
  .promise {
    display: grid; gap: var(--gap-1);
  }
  .promise .num {
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.22em;
    color: var(--cyan-2);
  }
  .promise h3 {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: clamp(20px, 2.4vw, 28px);
    letter-spacing: -0.015em;
    color: var(--ink);
    margin: 0;
  }
  .promise p {
    font-size: var(--t-small);
    color: var(--ink-muted);
    line-height: 1.4;
    margin: 0;
  }

  @media (max-width: 800px) {
    .promise-line { grid-template-columns: 1fr; gap: var(--gap-3); }
  }

  /* Slash motif ambient */
  .slash-motif {
    position: absolute; inset: 0; pointer-events: none; overflow: hidden;
    opacity: 0; transition: opacity 400ms var(--ease) 1300ms;
  }
  .starter.is-revealed .slash-motif { opacity: 0.5; }
  .slash-motif::before {
    content: "";
    position: absolute;
    width: 240%; height: 1px;
    background: var(--rule-cyan);
    top: 50%; left: -70%;
    transform: rotate(-22deg);
  }

  /* Reveal-on-load helper (los hijos heredan stagger via inline style en JS) */
  .reveal { opacity: 0; transform: translateY(8px); transition: opacity var(--duration-3) var(--ease), transform var(--duration-3) var(--ease); }
  .starter.is-revealed .reveal { opacity: 1; transform: none; }
  ```

- [ ] **Step 2: Inyectar el markup del starter en el `<main>` y el contenido del aside**

  Reemplazar el contenido del `<aside id="sidebar">` y `<main id="mainStage">` (que estaban vacíos tras Task 2) por:

  ```html
  <aside class="sidebar" id="sidebar">
    <div class="eyebrow">01 / Discovery</div>
    <h1 class="display" style="font-size: var(--t-h2);">Encuentra tu primer empleado IA.</h1>
    <p class="lead">— Una mini sesión consultiva para detectar dónde se escapa tiempo, dinero o clientes.</p>
    <div class="hr-strong" style="width: 100%; opacity: 1;"></div>
    <div class="aside-receivable">
      <div class="eyebrow muted">Qué recibirás</div>
      <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: var(--gap-2);">
        <li><strong style="font-family: var(--font-display); font-size: var(--t-body); display: block; color: var(--ink);">Fugas detectadas</strong><span class="small">Dónde se pierde tiempo, dinero, clientes o foco.</span></li>
        <li><strong style="font-family: var(--font-display); font-size: var(--t-body); display: block; color: var(--ink);">Primer empleado IA recomendado</strong><span class="small">Qué debería hacer, con qué datos, límites y riesgos.</span></li>
        <li><strong style="font-family: var(--font-display); font-size: var(--t-body); display: block; color: var(--ink);">Plan de 7 días</strong><span class="small">Primeros pasos realistas sin lenguaje técnico.</span></li>
      </ul>
    </div>
  </aside>

  <main id="mainStage">
    <section class="starter" id="starter">
      <div class="slash-motif" aria-hidden="true"></div>
      <div class="eyebrow reveal" style="transition-delay: 120ms;">Discovery gratuito · 7-10 min</div>
      <h2 class="hero-title reveal" style="transition-delay: 240ms;">¿Dónde se te escapa tiempo, dinero o clientes?</h2>
      <p class="hero-lead reveal" style="transition-delay: 600ms;">— Una sesión consultiva con un agente que escucha, repregunta y separa automatizaciones útiles de ideas bonitas que todavía no toca construir.</p>
      <div class="reveal" style="transition-delay: 800ms;">
        <button type="button" class="cta-primary" id="startSession">
          Empezar conversación
          <span class="arrow" aria-hidden="true">→</span>
        </button>
        <span class="micro-tag" id="microTag"><span class="dot"></span>Mejor con micro</span>
      </div>
      <div class="reveal" style="transition-delay: 900ms;">
        <button type="button" class="sample-link" id="sampleLink">Ver un informe de muestra (2 min) →</button>
      </div>
      <div class="hr-strong"></div>
      <div class="promise-line">
        <article class="promise reveal" style="transition-delay: 1100ms;">
          <span class="num">01 / Cuéntame una escena</span>
          <h3>Una situación reciente</h3>
          <p>Donde algo se acumuló, se retrasó o se quedó sin responder.</p>
        </article>
        <article class="promise reveal" style="transition-delay: 1180ms;">
          <span class="num">02 / Yo extraigo el patrón</span>
          <h3>De relato a procesos</h3>
          <p>Convierto tu caso en señales y procesos repetibles.</p>
        </article>
        <article class="promise reveal" style="transition-delay: 1260ms;">
          <span class="num">03 / Te entrego un plan</span>
          <h3>Empleado IA recomendado</h3>
          <p>Riesgos, primer paso, plan de 7 y 30 días.</p>
        </article>
      </div>
    </section>
  </main>
  ```

- [ ] **Step 3: Disparar el reveal al cargar**

  Añadir al `<script>` (al final, antes de `</script>`):

  ```javascript
  /* === STARTER REVEAL === */
  requestAnimationFrame(() => {
    const starter = document.getElementById("starter");
    if (starter) starter.classList.add("is-revealed");
  });
  ```

- [ ] **Step 4: Verificación visual**

  Recargar la página. Esperado:
  - Tras ~120ms cada elemento aparece con fade + slide-up suave en orden (eyebrow → título → lead → CTA → link → regla → 3 promesas → slash motif).
  - Hover en CTA: fondo cyan, texto navy, transición suave.
  - El layout cabe en 1 pantalla en desktop a 1440×900 sin scroll forzado.
  - Mobile (resize a 375px): promise-line apilada, CTA legible, micro-tag debajo.

- [ ] **Step 5: Verificación de accesibilidad mínima**

  En DevTools → Application → Local Overrides, simular `prefers-reduced-motion: reduce` (o emularlo en Rendering pane). Recargar. Esperado: todo aparece instantáneamente sin animación de transform.

- [ ] **Step 6: Actualizar `test_public_ui_flow.py`**

  Buscar líneas que validen textos del starter eliminado y actualizarlas. Texto a cambiar:

  - El test actual busca: `page.get_by_text("analiza tu negocio como lo haría un consultor")` → ese texto pertenecía al starter-copy original. Reemplazar por: `page.get_by_text("escucha, repregunta y separa")` (parte del nuevo lead).

  Ejecutar:

  ```bash
  ./run_local_beta.sh
  python3 test_public_ui_flow.py --base http://localhost:8787
  ```

  Esperado: el test fallaba en la línea del texto antiguo; tras el cambio, pasa al menos hasta esa aserción.

  Si fallan más selectores (probablemente el del CTA "Empezar diagnóstico"), actualizarlos: `page.get_by_role("button", name="Empezar conversación")`.

  Re-ejecutar hasta que el script pase la fase de "starter visible". Las fases posteriores del test (chat, etc.) seguirán fallando porque aún no están reconstruidas — eso es esperado y se arregla en tasks siguientes.

- [ ] **Step 7: Commit**

  ```bash
  git add Agente_Real_CRM.html test_public_ui_flow.py
  git commit -m "$(cat <<'EOF'
  Build slim cinematic starter for the public agent

  Replace the 6-block starter with hero + lead + CTA + 3-node promise
  line. Add cubic-bezier reveal stagger and respect prefers-reduced-motion.
  Update Playwright UI test selectors to match the new copy.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 4: Chat surface limpio + backend rewind

**Por qué:** Reconstruir la conversación con tipografía editorial sin cards en cada turno, etiquetas solo en el primero, edit-rewrite con `rewind_to_turn` aditivo en backend.

**Files:**
- Modify: `Agente_Real_CRM.html` (markup del chat, composer, JS de envío y render; CSS del chat)
- Modify: `app_server.py` (handler de `POST /api/chat` para aceptar `rewind_to_turn`)
- Create: `test_rewind_to_turn.py`

### Backend primero (TDD)

- [ ] **Step 1: Escribir test fallido para `rewind_to_turn`**

  Crear `test_rewind_to_turn.py`:

  ```python
  #!/usr/bin/env python3
  """Verifica que /api/chat acepte rewind_to_turn y trunque el transcript del lead."""
  import json
  import os
  import sqlite3
  import sys
  import time
  import urllib.request
  from pathlib import Path

  BASE = os.environ.get("BASE", "http://localhost:8787")


  def post(path, payload):
      req = urllib.request.Request(
          f"{BASE}{path}",
          data=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
          method="POST",
      )
      with urllib.request.urlopen(req, timeout=60) as resp:
          return resp.status, json.loads(resp.read().decode("utf-8"))


  def main() -> int:
      # Crear sesión
      status, data = post("/api/session", {})
      assert status == 200, f"session create failed: {status} {data}"
      lead_id = data["lead_id"]

      # Tres turnos para tener historial
      for txt in ["primero", "segundo", "tercero"]:
          status, _ = post("/api/chat", {"lead_id": lead_id, "message": txt})
          assert status in (200, 429), f"chat returned {status}"
          if status == 429:
              # Si está saturado el semáforo, abortamos sin marcar fail
              print(json.dumps({"ok": True, "skipped": True, "reason": "ai busy during setup"}))
              return 0
          time.sleep(0.3)

      # Verificar transcript tiene 3 user turns
      db_path = Path(os.environ.get("CRM_DB", "crm.sqlite3"))
      con = sqlite3.connect(db_path)
      try:
          row = con.execute("SELECT transcript FROM leads WHERE id = ?", (lead_id,)).fetchone()
      finally:
          con.close()
      assert row, "lead not in CRM"
      transcript_pre = json.loads(row[0])
      user_turns_pre = [m for m in transcript_pre if m.get("role") == "user"]
      assert len(user_turns_pre) == 3, f"expected 3 user turns, got {len(user_turns_pre)}"

      # Rewind al turno 1 (conserva inclusive) y manda nuevo mensaje
      status, _ = post("/api/chat", {"lead_id": lead_id, "message": "rewind y nuevo", "rewind_to_turn": 1})
      assert status in (200, 429), f"rewind chat returned {status}"
      if status == 429:
          print(json.dumps({"ok": True, "skipped": True, "reason": "ai busy after rewind"}))
          return 0

      # Verificar truncado: 2 user turns (el 1 conservado + el nuevo)
      con = sqlite3.connect(db_path)
      try:
          row = con.execute("SELECT transcript FROM leads WHERE id = ?", (lead_id,)).fetchone()
      finally:
          con.close()
      transcript_post = json.loads(row[0])
      user_turns_post = [m for m in transcript_post if m.get("role") == "user"]
      assert len(user_turns_post) == 2, f"expected 2 user turns after rewind, got {len(user_turns_post)}"
      assert user_turns_post[0]["content"] == "primero", f"expected first turn preserved, got {user_turns_post[0]}"
      assert user_turns_post[-1]["content"] == "rewind y nuevo"

      print(json.dumps({"ok": True, "lead_id": lead_id, "user_turns_post": len(user_turns_post)}, indent=2))
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 2: Ejecutar el test — debe fallar**

  ```bash
  ./run_local_beta.sh
  python3 test_rewind_to_turn.py
  ```

  Esperado: AssertionError en `expected 2 user turns after rewind, got 4` (porque el backend aún ignora `rewind_to_turn` y el mensaje se añade encima de los 3 anteriores).

- [ ] **Step 3: Implementar `rewind_to_turn` en `app_server.py`**

  Localizar el handler `POST /api/chat` en `app_server.py` (alrededor de la línea 1570 según `grep`). Justo después de cargar el lead y antes de añadir el nuevo mensaje al transcript, añadir el truncado:

  ```python
  # Justo después de:
  #   user_turns = len([m for m in lead["transcript"] if m.get("role") == "user"])
  #   if user_turns >= MAX_USER_TURNS: ...
  #
  # Añadir:
  rewind_to = payload.get("rewind_to_turn")
  if isinstance(rewind_to, int) and rewind_to >= 0:
      # Conservar inclusivamente hasta el user turn de índice rewind_to
      user_indices = [i for i, m in enumerate(lead["transcript"]) if m.get("role") == "user"]
      if rewind_to < len(user_indices):
          cutoff = user_indices[rewind_to] + 1  # inclusive del user turn pedido
          # Conservar también la respuesta del agente inmediatamente posterior si existe
          if cutoff < len(lead["transcript"]) and lead["transcript"][cutoff].get("role") == "assistant":
              cutoff += 1
          lead["transcript"] = lead["transcript"][:cutoff]
          insert_event(lead_id, "session_rewind", {"to_turn": rewind_to, "kept_messages": len(lead["transcript"])})
  ```

  Lo siguiente del handler (que añade `user_text` al transcript y llama a `call_ai`) ya queda correcto.

- [ ] **Step 4: Re-ejecutar el test — debe pasar**

  ```bash
  python3 test_rewind_to_turn.py
  ```

  Esperado: `{"ok": true, "lead_id": "...", "user_turns_post": 2}` o `skipped` si la IA está saturada (skip cuenta como pass).

### Frontend (chat surface + edit-rewrite UI)

- [ ] **Step 5: Añadir CSS del chat al `<style>`**

  Insertar antes de `</style>`:

  ```css
  /* === CHAT === */
  .chat-stage {
    display: flex; flex-direction: column;
    flex: 1; min-height: 0;
    gap: var(--gap-3);
  }
  .chat-scroll {
    flex: 1; min-height: 0;
    overflow-y: auto;
    display: flex; flex-direction: column;
    gap: var(--gap-3);
    padding-right: 8px;
    scroll-behavior: smooth;
  }
  .chat-scroll::-webkit-scrollbar { width: 8px; }
  .chat-scroll::-webkit-scrollbar-thumb { background: var(--rule-strong); }

  .turn {
    display: grid; gap: 6px;
    max-width: 70%;
    position: relative;
  }
  .turn[data-role="agent"] { justify-self: start; }
  .turn[data-role="user"]  { justify-self: end; text-align: right; }
  .turn .label {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-muted);
  }
  .turn[data-role="user"] .label { color: var(--ink-faint); }
  .turn .body {
    font-size: var(--t-body);
    color: var(--ink-soft);
    line-height: 1.5;
  }
  .turn[data-role="agent"][data-short="true"] .body {
    font-family: var(--font-display);
    font-size: clamp(18px, 1.9vw, 19px);
    color: var(--ink);
    line-height: 1.3;
  }
  .turn-separator {
    height: 1px; background: var(--rule);
    width: 32px; margin: 0 auto;
  }

  .turn .edit-handle {
    position: absolute; top: 0; right: 0;
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-faint);
    border: 1px solid var(--rule-strong);
    padding: 4px 10px;
    background: var(--bg-elev);
    cursor: pointer;
    opacity: 0;
    transition: opacity var(--duration-2) var(--ease), color var(--duration-2) var(--ease);
  }
  .turn[data-role="user"]:hover .edit-handle,
  .turn[data-role="user"][data-edit-visible="true"] .edit-handle { opacity: 1; }
  .turn .edit-handle:hover { color: var(--cyan-2); border-color: var(--cyan); }

  /* Composer */
  .composer-wrap {
    border: 1px solid var(--rule);
    background: var(--bg-elev);
    padding: var(--gap-2);
    display: grid; gap: var(--gap-1);
  }
  .composer-grid {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: var(--gap-2);
    align-items: end;
  }
  .composer-grid textarea {
    width: 100%; resize: none;
    background: transparent;
    border: none;
    color: var(--ink);
    font: inherit;
    font-size: var(--t-body);
    min-height: 56px;
    max-height: 200px;
    padding: 8px 0;
  }
  .composer-grid textarea::placeholder { color: var(--ink-muted); font-style: italic; }
  .composer-grid textarea:focus { outline: none; }
  .composer-grid .icon-btn {
    width: 44px; height: 44px;
    display: inline-flex; align-items: center; justify-content: center;
    background: transparent;
    border: 1px solid var(--rule-strong);
    color: var(--ink-soft);
    cursor: pointer;
  }
  .composer-grid .icon-btn[data-recording="true"] { background: var(--cyan); color: var(--bg-deep); border-color: var(--cyan); }
  .composer-grid .icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .composer-grid .send-btn { /* hereda .cta-primary */ padding: 10px 22px; }
  .composer-hint {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }

  @media (max-width: 800px) {
    .turn { max-width: 90%; }
  }
  ```

- [ ] **Step 6: Reemplazar el contenido del `<main>` cuando arranca la sesión**

  Añadir al `<script>` (antes del `</script>`) una función que sustituye el starter por la chat-stage:

  ```javascript
  /* === ENTER CHAT === */
  let SESSION = { lead_id: null, transcript: [] };

  function enterChat() {
    setPhase(2);
    const main = document.getElementById("mainStage");
    main.innerHTML = `
      <div class="chat-stage">
        <div class="chat-scroll" id="chatScroll" aria-live="polite" aria-relevant="additions"></div>
        <div class="composer-wrap">
          <div class="composer-grid">
            <textarea id="composer" placeholder="Cuéntame una escena reciente…" aria-label="Tu mensaje"></textarea>
            <button class="icon-btn" id="micBtn" type="button" aria-label="Grabar con micrófono" title="Micrófono">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <path d="M12 19v3"></path>
              </svg>
            </button>
            <button class="cta-primary send-btn" id="sendBtn" type="button">Enviar <span class="arrow">→</span></button>
          </div>
          <div class="composer-hint" id="composerHint">⏎ enviar · ⇧⏎ línea nueva</div>
        </div>
      </div>
    `;
    // Sidebar contextual chat se monta en Task 5
    document.getElementById("composer").focus();
  }

  function appendTurn(role, content) {
    const scroll = document.getElementById("chatScroll");
    const isFirstOfRole = !scroll.querySelector(`.turn[data-role="${role}"]`);
    const isShort = role === "agent" && content.length <= 120;
    if (scroll.lastElementChild && !scroll.lastElementChild.classList.contains("turn-separator")) {
      const sep = document.createElement("div");
      sep.className = "turn-separator";
      scroll.appendChild(sep);
    }
    const turn = document.createElement("div");
    turn.className = "turn";
    turn.dataset.role = role;
    if (isShort) turn.dataset.short = "true";
    turn.dataset.index = String(SESSION.transcript.filter(m => m.role === role).length);
    turn.innerHTML = `
      ${isFirstOfRole ? `<span class="label">${role === "agent" ? "Agente" : "Tú"}</span>` : ""}
      <div class="body"></div>
      ${role === "user" ? `<button class="edit-handle" type="button" aria-label="Reescribir esta respuesta">Reescribir</button>` : ""}
    `;
    turn.querySelector(".body").textContent = content;
    if (role === "user") {
      const handle = turn.querySelector(".edit-handle");
      handle.addEventListener("click", () => rewindToTurn(parseInt(turn.dataset.index, 10)));
    }
    scroll.appendChild(turn);
    SESSION.transcript.push({ role, content });
    scroll.scrollTop = scroll.scrollHeight;
    // Composer hint se autodestruye tras el primer mensaje del usuario
    const hint = document.getElementById("composerHint");
    if (hint && role === "user") hint.style.display = "none";
  }

  async function sendMessage(text, opts = {}) {
    if (!SESSION.lead_id || !text.trim()) return;
    appendTurn("user", text);
    const sendBtn = document.getElementById("sendBtn");
    const composer = document.getElementById("composer");
    sendBtn.disabled = true; sendBtn.innerHTML = "Enviando ▍";
    composer.disabled = true; composer.value = "";
    setSaveStatus("syncing", "GUARDANDO ▍");
    try {
      const body = { lead_id: SESSION.lead_id, message: text };
      if (opts.rewindTo !== undefined) body.rewind_to_turn = opts.rewindTo;
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (res.status === 429) {
        // Cola: implementado en Task 7
        appendTurn("agent", data.error || "Estoy con otra sesión. Vuelvo en unos segundos.");
        return;
      }
      if (!res.ok) {
        appendTurn("agent", "No te entrego una respuesta mediocre. Lo retomamos en un momento.");
        return;
      }
      appendTurn("agent", data.reply || "");
      setSaveStatus("syncing", "GUARDADO HACE 0s");
    } catch (e) {
      setSaveStatus("reconnect", "RECONECTANDO ▍");
    } finally {
      sendBtn.disabled = false; sendBtn.innerHTML = `Enviar <span class="arrow">→</span>`;
      composer.disabled = false; composer.focus();
    }
  }

  async function rewindToTurn(index) {
    const composer = document.getElementById("composer");
    const scroll = document.getElementById("chatScroll");
    // Reconstruir UI: cortar a partir del user turn `index` (exclusive)
    const userTurns = scroll.querySelectorAll(`.turn[data-role="user"]`);
    const target = userTurns[index];
    if (!target) return;
    // Pre-rellenar el composer con el contenido y permitir editarlo
    composer.value = target.querySelector(".body").textContent;
    // Eliminar todo desde target en adelante (incluido)
    let node = target;
    // Caminar hacia atrás hasta el separador anterior si existe
    if (node.previousElementSibling && node.previousElementSibling.classList.contains("turn-separator")) {
      node = node.previousElementSibling;
    }
    while (node && node.nextElementSibling) node.nextElementSibling.remove();
    node.remove();
    // Actualizar SESSION.transcript localmente (lo verdadero ocurre en backend en el próximo send)
    SESSION.pendingRewindTo = index;
    composer.focus();
  }

  /* CTA del starter conecta con enterChat() */
  document.getElementById("startSession").addEventListener("click", async () => {
    const res = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const data = await res.json();
    SESSION.lead_id = data.lead_id;
    enterChat();
    // Primer mensaje del agente lo decide el backend en /api/session o se solicita aquí
    if (data.greeting) appendTurn("agent", data.greeting);
  });

  /* Envío del composer */
  document.addEventListener("keydown", (e) => {
    if (e.target && e.target.id === "composer" && e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const text = e.target.value.trim();
      if (!text) return;
      const opts = SESSION.pendingRewindTo !== undefined ? { rewindTo: SESSION.pendingRewindTo } : {};
      delete SESSION.pendingRewindTo;
      sendMessage(text, opts);
    }
  });
  document.addEventListener("click", (e) => {
    if (e.target && e.target.id === "sendBtn") {
      const text = document.getElementById("composer").value.trim();
      if (!text) return;
      const opts = SESSION.pendingRewindTo !== undefined ? { rewindTo: SESSION.pendingRewindTo } : {};
      delete SESSION.pendingRewindTo;
      sendMessage(text, opts);
    }
  });
  ```

  Nota: `data.greeting` puede no existir en la respuesta de `/api/session`. Verificar estructura real con `curl -X POST http://localhost:8787/api/session -H "Content-Type: application/json" -d '{}'`. Si el backend devuelve `transcript` con un primer mensaje del agente, iterar sobre él.

- [ ] **Step 7: Verificación visual completa**

  Recargar `http://localhost:8787/Agente_Real_CRM.html?ui_test=desktop`. Click en "Empezar conversación":
  - El starter se reemplaza por la chat-stage.
  - Phase-line del top frame avanza al nodo 2 (PROCESO).
  - Si el backend devuelve un primer mensaje, aparece como turno del agente con label "Agente".
  - Escribir en el composer y pulsar Enter envía. Aparece como turno "Tú" alineado a la derecha.
  - Tras la respuesta del agente, llega un segundo turno sin label (el primer turno del agente ya tenía label).
  - Hover sobre un mensaje propio: aparece "Reescribir" en la esquina superior derecha. Click → recompone el composer con ese texto y trunca el chat. Enviar de nuevo → backend recibe `rewind_to_turn` y trunca.

- [ ] **Step 8: Re-ejecutar `test_rewind_to_turn.py` y `test_public_ui_flow.py`**

  ```bash
  python3 test_rewind_to_turn.py
  python3 test_public_ui_flow.py --base http://localhost:8787
  ```

  Actualizar selectores en `test_public_ui_flow.py` cuando fallen (probablemente referencias a `#chat`, `#composer`, etc. del HTML antiguo). Mantener los textos de inicio del agente con `get_by_text` flexible.

- [ ] **Step 9: Commit**

  ```bash
  git add Agente_Real_CRM.html app_server.py test_rewind_to_turn.py test_public_ui_flow.py
  git commit -m "$(cat <<'EOF'
  Build clean editorial chat surface with rewind support

  Frontend: typography-driven turns without per-message cards, labels only
  on first turn of each role, hover-to-rewrite handle on user messages,
  ghost composer hint that self-destructs after first send.
  Backend: optional rewind_to_turn field in /api/chat truncates transcript
  to that user index inclusive. Aditive, no behavior change without the
  field. Covered by test_rewind_to_turn.py.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 5: Sidebar 3 bloques + bottom sheet mobile

**Por qué:** Sidebar contextual durante el chat con FOCO/SEÑALES/PRÓXIMO + mini phase-line vertical. En mobile se convierte en bottom sheet con tira siempre visible.

**Files:**
- Modify: `Agente_Real_CRM.html` (CSS sidebar; JS para refresh entre turnos)

- [ ] **Step 1: CSS del sidebar de chat y bottom sheet móvil**

  Insertar antes de `</style>`:

  ```css
  /* === SIDEBAR DE CHAT === */
  .sidebar-chat {
    display: grid; gap: var(--gap-3);
  }
  .sidebar-chat .block {
    display: grid; gap: var(--gap-1);
  }
  .sidebar-chat .block-label { /* hereda .eyebrow.muted */ }
  .sidebar-chat .block-value {
    font-family: var(--font-display);
    font-size: clamp(18px, 1.8vw, 22px);
    color: var(--ink);
    line-height: 1.3;
  }
  .sidebar-chat .block-list {
    list-style: none; padding: 0; margin: 0;
    display: grid; gap: 6px;
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--ink-soft);
    line-height: 1.4;
  }
  .sidebar-chat .block-list.warn li { color: var(--refine); }
  .sidebar-chat .block-list li { padding-left: 14px; position: relative; }
  .sidebar-chat .block-list li::before {
    content: "·"; position: absolute; left: 0; color: var(--cyan-2);
  }
  .sidebar-chat .vline { /* mini vertical phase line */
    display: grid; gap: 6px;
    border-left: 1px solid var(--rule);
    padding-left: var(--gap-2);
    margin-top: var(--gap-1);
  }
  .sidebar-chat .vline .vstep {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-faint);
    position: relative;
  }
  .sidebar-chat .vline .vstep::before {
    content: ""; position: absolute; left: -19px; top: 6px;
    width: 6px; height: 6px;
    border: 1px solid currentColor;
  }
  .sidebar-chat .vline .vstep[data-state="active"] {
    color: var(--cyan-2);
  }
  .sidebar-chat .vline .vstep[data-state="active"]::before { background: var(--cyan-2); }
  .sidebar-chat .vline .vstep[data-state="done"] { color: var(--ink-muted); }
  .sidebar-chat .vline .vstep[data-state="done"]::before { background: var(--ink-muted); }

  /* Slide-in updates */
  .sidebar-chat .block.is-updated { animation: sb-update 250ms var(--ease); }
  @keyframes sb-update {
    from { opacity: 0; transform: translateX(8px); }
    to   { opacity: 1; transform: none; }
  }

  /* === MOBILE BOTTOM SHEET === */
  @media (max-width: 800px) {
    aside.sidebar.is-chat-mode {
      position: fixed; left: 0; right: 0; bottom: 0;
      max-height: 60dvh;
      background: var(--bg-elev);
      border-top: 1px solid var(--rule-strong);
      border-right: none;
      padding: var(--gap-2) var(--pad-x);
      transform: translateY(calc(100% - 60px));
      transition: transform var(--duration-3) var(--ease);
      z-index: 10;
      overflow-y: auto;
    }
    aside.sidebar.is-chat-mode[data-open="true"] { transform: none; }
    aside.sidebar.is-chat-mode .sheet-handle {
      display: flex; justify-content: space-between; align-items: center;
      cursor: pointer; padding: 8px 0;
      font-family: var(--font-mono);
      font-size: 11px; letter-spacing: 0.22em;
      text-transform: uppercase; color: var(--ink-soft);
    }
    aside.sidebar.is-chat-mode .sheet-handle::before {
      content: "▴"; color: var(--cyan-2); margin-right: 8px;
    }
    aside.sidebar.is-chat-mode[data-open="true"] .sheet-handle::before { content: "▾"; }
  }
  @media (min-width: 801px) {
    aside.sidebar .sheet-handle { display: none; }
  }
  ```

- [ ] **Step 2: JS para mostrar el sidebar de chat tras `enterChat()`**

  Añadir al `<script>`, antes del `</script>`:

  ```javascript
  /* === SIDEBAR CHAT MODE === */
  function renderSidebarChat(state = {}) {
    const sidebar = document.getElementById("sidebar");
    const phases = ["Contexto","Proceso","Decisión","Cierre"];
    const activePhase = state.phase || 2;
    const phasesHtml = phases.map((p, i) => {
      const idx = i + 1;
      let s = "";
      if (idx < activePhase) s = "done";
      else if (idx === activePhase) s = "active";
      return `<div class="vstep" data-state="${s}">${p}</div>`;
    }).join("");
    sidebar.classList.add("is-chat-mode");
    sidebar.innerHTML = `
      <div class="sheet-handle" id="sheetHandle">
        <span>Lo que estoy entendiendo</span>
        <span class="block-value" style="font-size: 14px; color: var(--cyan-2);">${(state.foco || "Buscando el primer proceso").slice(0, 40)}</span>
      </div>
      <div class="sidebar-chat">
        <div class="block">
          <div class="eyebrow muted">02 / Discovery en vivo</div>
        </div>
        <div class="block">
          <div class="eyebrow muted block-label">Foco</div>
          <div class="block-value" id="sbFoco">${state.foco || "Buscando el primer proceso claro"}</div>
        </div>
        <div class="vline" id="sbVline">${phasesHtml}</div>
        <div class="block">
          <div class="eyebrow muted block-label">Señales</div>
          <ul class="block-list" id="sbSignals">${(state.signals || ["Aún esperando contexto."]).map(s => `<li>${s}</li>`).join("")}</ul>
        </div>
        <div class="block">
          <div class="eyebrow muted block-label">Próximo</div>
          <ul class="block-list warn" id="sbNext">${(state.next || ["Negocio, cliente y proceso repetitivo."]).map(s => `<li>${s}</li>`).join("")}</ul>
        </div>
      </div>
    `;
    const handle = document.getElementById("sheetHandle");
    if (handle) handle.addEventListener("click", () => {
      sidebar.dataset.open = sidebar.dataset.open === "true" ? "false" : "true";
    });
  }

  function updateSidebarFromTurn(facts = {}) {
    const fields = {
      sbFoco: facts.focus,
      sbSignals: facts.signals,
      sbNext: facts.gaps,
    };
    if (fields.sbFoco) {
      const el = document.getElementById("sbFoco");
      if (el) { el.textContent = fields.sbFoco; el.parentElement.classList.add("is-updated"); setTimeout(() => el.parentElement.classList.remove("is-updated"), 260); }
    }
    if (Array.isArray(fields.sbSignals)) {
      const el = document.getElementById("sbSignals");
      if (el) { el.innerHTML = fields.sbSignals.map(s => `<li>${s}</li>`).join(""); el.parentElement.classList.add("is-updated"); setTimeout(() => el.parentElement.classList.remove("is-updated"), 260); }
    }
    if (Array.isArray(fields.sbNext)) {
      const el = document.getElementById("sbNext");
      if (el) { el.innerHTML = fields.sbNext.map(s => `<li>${s}</li>`).join(""); el.parentElement.classList.add("is-updated"); setTimeout(() => el.parentElement.classList.remove("is-updated"), 260); }
    }
    // Actualizar mini vline según fase
    if (typeof facts.phase === "number") {
      const steps = document.querySelectorAll("#sbVline .vstep");
      steps.forEach((s, i) => {
        const idx = i + 1;
        if (idx < facts.phase) s.dataset.state = "done";
        else if (idx === facts.phase) s.dataset.state = "active";
        else s.removeAttribute("data-state");
      });
    }
  }
  ```

- [ ] **Step 3: Conectar el sidebar al ciclo de chat**

  En la función `enterChat()` (Task 4), justo después de inyectar el HTML del main, añadir:

  ```javascript
  renderSidebarChat({ phase: 2 });
  ```

  En la función `sendMessage()`, dentro del bloque `if (!res.ok)` exitoso (después de `appendTurn("agent", data.reply)`), añadir:

  ```javascript
  // Refresh del sidebar entre turnos (single coherent update)
  if (data.facts) updateSidebarFromTurn({
    focus: data.facts.focus,
    signals: data.facts.signals,
    gaps: data.facts.gaps,
    phase: data.facts.phase,
  });
  // Phase line global
  if (data.facts && typeof data.facts.phase === "number") setPhase(data.facts.phase);
  ```

  Verificar en el JSON real que devuelve `/api/chat` qué campos existen. Adaptar nombres si difieren (`facts.focus` puede llamarse `focus_current`, `signals` puede ser `evidence`, etc.). Hacer un `console.log(data)` durante una vuelta de prueba para descubrir el shape exacto, y ajustar.

- [ ] **Step 4: Verificación visual**

  Iniciar sesión → enviar 2-3 mensajes. Esperado:
  - Sidebar muestra "02 / DISCOVERY EN VIVO" + FOCO + mini vline vertical de 4 fases con la actual en cyan + SEÑALES (lista) + PRÓXIMO (lista en amarillo).
  - Cada bloque que cambia entre turnos tiene una micro-animación slide-in desde la derecha + fade.
  - Mobile (resize a 375px): sidebar pasa a bottom sheet con tira de 60px visible mostrando el FOCO actual. Tap → expande a 60dvh.

- [ ] **Step 5: Commit**

  ```bash
  git add Agente_Real_CRM.html
  git commit -m "$(cat <<'EOF'
  Add three-block contextual sidebar with mobile bottom sheet

  FOCO / SEÑALES / PRÓXIMO with mini vertical phase line. Updates only
  between turns to avoid alert-like flashes. Bottom sheet on mobile keeps
  current focus always visible without competing with chat real estate.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 6: Estado de espera limpio

**Por qué:** Reemplazar el estado "agente pensando" por una barra asintótica + ETA en lugar de texto rotante. Cero ansiedad visual.

**Files:**
- Modify: `Agente_Real_CRM.html` (CSS de waiting; JS para mostrar/esconder waiting card)

- [ ] **Step 1: Añadir CSS del estado de espera**

  Insertar antes de `</style>`:

  ```css
  /* === WAITING STATE === */
  .turn.waiting {
    border: 1px solid var(--rule);
    background: var(--bg-elev);
    padding: 18px 22px;
    max-width: 70%;
    display: grid; gap: 10px;
  }
  .turn.waiting .label {
    color: var(--cyan-2);
  }
  .turn.waiting .cursor {
    display: inline-block; width: 8px; height: 16px;
    background: var(--cyan-2); margin-left: 6px;
    vertical-align: middle;
    animation: cursor-blink 1.2s infinite;
  }
  @keyframes cursor-blink { 50% { opacity: 0; } }

  .wait-bar {
    height: 1px; background: var(--rule-strong); position: relative; overflow: hidden;
  }
  .wait-bar > i {
    display: block; height: 100%;
    background: var(--cyan);
    width: 0%;
    transition: width 600ms ease-out;
  }
  .wait-eta {
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.2em;
    color: var(--ink-muted);
  }
  .wait-extended {
    font-size: var(--t-small);
    color: var(--ink-muted);
    font-style: italic;
  }
  ```

- [ ] **Step 2: JS de gestión de waiting**

  Añadir al `<script>`:

  ```javascript
  /* === WAITING STATE === */
  const ETA_HISTORY = [];
  let _waitTimers = [];

  function showWaitingTurn() {
    const scroll = document.getElementById("chatScroll");
    if (scroll.lastElementChild && !scroll.lastElementChild.classList.contains("turn-separator")) {
      const sep = document.createElement("div");
      sep.className = "turn-separator";
      scroll.appendChild(sep);
    }
    const eta = ETA_HISTORY.length ? Math.round(ETA_HISTORY.reduce((a,b)=>a+b,0) / ETA_HISTORY.length) : 10;
    const turn = document.createElement("div");
    turn.className = "turn waiting";
    turn.id = "waitingTurn";
    turn.dataset.role = "agent";
    turn.innerHTML = `
      <span class="label">Agente <span class="cursor"></span></span>
      <div class="wait-bar"><i></i></div>
      <div class="wait-eta">respondiendo · ~${eta}s</div>
    `;
    scroll.appendChild(turn);
    scroll.scrollTop = scroll.scrollHeight;
    // Asintótico hacia 90% en el ETA
    const fill = turn.querySelector(".wait-bar > i");
    let pct = 0;
    const tick = setInterval(() => {
      pct = pct + (90 - pct) * 0.08;
      fill.style.width = `${Math.min(pct, 90)}%`;
    }, 600);
    // Mensaje extendido a 25s
    const extendedTimer = setTimeout(() => {
      const note = document.createElement("div");
      note.className = "wait-extended";
      note.textContent = "Está pensando una buena pregunta. Aguanta un momento.";
      turn.appendChild(note);
    }, 25000);
    _waitTimers.push(tick, extendedTimer);
    return turn;
  }

  function dismissWaitingTurn(elapsedSeconds) {
    const turn = document.getElementById("waitingTurn");
    _waitTimers.forEach(clearInterval);
    _waitTimers.forEach(clearTimeout);
    _waitTimers = [];
    if (!turn) return;
    const fill = turn.querySelector(".wait-bar > i");
    if (fill) fill.style.width = "100%";
    setTimeout(() => turn.remove(), 200);
    if (typeof elapsedSeconds === "number" && elapsedSeconds > 0) {
      ETA_HISTORY.push(elapsedSeconds);
      if (ETA_HISTORY.length > 3) ETA_HISTORY.shift();
    }
  }
  ```

- [ ] **Step 3: Conectar showWaitingTurn / dismissWaitingTurn al `sendMessage`**

  Modificar la función `sendMessage()` (de Task 4) para llamar a estos helpers:

  ```javascript
  async function sendMessage(text, opts = {}) {
    if (!SESSION.lead_id || !text.trim()) return;
    appendTurn("user", text);
    showWaitingTurn();
    const startTs = performance.now();
    const sendBtn = document.getElementById("sendBtn");
    const composer = document.getElementById("composer");
    sendBtn.disabled = true; sendBtn.innerHTML = "Enviando ▍";
    composer.disabled = true; composer.value = "";
    setSaveStatus("syncing", "GUARDANDO ▍");
    try {
      const body = { lead_id: SESSION.lead_id, message: text };
      if (opts.rewindTo !== undefined) body.rewind_to_turn = opts.rewindTo;
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      const elapsed = (performance.now() - startTs) / 1000;
      dismissWaitingTurn(elapsed);
      if (res.status === 429) {
        appendTurn("agent", data.error || "Estoy con otra sesión. Vuelvo en unos segundos.");
        return;
      }
      if (!res.ok) {
        appendTurn("agent", "No te entrego una respuesta mediocre. Lo retomamos en un momento.");
        return;
      }
      appendTurn("agent", data.reply || "");
      if (data.facts) updateSidebarFromTurn({
        focus: data.facts.focus, signals: data.facts.signals,
        gaps: data.facts.gaps, phase: data.facts.phase,
      });
      if (data.facts && typeof data.facts.phase === "number") setPhase(data.facts.phase);
      setSaveStatus("syncing", "GUARDADO HACE 0s");
    } catch (e) {
      dismissWaitingTurn();
      setSaveStatus("reconnect", "RECONECTANDO ▍");
    } finally {
      sendBtn.disabled = false; sendBtn.innerHTML = `Enviar <span class="arrow">→</span>`;
      composer.disabled = false; composer.focus();
    }
  }
  ```

- [ ] **Step 4: Verificación visual**

  Enviar un mensaje. Esperado:
  - Aparece la card de espera con label "Agente ▍" en cyan y cursor parpadeando.
  - Bajo la label, una barra fina cyan crece desde 0% hasta ~90% durante ~10-12s.
  - Texto mono "respondiendo · ~10s" debajo.
  - Si el agente tarda más de 25s, aparece una línea italic gris "Está pensando una buena pregunta. Aguanta un momento."
  - Al llegar la respuesta, la barra completa al 100%, fade out 200ms, y aparece el turno real del agente.

- [ ] **Step 5: Commit**

  ```bash
  git add Agente_Real_CRM.html
  git commit -m "$(cat <<'EOF'
  Replace agent waiting state with asymptotic progress bar

  Removes rotating mono messages in favor of a 1px progress strip that
  grows asymptotically to 90% with a self-correcting ETA based on rolling
  average of last 3 turn durations. Extended hint after 25s only.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 7: Cola transparente + endpoint `/api/notify-when-free`

**Por qué:** Cuando `MAX_AI_CONCURRENCY=1` está saturado, mostrar posición + ETA + permitir captura de email para notificación posterior.

**Files:**
- Modify: `app_server.py` (añadir cuenta de espera al semáforo + campos en respuesta 429 + nuevo endpoint)
- Modify: `Agente_Real_CRM.html` (UI de cola + composer accesible mientras espera)
- Create: `test_notify_when_free.py`

### Backend primero

- [ ] **Step 1: Test fallido para `/api/notify-when-free`**

  Crear `test_notify_when_free.py`:

  ```python
  #!/usr/bin/env python3
  """Verifica que /api/notify-when-free registre el email y devuelva ok."""
  import json
  import os
  import sqlite3
  import sys
  import urllib.request
  from pathlib import Path

  BASE = os.environ.get("BASE", "http://localhost:8787")


  def post(path, payload):
      req = urllib.request.Request(
          f"{BASE}{path}",
          data=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
          method="POST",
      )
      try:
          with urllib.request.urlopen(req, timeout=10) as resp:
              return resp.status, json.loads(resp.read().decode("utf-8"))
      except urllib.error.HTTPError as e:
          return e.code, json.loads(e.read().decode("utf-8"))


  def main() -> int:
      status, data = post("/api/session", {})
      assert status == 200, f"session failed: {status}"
      lead_id = data["lead_id"]
      status, data = post("/api/notify-when-free", {"lead_id": lead_id, "email": "test+notify@example.com"})
      assert status == 200, f"notify-when-free returned {status}: {data}"
      assert data.get("ok") is True

      # Verificar evento en CRM
      db_path = Path(os.environ.get("CRM_DB", "crm.sqlite3"))
      con = sqlite3.connect(db_path)
      try:
          row = con.execute("SELECT payload FROM events WHERE lead_id = ? AND event = ?", (lead_id, "notify_when_free")).fetchone()
      finally:
          con.close()
      assert row, "notify_when_free event not stored"
      payload = json.loads(row[0])
      assert payload.get("email") == "test+notify@example.com"

      # Email inválido debe ser rechazado
      status, data = post("/api/notify-when-free", {"lead_id": lead_id, "email": "no-arroba"})
      assert status == 400, f"invalid email should 400, got {status}"

      print(json.dumps({"ok": True, "lead_id": lead_id}, indent=2))
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 2: Ejecutar — debe fallar**

  ```bash
  ./run_local_beta.sh
  python3 test_notify_when_free.py
  ```

  Esperado: status 404 (endpoint no existe).

- [ ] **Step 3: Implementar endpoint en `app_server.py`**

  Localizar la lista de rutas en `Handler.do_POST` (cerca de la línea 600+ de `app_server.py`). Añadir un nuevo handler. Reusar `valid_email`, `insert_event`, y opcionalmente `CRM_WEBHOOK_URL`:

  ```python
  # Dentro de Handler.do_POST, en el bloque de routing if/elif:
  elif self.path == "/api/notify-when-free":
      payload = read_json(self)
      lead_id = payload.get("lead_id")
      email = (payload.get("email") or "").strip().lower()
      if not lead_id or not email or not valid_email(email):
          self._json({"error": "Email inválido o lead_id ausente."}, 400)
          return
      lead = self._load_lead_or_404(lead_id)
      if not lead:
          return
      insert_event(lead_id, "notify_when_free", {"email": email, "registered_at": now()})
      # Disparo opcional al webhook si está configurado
      try:
          if CRM_WEBHOOK_URL:
              fire_crm_webhook("notify_when_free", {"lead_id": lead_id, "email": email})
      except Exception:
          pass  # no bloquear UX si el webhook falla
      self._json({"ok": True}, 200)
      return
  ```

  (Si no existe `fire_crm_webhook`, comprobar el nombre real con `grep "def.*webhook" app_server.py` y adaptar.)

- [ ] **Step 4: Re-ejecutar test — debe pasar**

  ```bash
  python3 test_notify_when_free.py
  ```

  Esperado: `{"ok": true, "lead_id": "..."}`.

- [ ] **Step 5: Test fallido para campos `queue_position` y `eta_seconds`**

  Modificar `test_ai_concurrency.py` (existente) para verificar que la respuesta 429 incluya estos campos. Localizar la aserción actual y añadir:

  ```python
  # Tras la aserción existente que valida status==429:
  body = json.loads(resp.read().decode("utf-8"))
  assert "queue_position" in body, f"missing queue_position in 429 body: {body}"
  assert "eta_seconds" in body, f"missing eta_seconds in 429 body: {body}"
  assert isinstance(body["queue_position"], int)
  assert isinstance(body["eta_seconds"], (int, float))
  ```

  Ejecutar:

  ```bash
  python3 test_ai_concurrency.py
  ```

  Esperado: AssertionError "missing queue_position".

- [ ] **Step 6: Implementar campos `queue_position` y `eta_seconds` en `app_server.py`**

  Añadir al inicio de `app_server.py` (cerca de las constantes globales):

  ```python
  # Cuenta de peticiones esperando el semáforo de IA
  _AI_QUEUE_DEPTH = 0
  _AI_QUEUE_LOCK = threading.Lock()
  _AI_TURN_DURATIONS = []  # rolling de últimas 5 duraciones (segundos)
  ```

  Modificar `call_ai` (alrededor de la línea 442) para tracker la cola y la duración. Ejemplo (adaptar al código real):

  ```python
  def call_ai(instructions: str, input_text: str) -> dict:
      global _AI_QUEUE_DEPTH
      with _AI_QUEUE_LOCK:
          _AI_QUEUE_DEPTH += 1
          my_position = _AI_QUEUE_DEPTH  # 1 si soy el único, 2+ si hay otros
      try:
          if not AI_SEMAPHORE.acquire(timeout=AI_QUEUE_TIMEOUT_SECONDS):
              avg = (sum(_AI_TURN_DURATIONS) / len(_AI_TURN_DURATIONS)) if _AI_TURN_DURATIONS else 12
              raise AiBusyError("agent_busy", queue_position=my_position, eta_seconds=int(avg * my_position))
          start = time.monotonic()
          try:
              # ... cuerpo actual de call_ai ...
              return result
          finally:
              dur = time.monotonic() - start
              _AI_TURN_DURATIONS.append(dur)
              if len(_AI_TURN_DURATIONS) > 5:
                  _AI_TURN_DURATIONS.pop(0)
              AI_SEMAPHORE.release()
      finally:
          with _AI_QUEUE_LOCK:
              _AI_QUEUE_DEPTH -= 1
  ```

  Definir/actualizar `AiBusyError`:

  ```python
  class AiBusyError(Exception):
      def __init__(self, message="agent_busy", queue_position=1, eta_seconds=15):
          super().__init__(message)
          self.queue_position = queue_position
          self.eta_seconds = eta_seconds
  ```

  En el handler de `/api/chat` que captura `AiBusyError`, añadir los campos al body:

  ```python
  except AiBusyError as exc:
      insert_event(lead_id, "ai_busy", {"stage": "chat", "error": str(exc), "elapsed_seconds": round(time.monotonic() - started_at, 2)})
      self._json({
          "error": str(exc),
          "queue_position": exc.queue_position,
          "eta_seconds": exc.eta_seconds,
      }, 429)
      return
  ```

- [ ] **Step 7: Re-ejecutar tests**

  ```bash
  python3 test_ai_concurrency.py
  python3 test_notify_when_free.py
  python3 test_rewind_to_turn.py
  ```

  Los tres deben pasar.

### Frontend (UI de cola)

- [ ] **Step 8: CSS de la card de cola**

  Insertar antes de `</style>`:

  ```css
  /* === QUEUE CARD === */
  .turn.queue {
    border: 1px solid var(--refine);
    background: var(--bg-elev);
    padding: 22px;
    display: grid; gap: 14px;
    max-width: 80%;
  }
  .turn.queue .label { color: var(--refine); }
  .turn.queue .pos {
    font-family: var(--font-mono);
    font-size: 14px;
    letter-spacing: 0.2em;
    color: var(--ink-soft);
  }
  .turn.queue .pos b { color: var(--refine); margin-right: 6px; }
  .turn.queue .copy { color: var(--ink-soft); font-size: var(--t-body); line-height: 1.4; }
  .turn.queue .notify-form {
    display: grid; grid-template-columns: 1fr auto; gap: var(--gap-1);
    border: 1px solid var(--rule);
    padding: 12px;
    background: var(--bg-warm);
  }
  .turn.queue .notify-form input {
    background: transparent; border: none; color: var(--ink); font: inherit; font-size: var(--t-body);
  }
  .turn.queue .notify-form input:focus { outline: none; }
  .turn.queue .notify-form button {
    background: var(--cyan); color: var(--bg-deep); border: none;
    font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.2em;
    text-transform: uppercase; padding: 8px 14px; cursor: pointer;
  }
  ```

- [ ] **Step 9: JS de la cola**

  En `sendMessage()`, sustituir el bloque que maneja `res.status === 429` actual por:

  ```javascript
  if (res.status === 429) {
    showQueueTurn(data.queue_position || 1, data.eta_seconds || 30, text, opts);
    return;
  }
  ```

  Añadir al `<script>`:

  ```javascript
  /* === QUEUE TURN === */
  function showQueueTurn(position, etaSeconds, pendingText, sendOpts) {
    const scroll = document.getElementById("chatScroll");
    const turn = document.createElement("div");
    turn.className = "turn queue";
    turn.dataset.role = "agent";
    turn.id = "queueTurn";
    const minutes = Math.max(1, Math.round(etaSeconds / 60));
    turn.innerHTML = `
      <span class="label">Agente — en cola</span>
      <div class="pos"><b>Posición ${position}</b>· espera estimada ~${minutes} min</div>
      <p class="copy">No te muevas: sigo tu sesión sin que tengas que recargar.</p>
      <form class="notify-form" id="notifyForm">
        <input type="email" placeholder="Avísame por email cuando esté libre" aria-label="Email para aviso" />
        <button type="submit">Avisar</button>
      </form>
    `;
    scroll.appendChild(turn);
    scroll.scrollTop = scroll.scrollHeight;
    // Auto-retry con backoff
    setTimeout(() => retryAfterQueue(pendingText, sendOpts), Math.min(etaSeconds * 1000, 30000));
    document.getElementById("notifyForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = e.target.querySelector("input").value.trim();
      if (!email) return;
      const r = await fetch("/api/notify-when-free", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_id: SESSION.lead_id, email }),
      });
      if (r.ok) {
        e.target.innerHTML = `<span class="copy" style="color: var(--proceed);">Te aviso en cuanto el agente esté libre. Puedes cerrar esta pestaña.</span>`;
      }
    });
  }

  async function retryAfterQueue(text, opts) {
    const queueTurn = document.getElementById("queueTurn");
    if (queueTurn) queueTurn.remove();
    sendMessage(text, opts);
  }
  ```

- [ ] **Step 10: Verificación funcional**

  Para forzar el estado de cola sin esperar a saturación real, podemos arrancar dos peticiones simultáneamente. Desde DevTools console:

  ```javascript
  for (let i = 0; i < 2; i++) sendMessage("test concurrencia " + i);
  ```

  Esperado: la segunda petición devuelve 429 y muestra la card de cola con posición 2 y ETA estimada. Tras el ETA, la petición se reintenta sola.

  Probar el formulario de aviso: pegar un email y enviar → respuesta verde "Te aviso en cuanto el agente esté libre".

- [ ] **Step 11: Commit**

  ```bash
  git add Agente_Real_CRM.html app_server.py test_ai_concurrency.py test_notify_when_free.py
  git commit -m "$(cat <<'EOF'
  Expose AI queue depth in 429 responses and add notify-when-free endpoint

  Backend tracks pending requests waiting on the BoundedSemaphore and
  attaches queue_position + eta_seconds to AiBusyError responses. Adds
  POST /api/notify-when-free that registers an email + lead_id in the CRM
  events table and fires CRM_WEBHOOK_URL if configured. Frontend renders
  a queue card with auto-retry and an opt-in email capture for late notify.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 8: Errores honestos (red, IA caída, validación, rate limit)

**Por qué:** Eliminar toasts/modals genéricos. Todo error vive como mensaje del agente o como micro-línea en el top frame.

**Files:**
- Modify: `Agente_Real_CRM.html` (CSS + JS de errores)

- [ ] **Step 1: CSS de variantes de error**

  Insertar antes de `</style>`:

  ```css
  /* === ERROR VARIANTS === */
  .turn.error-net { /* invisible — usamos top frame */ display: none; }
  .turn.error-ai {
    border: 1px solid var(--park);
    background: var(--bg-elev);
    padding: 22px;
    display: grid; gap: 14px;
    max-width: 80%;
  }
  .turn.error-ai .label { color: var(--park); }
  .turn.error-ai .actions { display: flex; gap: var(--gap-2); margin-top: var(--gap-1); }
  .turn.error-ai .actions a {
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-soft);
    text-decoration: underline;
    text-underline-offset: 4px;
  }
  .turn.error-ai .actions a:hover { color: var(--cyan-2); }

  .turn.rate {
    border: 1px solid var(--refine);
    background: var(--bg-elev);
    padding: 18px 22px;
    display: grid; gap: 8px;
    max-width: 70%;
  }
  .turn.rate .label { color: var(--refine); }
  .turn.rate .countdown { font-family: var(--font-mono); color: var(--refine); font-size: 14px; letter-spacing: 0.2em; }

  /* Email invalid (ver Task 10) */
  .field-error { color: var(--ink-muted); font-size: 13px; margin-top: 6px; }
  .field-error[data-state="error"] { color: var(--park); }
  ```

- [ ] **Step 2: JS de error handling**

  Añadir al `<script>`:

  ```javascript
  /* === ERROR HELPERS === */
  let _netRetryCount = 0;
  let _netRetryTimer;

  function flagNetReconnecting() {
    _netRetryCount++;
    setSaveStatus("reconnect", "RECONECTANDO ▍");
    clearTimeout(_netRetryTimer);
    _netRetryTimer = setTimeout(() => {
      if (_netRetryCount >= 3) showAiDownCard();
      else setSaveStatus(null);
    }, 9000);
  }

  function flagNetOk() {
    _netRetryCount = 0;
    setSaveStatus(null);
  }

  function showAiDownCard() {
    const scroll = document.getElementById("chatScroll");
    if (!scroll || scroll.querySelector(".turn.error-ai")) return;
    const turn = document.createElement("div");
    turn.className = "turn error-ai";
    turn.dataset.role = "agent";
    turn.innerHTML = `
      <span class="label">El agente no está disponible ahora</span>
      <p class="copy">No te entrego un diagnóstico mediocre. Cuando vuelva, te aviso yo mismo — o puedes leer un informe de muestra mientras tanto.</p>
      <div class="actions">
        <a href="#" id="aiNotifyMe">Avisarme cuando vuelva →</a>
        <a href="#" id="aiSampleLink">Ver muestra →</a>
      </div>
    `;
    scroll.appendChild(turn);
    scroll.scrollTop = scroll.scrollHeight;
    document.getElementById("aiNotifyMe").addEventListener("click", (e) => {
      e.preventDefault();
      // Reusa el formulario notify de Task 7 directamente
      showQueueTurn(0, 60, null, null);  // posición 0 = no en cola, solo notificar
    });
    document.getElementById("aiSampleLink").addEventListener("click", (e) => {
      e.preventDefault();
      window.open("/r/sample", "_blank");  // si no existe ruta, sustituir por modal
    });
  }

  function showRateLimitTurn(seconds = 30) {
    const scroll = document.getElementById("chatScroll");
    const turn = document.createElement("div");
    turn.className = "turn rate";
    turn.dataset.role = "agent";
    turn.innerHTML = `
      <span class="label">Pausa breve</span>
      <p class="copy">Estás yendo muy rápido. Sigo en <span class="countdown">${seconds}s</span>.</p>
    `;
    scroll.appendChild(turn);
    scroll.scrollTop = scroll.scrollHeight;
    const countdown = turn.querySelector(".countdown");
    let remaining = seconds;
    const composer = document.getElementById("composer");
    const sendBtn = document.getElementById("sendBtn");
    if (composer) composer.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    const interval = setInterval(() => {
      remaining--;
      if (countdown) countdown.textContent = `${remaining}s`;
      if (remaining <= 0) {
        clearInterval(interval);
        turn.remove();
        if (composer) { composer.disabled = false; composer.focus(); }
        if (sendBtn) sendBtn.disabled = false;
      }
    }, 1000);
  }
  ```

- [ ] **Step 3: Conectar al `sendMessage`**

  En `sendMessage()`, ajustar el manejo de errores no-OK y de catch:

  ```javascript
  // Dentro del try/catch:
  if (res.status === 429 && data.queue_position) {
    showQueueTurn(data.queue_position, data.eta_seconds || 30, text, opts);
    return;
  }
  if (res.status === 429) {
    // 429 sin queue_position = rate limit clásico
    showRateLimitTurn(30);
    return;
  }
  if (res.status === 502 || res.status === 503) {
    showAiDownCard();
    return;
  }
  if (!res.ok) {
    appendTurn("agent", "No te entrego una respuesta mediocre. Lo retomamos en un momento.");
    return;
  }
  // ... resto exitoso ...
  flagNetOk();
  // En el catch:
  } catch (e) {
    dismissWaitingTurn();
    flagNetReconnecting();
  }
  ```

- [ ] **Step 4: Verificación**

  - **Net error**: en DevTools → Network, simular "Offline" y enviar mensaje. Esperado: top frame muestra "RECONECTANDO ▍" en cyan. Tras tres intentos fallidos (~27s), aparece la card "El agente no está disponible ahora" con dos salidas.
  - **AI down**: en DevTools console, `fetch = () => Promise.resolve({ ok: false, status: 502, json: () => ({}) });`, enviar mensaje. Esperado: aparece card error-ai inmediatamente.
  - **Rate limit clásico**: simular respuesta 429 sin `queue_position`. Esperado: card amarilla con countdown, composer bloqueado.

- [ ] **Step 5: Commit**

  ```bash
  git add Agente_Real_CRM.html
  git commit -m "$(cat <<'EOF'
  Add honest error states for net, AI-down and rate-limit

  Errors now live as agent turns or top-frame micro-lines, never as
  toasts. Net error retries silently for ~9s; only after three failures
  it escalates to a card. AI-down offers a notify-me path and a sample
  report fallback. Classic 429 (no queue_position) shows an amber card
  with a countdown and locks the composer.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 9: Restauración de sesión

**Por qué:** Recargar la página debe sentirse como continuación natural, no como reinicio. Mostrar última pregunta del agente + dos opciones explícitas.

**Files:**
- Modify: `Agente_Real_CRM.html` (JS de check-on-load + render de welcome-back)
- Modify: `test_session_restore_flow.py`

- [ ] **Step 1: JS de detección y render**

  Añadir al `<script>`, justo después del `setSaveStatus` helper de Task 2:

  ```javascript
  /* === SESSION RESTORE === */
  async function tryRestoreSession() {
    const stored = localStorage.getItem("primer_empleado_lead_id");
    if (!stored) return false;
    try {
      const res = await fetch(`/api/lead?id=${encodeURIComponent(stored)}`, { method: "GET" });
      if (!res.ok) return false;
      const lead = await res.json();
      if (!lead || !lead.transcript || lead.transcript.length === 0) return false;
      const lastAgent = [...lead.transcript].reverse().find(m => m.role === "assistant");
      renderWelcomeBack(lead, lastAgent);
      SESSION.lead_id = lead.lead_id || lead.id || stored;
      return true;
    } catch (e) { return false; }
  }

  function renderWelcomeBack(lead, lastAgent) {
    const main = document.getElementById("mainStage");
    main.innerHTML = `
      <section class="starter" id="starter">
        <div class="eyebrow">Bienvenido de vuelta</div>
        <p class="hero-lead">Seguíamos en:</p>
        <div class="turn" data-role="agent" data-short="${(lastAgent?.content || '').length <= 120}">
          <span class="label">Agente</span>
          <div class="body">${(lastAgent?.content || '').replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]))}</div>
        </div>
        <div style="display: flex; gap: var(--gap-2); margin-top: var(--gap-3);">
          <button type="button" class="cta-primary" id="continueSession">Continuar <span class="arrow">→</span></button>
          <button type="button" class="sample-link" id="resetSession">Empezar de cero</button>
        </div>
      </section>
    `;
    requestAnimationFrame(() => main.querySelector(".starter").classList.add("is-revealed"));
    document.getElementById("continueSession").addEventListener("click", () => {
      enterChat();
      // Re-render del transcript completo
      const scroll = document.getElementById("chatScroll");
      lead.transcript.forEach(m => appendTurn(m.role === "assistant" ? "agent" : "user", m.content));
    });
    document.getElementById("resetSession").addEventListener("click", () => {
      localStorage.removeItem("primer_empleado_lead_id");
      location.reload();
    });
  }
  ```

- [ ] **Step 2: Persistir el lead_id al iniciar sesión**

  En el handler del CTA "Empezar conversación" (Task 4), tras `SESSION.lead_id = data.lead_id;`, añadir:

  ```javascript
  localStorage.setItem("primer_empleado_lead_id", SESSION.lead_id);
  ```

- [ ] **Step 3: Llamar a tryRestoreSession al cargar**

  Reemplazar el bloque de starter reveal de Task 3 por:

  ```javascript
  /* === BOOT === */
  (async () => {
    const restored = await tryRestoreSession();
    if (!restored) {
      requestAnimationFrame(() => {
        const starter = document.getElementById("starter");
        if (starter) starter.classList.add("is-revealed");
      });
    }
  })();
  ```

- [ ] **Step 4: Verificación**

  - Iniciar sesión y enviar 1-2 mensajes.
  - Recargar `http://localhost:8787/Agente_Real_CRM.html`. Esperado: aparece pantalla "Bienvenido de vuelta" con la última pregunta del agente y dos botones.
  - Click "Continuar" → entra al chat con el transcript reconstruido.
  - Recargar y click "Empezar de cero" → vuelve al starter inicial.

- [ ] **Step 5: Actualizar `test_session_restore_flow.py`**

  Buscar el texto antiguo (probablemente "RETOMANDO TU DISCOVERY" o similar) y reemplazarlo por:

  ```python
  page.get_by_text("Bienvenido de vuelta").wait_for(timeout=5000)
  page.get_by_role("button", name="Continuar").click()
  ```

  Ejecutar:

  ```bash
  python3 test_session_restore_flow.py --base http://localhost:8787
  ```

  Iterar hasta verde.

- [ ] **Step 6: Commit**

  ```bash
  git add Agente_Real_CRM.html test_session_restore_flow.py
  git commit -m "$(cat <<'EOF'
  Welcome users back with last agent turn and explicit choices

  Replaces the cryptic ID-based resume message with the actual last
  question from the agent and two explicit buttons (continue / restart).
  Lead_id persists in localStorage to support reloads.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 10: Email-gate con preview parcial

**Por qué:** Mostrar el valor antes de pedir el email. Render de secciones 01 y 03 del informe inline; el email-gate aparece debajo, no encima.

**Files:**
- Modify: `Agente_Real_CRM.html` (CSS + JS del email-gate y preview parcial)
- Modify: `test_public_report_flow.py`

- [ ] **Step 1: CSS del email-gate**

  Insertar antes de `</style>`:

  ```css
  /* === EMAIL GATE === */
  .gate-card {
    border: 1px solid var(--rule-strong);
    background: var(--bg-elev);
    padding: var(--gap-3);
    display: grid; gap: var(--gap-2);
    margin-top: var(--gap-3);
  }
  .gate-card .gate-eyebrow { /* hereda .eyebrow */ }
  .gate-card .gate-title {
    font-family: var(--font-display);
    font-size: var(--t-h2);
    line-height: 1.1; letter-spacing: -0.02em;
    color: var(--ink); margin: 0;
    text-wrap: balance;
  }
  .gate-card .gate-lead { font-style: italic; color: var(--ink-soft); margin: 0; }
  .gate-card .field {
    display: grid; gap: 6px;
  }
  .gate-card .field label {
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }
  .gate-card .field input {
    background: transparent;
    border: none;
    border-bottom: 1px dashed var(--rule);
    color: var(--ink);
    font-family: var(--font-display);
    font-size: clamp(20px, 2.2vw, 24px);
    padding: 8px 0;
  }
  .gate-card .field input:focus { outline: none; border-bottom: 1px solid var(--cyan); }
  .gate-card .field.is-error input { border-bottom-color: var(--park); }
  .gate-card .trust { color: var(--proceed); font-size: 13px; font-family: var(--font-mono); letter-spacing: 0.18em; text-transform: uppercase; }
  .gate-card details { color: var(--ink-muted); font-size: 13px; }
  .gate-card details summary { cursor: pointer; font-family: var(--font-mono); letter-spacing: 0.18em; text-transform: uppercase; }
  .gate-card details p { margin-top: 8px; line-height: 1.4; }

  /* Preview parcial inline en chat */
  .report-preview {
    border-top: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
    padding: var(--gap-3) 0;
    margin: var(--gap-3) 0;
    display: grid; gap: var(--gap-3);
  }
  .report-preview .section { display: grid; gap: 8px; }
  .report-preview .section .num {
    font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.22em; color: var(--cyan-2);
  }
  .report-preview .section h2 {
    font-family: var(--font-display); font-size: clamp(24px, 3vw, 36px);
    color: var(--ink); margin: 0; line-height: 1.1; letter-spacing: -0.02em;
  }
  .report-preview .section p { color: var(--ink-soft); line-height: 1.5; margin: 0; }
  ```

- [ ] **Step 2: JS para detectar `report_ready` y renderizar preview + gate**

  Añadir al `<script>`. La señal de "informe listo" debe venir del backend; verificar en el JSON real qué campo lo indica (probablemente `data.ready_for_report === true` en la respuesta de chat). Adaptar al campo real:

  ```javascript
  /* === REPORT PREVIEW + EMAIL GATE === */
  function maybeShowEmailGate(data) {
    if (!data || !data.ready_for_report) return false;
    setPhase(3);
    const scroll = document.getElementById("chatScroll");
    // Render preview parcial (secciones 01 y 03 del JSON del informe inline si vinieron)
    const preview = data.report_preview || data.report; // adaptar
    if (preview) {
      const node = document.createElement("section");
      node.className = "report-preview";
      node.innerHTML = `
        <div class="section">
          <span class="num">01 / Resumen de acción</span>
          <h2>${escapeHtml(preview.headline || preview.summary || "Aquí está tu primer empleado IA recomendado.")}</h2>
        </div>
        <div class="section">
          <span class="num">03 / Por qué empezar aquí</span>
          <p>${escapeHtml(preview.recommendation_reason || preview.reason || "")}</p>
        </div>
      `;
      scroll.appendChild(node);
    }
    // Gate
    const gate = document.createElement("section");
    gate.className = "gate-card";
    gate.id = "emailGate";
    gate.innerHTML = `
      <div class="eyebrow">El agente tiene una recomendación</div>
      <h2 class="gate-title">He convertido tu caso en un primer empleado IA viable.</h2>
      <p class="gate-lead">— Dime a qué email te lo envío y te abro el informe completo. Una sola vez. Sin newsletter automática.</p>
      <div class="field" id="emailField">
        <label for="emailInput">Email</label>
        <input type="email" id="emailInput" autocomplete="email" placeholder="tu@email.com" />
        <div class="field-error" id="emailFieldError"></div>
      </div>
      <button class="cta-primary" id="emailSubmit" type="button">Recibir informe completo <span class="arrow">→</span></button>
      <div class="trust">— Una sola vez. Sin newsletter automática.</div>
      <details><summary>¿Por qué pido el email?</summary><p>Para entregarte el informe completo y, si quieres, escribirte una vez con la siguiente acción. No te suscribo a ninguna lista. Lee la política de privacidad.</p></details>
    `;
    scroll.appendChild(gate);
    scroll.scrollTop = scroll.scrollHeight;
    const input = document.getElementById("emailInput");
    const errorEl = document.getElementById("emailFieldError");
    const fieldEl = document.getElementById("emailField");
    input.addEventListener("blur", () => {
      const v = input.value.trim();
      if (!v) return;
      const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
      fieldEl.classList.toggle("is-error", !valid);
      errorEl.textContent = valid ? "" : "Ese email no parece válido.";
      errorEl.dataset.state = valid ? "" : "error";
    });
    document.getElementById("emailSubmit").addEventListener("click", () => requestReport(input.value.trim()));
    return true;
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[<>&"]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"}[c]));
  }

  async function requestReport(email) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return;
    setSaveStatus("syncing", "GENERANDO INFORME ▍");
    try {
      const res = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_id: SESSION.lead_id, email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "report_failed");
      renderReportInline(data); // ver Task 11
    } catch (e) {
      setSaveStatus("reconnect", "REINTENTANDO ▍");
    }
  }
  ```

- [ ] **Step 3: Conectar al `sendMessage`**

  En el bloque exitoso de `sendMessage()` (después de `appendTurn("agent", data.reply)`), añadir:

  ```javascript
  if (maybeShowEmailGate(data)) {
    document.getElementById("composer").disabled = true;
    document.getElementById("sendBtn").disabled = true;
  }
  ```

- [ ] **Step 4: Verificación funcional**

  Hacer una sesión completa de discovery hasta que el agente decida que tiene suficiente. Esperado:
  - Tras el último turno del agente, aparecen las secciones 01 y 03 del informe inline.
  - Debajo, la card del email-gate con el campo dashed-underline y los CTAs.
  - Phase line del top frame avanza a fase 03.
  - Validación on-blur: escribir "no-arroba" + Tab → línea pasa a roja con texto "Ese email no parece válido." Escribir email válido → línea cyan, sin error.
  - Click en `<details>` "¿Por qué pido el email?" → expande la explicación.

- [ ] **Step 5: Actualizar `test_public_report_flow.py`**

  Buscar selectores del email-gate antiguo y actualizarlos. El test debe poder:
  - Detectar que las secciones 01 y 03 del preview son visibles antes del email-gate.
  - Encontrar el input por `aria-label` "Email" o por id `emailInput`.
  - Verificar el botón `Recibir informe completo`.

- [ ] **Step 6: Commit**

  ```bash
  git add Agente_Real_CRM.html test_public_report_flow.py
  git commit -m "$(cat <<'EOF'
  Show partial report preview before asking for email

  Sections 01 and 03 render inline in the chat flow when the agent flags
  ready_for_report, then the email gate appears below. On-blur validation,
  collapsible privacy explanation, trust signal in proceed-green.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 11: Informe editorial inline (fase 04)

**Por qué:** Render del informe completo como secuencia editorial dentro del flujo, con índice sticky por etiquetas, feedback siempre visible y compartir vía private link.

**Files:**
- Modify: `Agente_Real_CRM.html` (CSS + JS del render del informe)

- [ ] **Step 1: CSS del informe**

  Insertar antes de `</style>`:

  ```css
  /* === REPORT === */
  .report {
    display: grid; gap: var(--gap-4);
    padding-top: var(--gap-3);
  }
  .report-sticky {
    position: sticky; top: 0; z-index: 5;
    background: var(--bg);
    padding: var(--gap-2) 0;
    border-bottom: 1px solid var(--rule);
    display: grid;
    grid-template-columns: 1fr auto auto;
    align-items: center;
    gap: var(--gap-2);
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 0.18em;
  }
  .report-sticky .index { display: flex; gap: var(--gap-2); flex-wrap: wrap; color: var(--ink-muted); }
  .report-sticky .index a { color: inherit; text-decoration: none; cursor: pointer; }
  .report-sticky .index a[data-active="true"] { color: var(--cyan-2); }
  .report-sticky .read-time { color: var(--ink-faint); }
  .report-sticky .actions { display: flex; gap: var(--gap-2); }
  .report-sticky .actions button {
    background: transparent; border: 1px solid var(--rule-strong);
    color: var(--ink-soft); padding: 6px 10px;
    font: inherit; font-size: 11px; letter-spacing: 0.18em;
    text-transform: uppercase; cursor: pointer;
  }
  .report-sticky .actions button:hover { color: var(--cyan-2); border-color: var(--cyan); }
  .report-sticky .feedback { display: flex; gap: 6px; }
  .report-sticky .feedback .pill {
    border: 1px solid var(--rule-strong); padding: 4px 10px;
    font-size: 11px; letter-spacing: 0.18em; cursor: pointer;
    background: transparent; color: var(--ink-soft);
  }
  .report-sticky .feedback .pill[data-selected="true"] { background: var(--cyan); color: var(--bg-deep); border-color: var(--cyan); }

  .report-section {
    display: grid; gap: var(--gap-2);
    opacity: 0; transform: translateY(12px);
    transition: opacity 500ms var(--ease), transform 500ms var(--ease);
  }
  .report-section.is-visible { opacity: 1; transform: none; }
  .report-section .num { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.22em; color: var(--cyan-2); }
  .report-section h2 {
    font-family: var(--font-display); font-size: var(--t-h2);
    line-height: 1.05; letter-spacing: -0.02em;
    color: var(--ink); margin: 0;
  }
  .report-section h3 { font-family: var(--font-display); font-size: clamp(22px, 2.4vw, 28px); margin: 0; color: var(--ink); }
  .report-section p { color: var(--ink-soft); line-height: 1.5; margin: 0; }
  .report-section ul { padding-left: 20px; color: var(--ink-soft); line-height: 1.5; margin: 0; }
  .report-section ul li { margin-bottom: 6px; }

  .report-lanes { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--gap-2); }
  .report-lane { border: 1px solid var(--rule); padding: var(--gap-2); display: grid; gap: var(--gap-1); }
  .report-lane.proceed { border-color: var(--proceed); }
  .report-lane.refine  { border-color: var(--refine); }
  .report-lane.park    { border-color: var(--park); }
  .report-lane h3 { font-size: clamp(20px, 2vw, 24px); }
  .report-lane.proceed h3 { color: var(--proceed); }
  .report-lane.refine  h3 { color: var(--refine); }
  .report-lane.park    h3 { color: var(--park); }
  @media (max-width: 800px) { .report-lanes { grid-template-columns: 1fr; } }

  .report-timeline { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--gap-2); border-top: 1px solid var(--rule-strong); padding-top: var(--gap-2); }
  .report-timeline .stop { display: grid; gap: 6px; }
  .report-timeline .stop .num { color: var(--ink-muted); }
  .report-timeline .stop h4 { font-family: var(--font-display); font-size: clamp(18px, 1.8vw, 22px); margin: 0; color: var(--ink); }
  .report-timeline .stop p { font-size: 14px; color: var(--ink-muted); margin: 0; }

  @media print {
    .report-sticky { display: none !important; }
    .report-section { opacity: 1 !important; transform: none !important; page-break-inside: avoid; }
  }
  ```

- [ ] **Step 2: JS de render del informe**

  Añadir al `<script>`:

  ```javascript
  /* === REPORT RENDERING === */
  function renderReportInline(report) {
    setPhase(4);
    const main = document.getElementById("mainStage");
    const wordCount = JSON.stringify(report).split(/\s+/).length;
    const minutes = Math.max(2, Math.round(wordCount / 200));
    const sections = [
      { num: "01", label: "Resumen", title: "Resumen de acción", body: report.summary || report.headline || "" },
      { num: "02", label: "Por qué", title: "Lo que he entendido", body: report.business_snapshot || "" },
      { num: "03", label: "Razón", title: "Por qué empezar aquí", body: report.recommendation_reason || "" },
      { num: "04", label: "Señales", title: "Señales detectadas", list: report.evidence_summary || [] },
      { num: "05", label: "Lanes", title: "Oportunidades prioritarias", lanes: report.opportunities || [] },
      { num: "06", label: "No aún", title: "No automatizar todavía", list: report.do_not_automate_yet || [] },
      { num: "07", label: "Plan 7d", title: "Plan de 7 días", timeline: report.seven_day_plan || [] },
      { num: "08", label: "Plan 30d", title: "Plan de 30 días", timeline: report.thirty_day_plan || [] },
      { num: "09", label: "Próximo", title: "Siguiente paso recomendado", body: report.cta?.message || "" },
    ];
    const indexHtml = sections.map(s => `<a data-target="sec-${s.num}">${s.label}</a>`).join("·");
    main.innerHTML = `
      <header class="report-sticky">
        <div class="read-time">Lectura · ${minutes} min</div>
        <nav class="index">${indexHtml}</nav>
        <div class="actions">
          <button id="copyLinkBtn">Copiar enlace privado</button>
          <button onclick="window.print()">⌘P</button>
        </div>
        <div class="feedback">
          <button class="pill" data-feedback="util">Útil</button>
          <button class="pill" data-feedback="regular">Regular</button>
          <button class="pill" data-feedback="poco">Poco útil</button>
        </div>
      </header>
      <section class="report" id="reportRoot">
        ${sections.map(s => renderSection(s)).join("")}
      </section>
    `;
    // IntersectionObserver para reveal + active index
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(en => {
        if (en.isIntersecting) {
          en.target.classList.add("is-visible");
          const id = en.target.id;
          document.querySelectorAll(".report-sticky .index a").forEach(a => {
            a.dataset.active = a.dataset.target === id ? "true" : "false";
          });
        }
      });
    }, { threshold: 0.2, rootMargin: "0px 0px -20% 0px" });
    document.querySelectorAll(".report-section").forEach(s => obs.observe(s));
    // Index click → scroll
    document.querySelectorAll(".report-sticky .index a").forEach(a => {
      a.addEventListener("click", () => {
        const target = document.getElementById(a.dataset.target);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
    // Copy private link
    document.getElementById("copyLinkBtn").addEventListener("click", async (e) => {
      const url = `${location.origin}/r/${SESSION.lead_id}/${report.private_token || ""}`;
      try { await navigator.clipboard.writeText(url); e.target.textContent = "Enlace copiado ✓"; } catch (err) {}
      setTimeout(() => { e.target.textContent = "Copiar enlace privado"; }, 2400);
    });
    // Feedback
    document.querySelectorAll(".report-sticky .feedback .pill").forEach(pill => {
      pill.addEventListener("click", async () => {
        document.querySelectorAll(".report-sticky .feedback .pill").forEach(p => p.dataset.selected = "false");
        pill.dataset.selected = "true";
        await fetch("/api/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lead_id: SESSION.lead_id, feedback: pill.dataset.feedback }),
        });
      });
    });
  }

  function renderSection(s) {
    let body = "";
    if (s.body) body = `<p>${escapeHtml(s.body)}</p>`;
    if (s.list && s.list.length) body = `<ul>${s.list.map(it => `<li>${escapeHtml(typeof it === "string" ? it : it.text || JSON.stringify(it))}</li>`).join("")}</ul>`;
    if (s.lanes && s.lanes.length) {
      const buckets = { proceed: [], refine: [], park: [] };
      s.lanes.forEach(o => {
        const cls = o.verdict === "PROCEED" ? "proceed" : o.verdict === "REFINE" ? "refine" : "park";
        buckets[cls].push(o);
      });
      body = `<div class="report-lanes">
        ${["proceed","refine","park"].map(k => `
          <article class="report-lane ${k}">
            <h3>${k.toUpperCase()}</h3>
            ${buckets[k].map(o => `<p>${escapeHtml(o.title || o.name || "")}</p>`).join("")}
          </article>
        `).join("")}
      </div>`;
    }
    if (s.timeline && s.timeline.length) {
      body = `<div class="report-timeline">${s.timeline.map((t, i) => `
        <div class="stop">
          <span class="num">DÍA ${i+1}</span>
          <h4>${escapeHtml(typeof t === "string" ? t : t.title || "")}</h4>
          ${typeof t === "object" && t.detail ? `<p>${escapeHtml(t.detail)}</p>` : ""}
        </div>
      `).join("")}</div>`;
    }
    return `<section class="report-section" id="sec-${s.num}">
      <span class="num">${s.num} / ${s.label}</span>
      <h2>${escapeHtml(s.title)}</h2>
      ${body}
    </section>`;
  }
  ```

- [ ] **Step 3: Verificación**

  Completar una sesión hasta el informe. Esperado:
  - Phase line en fase 04.
  - Sticky frame arriba con `Lectura · N min` + índice horizontal con etiquetas + botones "Copiar enlace privado" / "⌘P" + 3 mini-pills de feedback.
  - 9 secciones del informe debajo, cada una hace fade-up al entrar en viewport.
  - Click en una etiqueta del índice → scroll suave a la sección.
  - Click en una etiqueta de feedback → marca seleccionada, envío al backend.
  - Imprimir (⌘P o botón) → preview con los colores dark conservados, sin sticky frame.

- [ ] **Step 4: Re-ejecutar `test_public_report_flow.py`**

  Actualizar selectores: el informe ya no es modal, vive en `#reportRoot`. Las secciones tienen IDs `sec-01` a `sec-09`. El feedback son `.pill` con `data-feedback`.

- [ ] **Step 5: Commit**

  ```bash
  git add Agente_Real_CRM.html test_public_report_flow.py
  git commit -m "$(cat <<'EOF'
  Render report inline as 9 editorial sections with sticky toolbar

  Replaces the modal report with an in-flow vertical sequence using
  lanes, timeline and section cards from the spec. Sticky toolbar holds
  reading time, label index, copy-private-link, print and feedback pills.
  IntersectionObserver reveals each section on scroll and tracks the
  active index entry.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

---

## Task 12: Accesibilidad transversal y cierre

**Por qué:** Auditar y endurecer focus, ARIA, contraste, tap targets y motion-reduce. Es el último filtro antes de declarar done.

**Files:**
- Modify: `Agente_Real_CRM.html` (refinamientos puntuales)

- [ ] **Step 1: Auditoría de focus**

  Recorrer la app con Tab desde el starter. Todos los interactivos deben tener un focus ring visible (`outline: 2px solid var(--cyan-2)`). Si alguno se lo come (botón `.cta-primary`, `.icon-btn`, `.pill`, `.sample-link`, `.edit-handle`), añadir manualmente `:focus-visible` con el outline.

- [ ] **Step 2: Verificar `aria-live`**

  - El `chatScroll` ya tiene `aria-live="polite"` (Task 4). Confirmar.
  - El `saveStatus` ya tiene `aria-live="polite"` (Task 2). Confirmar.
  - Añadir `aria-live="polite"` al bloque FOCO del sidebar (Task 5):

    ```html
    <div class="block-value" id="sbFoco" aria-live="polite">...</div>
    ```

- [ ] **Step 3: Tap targets**

  Verificar en Chrome DevTools (modo móvil) que todos los botones e inputs tienen al menos 44×44px efectivos. Donde no, ajustar `padding`. Sospechosos: las `.pill` del feedback (suben fácilmente con `padding: 8px 14px`), los `.edit-handle` de turnos.

- [ ] **Step 4: Auditar contraste**

  Abrir DevTools → Lighthouse → Accessibility. Esperado: score ≥ 95. Si reporta contraste insuficiente:
  - `.eyebrow` muted en `--ink-muted` puede fallar en tamaños <14px → forzar `--ink-soft` en esos casos.
  - `.muted` en cuerpos largos: cambiar a `--ink-soft`.

- [ ] **Step 5: Probar `prefers-reduced-motion`**

  En DevTools → Rendering → Emulate CSS media: `prefers-reduced-motion: reduce`. Recargar y recorrer toda la app. Esperado: cero animaciones de transform; opacity-only o instantáneo. La regla global del Task 1 lo cubre, verificar que ninguna animación lo evade.

- [ ] **Step 6: Smoke completo**

  ```bash
  ./run_local_beta.sh
  python3 local_acceptance_check.py
  ```

  Esperado: pasa sin errores. Si falla, leer el output, identificar el test específico, ajustar o aceptar la regresión documentada.

- [ ] **Step 7: Commit**

  ```bash
  git add Agente_Real_CRM.html
  git commit -m "$(cat <<'EOF'
  Harden accessibility: focus rings, aria-live, contrast and tap targets

  Final pass to ensure all interactives have a visible focus indicator,
  live regions announce updates to screen readers, contrast meets AA
  on body text, tap targets are >=44px on mobile and prefers-reduced-
  motion is honored across all animations.

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

- [ ] **Step 8: Marcador final del proyecto**

  Resumen del estado tras este plan:

  - 12 commits aditivos sobre `origin/main`.
  - `Agente_Real_CRM.html` reescrito con sistema editorial dark IA al Día.
  - `app_server.py` con 2 cambios aditivos (`rewind_to_turn` + cola transparente) y 1 endpoint nuevo (`/api/notify-when-free`).
  - 4 tests actualizados, 2 tests nuevos (`test_rewind_to_turn.py`, `test_notify_when_free.py`).
  - Cero cambios a CRM, prototipos antiguos, despliegue VPS o página de privacidad.

  Actualizar el `COMPLETION_AUDIT.md` con una nota breve sobre el redesign si procede.

---

## Self-review notes

Cobertura del spec:
- §3 Sistema de diseño → Task 1.
- §4 Layout macro → Task 2.
- §5 Starter → Task 3.
- §6 Chat → Tasks 4 + 5.
- §7 Email-gate con preview parcial → Task 10.
- §8 Informe editorial → Task 11.
- §9 Estados → Tasks 6 + 7 + 8 + 9.
- §10 Accesibilidad → Task 12 (también hilada en cada task).
- §11 Performance → Task 1 (anti-FOUT, tokens, IntersectionObserver implícito en Tasks 11+).
- §12 Cambios al backend → Tasks 4 + 7.
- §13 Tests → ajustes inline en cada task.
- §14 Orden de implementación → coincide con Tasks 1-12.
- §15 Fuera de scope → no aparece en ningún task.

Nada queda como "TBD" o "implement later". Cada step tiene código real o comando exacto. Los nombres de funciones JS (`enterChat`, `sendMessage`, `appendTurn`, `rewindToTurn`, `setPhase`, `setSaveStatus`, `renderSidebarChat`, `updateSidebarFromTurn`, `showWaitingTurn`, `dismissWaitingTurn`, `showQueueTurn`, `retryAfterQueue`, `flagNetReconnecting`, `flagNetOk`, `showAiDownCard`, `showRateLimitTurn`, `tryRestoreSession`, `renderWelcomeBack`, `maybeShowEmailGate`, `requestReport`, `renderReportInline`, `renderSection`, `escapeHtml`) son consistentes a lo largo del plan.

**Warning conocido:** los nombres de campos del JSON del backend (`facts.focus`, `facts.signals`, `facts.gaps`, `data.ready_for_report`, `data.report_preview`, `report.cta.message`, `report.opportunities[i].verdict`, `report.private_token`) están **asumidos** desde el README y no verificados turn-by-turn en el código real de `app_server.py`. El primer task que los toca (Task 5) instruye explícitamente a `console.log(data)` y adaptar. Esto es el único punto del plan donde la verificación contra el código real se difiere a la ejecución.
