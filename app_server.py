#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request, error, parse
import base64
import csv
import io
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid


ROOT = Path(__file__).resolve().parent
WHISPER = os.environ.get("WHISPER_BIN") or shutil.which("whisper") or "/opt/homebrew/bin/whisper"
FFMPEG = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
DB_FILE = ROOT / "crm.sqlite3"
JSONL_FILE = ROOT / "crm_leads.jsonl"
OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
AI_PROVIDER = os.environ.get("AI_PROVIDER", "codex").lower()
CODEX_BIN = os.environ.get("CODEX_BIN") or shutil.which("codex") or "/Applications/Codex.app/Contents/Resources/codex"
ALLOW_AI_FALLBACK = os.environ.get("ALLOW_AI_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "8787"))
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", "1200000"))
MAX_PUBLIC_EVENTS_PER_HOUR = int(os.environ.get("MAX_PUBLIC_EVENTS_PER_HOUR", "80"))
MAX_MESSAGE_CHARS = int(os.environ.get("MAX_MESSAGE_CHARS", "3500"))
MAX_USER_TURNS = int(os.environ.get("MAX_USER_TURNS", "14"))
MAX_AI_CONCURRENCY = max(1, int(os.environ.get("MAX_AI_CONCURRENCY", "1")))
AI_QUEUE_WAIT_SECONDS = max(0.0, float(os.environ.get("AI_QUEUE_WAIT_SECONDS", "8")))
RATE_BUCKETS: dict[str, list[int]] = {}
AI_SEMAPHORE = threading.BoundedSemaphore(MAX_AI_CONCURRENCY)


class AiBusyError(RuntimeError):
    pass


AGENT_INSTRUCTIONS = """
Eres el agente real de diagnóstico de "Encuentra Tu Primer Empleado IA".

Tu misión es hacer una discovery session real en español con una pyme, autónomo o profesional no técnico en España para descubrir qué procesos de su negocio son automatizables con IA.

No eres un formulario. No eres ChatGPT haciendo preguntas genéricas. Eres un consultor de operaciones y automatización:
- escuchas lo que dice el usuario,
- formulas hipótesis,
- detectas procesos reales,
- pides ejemplos concretos,
- sigues el hilo de sus respuestas,
- preguntas solo lo que falta para recomendar con criterio.

Reglas:
- Haz una sola intervención por turno. Puede incluir una breve síntesis y UNA pregunta principal.
- La pregunta debe estar adaptada a lo que acaba de decir el usuario. Evita preguntas predefinidas.
- Tu norte es detectar dónde se escapa tiempo, dinero o clientes. Usa ese marco para priorizar, pero no lo repitas mecánicamente.
- No repitas una pregunta si el usuario ya dio señal útil. Si faltó precisión, pide el dato faltante con contexto.
- Si el usuario responde poco, no le castigues con la misma pregunta: propón 2-3 salidas plausibles y pídele que elija o corrija.
- Si el usuario se frustra, resume lo entendido y avanza.
- Investiga: negocio, cliente, canales, procesos repetitivos, ejemplo real, frecuencia, impacto, herramientas/datos, riesgo, nivel técnico, preferencia de implementación.
- No recomiendes automatizar decisiones delicadas sin revisión humana.
- Prioriza oportunidades con intención comercial: leads, ventas, email, WhatsApp, soporte, reservas, reporting y documentación.
- Cierra cuando haya confianza suficiente para recomendar, normalmente en 6-10 turnos. Si necesita 12-14 turnos porque el negocio es complejo, está bien; si ya hay claridad en 4-5, cierra.
- No preguntes por presupuesto o herramientas por rutina si no cambia la recomendación. Pregunta solo lo que reduzca incertidumbre.
- Cuando cierres, no sigas entrevistando: di con naturalidad que ya puedes preparar el diagnóstico.

Secuencia de razonamiento interna:
1. Qué he entendido.
2. Qué proceso parece más prometedor.
3. Qué datos faltan para decidir.
4. Qué pregunta concreta reduce más incertidumbre.
5. Si ya puedo cerrar, no hagas más preguntas: di que ya puedes preparar el diagnóstico.

Framework de evaluación:
Composite = (Impacto x 0.40) + (Factibilidad x 0.30) + (Escalabilidad x 0.15) - (Sensibilidad de datos x 0.15)
Triage: PROCEED >= 3.5, REFINE 2.0-3.4, PARK < 2.0.

Devuelve siempre JSON válido con esta forma:
No copies este esquema literalmente. Rellena cada campo con información inferida de la conversación y escribe una respuesta natural adaptada al usuario.
{
  "reply": "mensaje natural al usuario",
  "stage": "contexto|exploracion|profundizacion|evaluacion|recomendacion|informe",
  "ready_for_report": false,
  "confidence": 0.0,
  "progress_label": "qué está haciendo el agente ahora",
  "current_focus": "proceso o área que está investigando",
  "open_gaps": ["dato concreto que falta"],
  "live_insights": ["insight breve que ya se puede afirmar"],
  "candidate_processes": [
    {
      "name": "proceso candidato",
      "why_it_matters": "por qué importa",
      "evidence": "qué dijo el usuario que lo sugiere",
      "confidence": 0.0
    }
  ],
  "facts": {
    "business": "",
    "customer": "",
    "channels": "",
    "main_processes": [],
    "selected_process": "",
    "example": "",
    "frequency": "",
    "impact": "",
    "tools": "",
    "data": "",
    "risk": "",
    "preference": "",
    "budget": "",
    "urgency": ""
  },
  "signals": {
    "email": 0,
    "sales": 0,
    "whatsapp": 0,
    "support": 0,
    "bookings": 0,
    "reporting": 0,
    "documentation": 0,
    "operations": 0
  }
}
"""


REPORT_INSTRUCTIONS = """
Genera un diagnóstico accionable en español para "Encuentra Tu Primer Empleado IA".

Usa la conversación y facts disponibles. Si falta algo, explícitalo como "confianza media/baja", no inventes.

Devuelve JSON válido:
No copies este esquema literalmente. Rellena cada campo con un diagnóstico específico, incluso si marcas confianza media o baja donde falten datos.
{
  "summary": "resumen ejecutivo",
  "business_snapshot": "lo que entendimos del negocio",
  "recommended_employee": "nombre del primer empleado IA",
  "recommendation_reason": "por qué este primero",
  "readiness": "listo|ordenar primero|alto potencial con revisión|no recomendable todavía",
  "opportunities": [
    {
      "name": "nombre de iniciativa",
      "current_process": "proceso actual",
      "problem": "problema detectado",
      "ai_employee": "rol recomendado",
      "what_it_would_do": ["acción 1", "acción 2"],
      "impact_score": 1,
      "feasibility_score": 1,
      "scalability_score": 1,
      "data_sensitivity_score": 1,
      "composite_score": 0.0,
      "triage": "PROCEED|REFINE|PARK",
      "tools": ["herramienta"],
      "data_needed": ["dato"],
      "risks": ["riesgo"],
      "first_step": "primer paso"
    }
  ],
  "do_not_automate_yet": ["cosa"],
  "seven_day_plan": ["día/paso 1"],
  "thirty_day_plan": ["semana/paso 1"],
  "cta": {
    "segment": "newsletter|cohort|implementation_call|resource|not_ready",
    "message": "siguiente paso recomendado"
  },
  "crm_summary": {
    "sector": "",
    "use_case": "",
    "score": 0,
    "urgency": "",
    "budget": "",
    "offer": "",
    "status": ""
  }
}
"""


def now() -> int:
    return int(time.time())


def client_ip(handler) -> str:
    forwarded = handler.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return handler.client_address[0]


def rate_limited(key: str, limit: int, window_seconds: int = 3600) -> bool:
    current = now()
    bucket = [stamp for stamp in RATE_BUCKETS.get(key, []) if current - stamp < window_seconds]
    if len(bucket) >= limit:
        RATE_BUCKETS[key] = bucket
        return True
    bucket.append(current)
    RATE_BUCKETS[key] = bucket
    return False


def valid_email(email: str) -> bool:
    if not email:
        return False
    if len(email) > 254 or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local and "." in domain and not any(char.isspace() for char in email))


def transcription_status() -> dict:
    whisper_path = shutil.which(WHISPER) if not Path(WHISPER).exists() else WHISPER
    ffmpeg_path = shutil.which(FFMPEG) if not Path(FFMPEG).exists() else FFMPEG
    return {
        "available": bool(whisper_path and ffmpeg_path),
        "whisper": whisper_path or "",
        "ffmpeg": ffmpeg_path or "",
    }


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                email TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                stage TEXT DEFAULT 'contexto',
                status TEXT DEFAULT 'new',
                facts_json TEXT DEFAULT '{}',
                signals_json TEXT DEFAULT '{}',
                outcome_json TEXT,
                transcript_json TEXT DEFAULT '[]',
                feedback_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                event TEXT NOT NULL,
                payload_json TEXT,
                created_at INTEGER NOT NULL
            )
            """
        )


def read_json(handler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length > MAX_BODY_BYTES:
        raise ValueError("Payload demasiado grande")
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def insert_event(lead_id: str | None, event_name: str, payload: dict):
    with db() as conn:
        conn.execute(
            "INSERT INTO events (lead_id, event, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (lead_id, event_name, json.dumps(payload, ensure_ascii=False), now()),
        )


def create_lead(email: str = "") -> dict:
    lead_id = str(uuid.uuid4())
    ts = now()
    transcript = []
    facts = {}
    signals = {}
    with db() as conn:
        conn.execute(
            """
            INSERT INTO leads (id, email, created_at, updated_at, facts_json, signals_json, transcript_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                email,
                ts,
                ts,
                json.dumps(facts, ensure_ascii=False),
                json.dumps(signals, ensure_ascii=False),
                json.dumps(transcript, ensure_ascii=False),
            ),
        )
    return {"lead_id": lead_id, "email": email, "facts": facts, "signals": signals, "transcript": transcript}


def get_lead(lead_id: str) -> dict:
    with db() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not row:
        raise KeyError("Lead not found")
    return {
        "id": row["id"],
        "email": row["email"] or "",
        "stage": row["stage"] or "contexto",
        "status": row["status"] or "new",
        "facts": json.loads(row["facts_json"] or "{}"),
        "signals": json.loads(row["signals_json"] or "{}"),
        "outcome": json.loads(row["outcome_json"]) if row["outcome_json"] else None,
        "transcript": json.loads(row["transcript_json"] or "[]"),
        "feedback": json.loads(row["feedback_json"]) if row["feedback_json"] else None,
    }


def update_lead(lead_id: str, *, email=None, stage=None, facts=None, signals=None, transcript=None, outcome=None, feedback=None, status=None):
    current = get_lead(lead_id)
    values = {
        "email": current["email"] if email is None else email,
        "stage": current["stage"] if stage is None else stage,
        "status": current["status"] if status is None else status,
        "facts_json": json.dumps(current["facts"] if facts is None else facts, ensure_ascii=False),
        "signals_json": json.dumps(current["signals"] if signals is None else signals, ensure_ascii=False),
        "transcript_json": json.dumps(current["transcript"] if transcript is None else transcript, ensure_ascii=False),
        "outcome_json": json.dumps(current["outcome"] if outcome is None else outcome, ensure_ascii=False) if (current["outcome"] if outcome is None else outcome) is not None else None,
        "feedback_json": json.dumps(current["feedback"] if feedback is None else feedback, ensure_ascii=False) if (current["feedback"] if feedback is None else feedback) is not None else None,
        "updated_at": now(),
        "id": lead_id,
    }
    with db() as conn:
        conn.execute(
            """
            UPDATE leads
            SET email = :email, stage = :stage, status = :status, facts_json = :facts_json,
                signals_json = :signals_json, transcript_json = :transcript_json,
                outcome_json = :outcome_json, feedback_json = :feedback_json, updated_at = :updated_at
            WHERE id = :id
            """,
            values,
        )


def extract_response_text(payload: dict) -> str:
    parts = []
    for item in payload.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        elif item.get("type") == "output_text":
            parts.append(item.get("text", ""))
    return "\n".join(parts).strip() or payload.get("output_text", "")


def extract_balanced_json(text: str) -> str:
    in_string = False
    escaped = False
    depth = 0
    start = -1
    for index, char in enumerate(text):
        if start < 0:
            if char == "{":
                start = index
                depth = 1
            continue
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError("No se encontró JSON válido en la respuesta")


def parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(extract_balanced_json(text))


def ensure_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_agent_result(result: dict, lead: dict) -> dict:
    facts = result.get("facts") if isinstance(result.get("facts"), dict) else lead.get("facts", {})
    signals = result.get("signals") if isinstance(result.get("signals"), dict) else lead.get("signals", {})
    confidence = result.get("confidence", 0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0, min(1, confidence))
    stage = result.get("stage") if result.get("stage") in stagePctBackend() else lead.get("stage", "contexto")
    reply = result.get("reply") or "Te sigo. Para recomendar bien, necesito un ejemplo concreto de cómo ocurre ahora ese proceso."
    normalized = {
        **result,
        "reply": reply,
        "stage": stage,
        "ready_for_report": bool(result.get("ready_for_report", False)),
        "confidence": confidence,
        "progress_label": result.get("progress_label") or "Entendiendo el negocio",
        "current_focus": result.get("current_focus") or facts.get("selected_process", ""),
        "open_gaps": ensure_list(result.get("open_gaps")),
        "live_insights": ensure_list(result.get("live_insights")),
        "candidate_processes": ensure_list(result.get("candidate_processes")),
        "facts": facts,
        "signals": signals,
    }
    return normalized


def stagePctBackend():
    return {"contexto", "exploracion", "profundizacion", "evaluacion", "recomendacion", "informe"}


def call_codex_cli(instructions: str, input_text: str) -> dict:
    if not CODEX_BIN or not Path(CODEX_BIN).exists():
        raise RuntimeError("Codex CLI no está disponible")
    if instructions == AGENT_INSTRUCTIONS:
        codex_instructions = """
Eres un consultor conversacional de automatización para pymes españolas y personas no técnicas.
Tu trabajo es hacer una discovery session real: entender el negocio, formular hipótesis, detectar procesos automatizables y hacer la siguiente pregunta más útil.
No eres un formulario. No uses un guion fijo. Cada pregunta debe nacer de la última respuesta del usuario y de lo que falta para poder recomendar con criterio.
Si falta concreción, pide un ejemplo real. Si el usuario ya dio información suficiente, no preguntes por preguntar: cierra y prepara diagnóstico.
Tu marco de decisión es sencillo: dónde se escapa tiempo, dinero o clientes; qué proceso se repite; qué datos existen; qué riesgo tendría automatizarlo; y cuál sería el primer empleado IA sensato.
Si el usuario responde con poco detalle o se molesta, demuestra que has entendido, ofrece opciones probables y avanza sin repetir la misma demanda.
Optimiza para una entrevista de 7-10 minutos: profunda, pero comprimida.

Responde solo con JSON. Tipos obligatorios:
- reply: string con la siguiente intervención concreta al usuario.
- stage: uno de contexto, exploracion, profundizacion, evaluacion, recomendacion, informe.
- ready_for_report: boolean.
- confidence: número entre 0 y 1.
- progress_label: string breve sobre qué estás analizando.
- current_focus: string con el proceso/área que estás investigando.
- open_gaps: array de datos concretos que faltan.
- live_insights: array de insights breves ya detectados.
- candidate_processes: array de objetos con name, why_it_matters, evidence, confidence.
- facts: objeto con claves opcionales business, customer, channels, main_processes, selected_process, example, frequency, impact, tools, data, risk, preference, budget, urgency.
- signals: objeto con puntuaciones numéricas para email, sales, whatsapp, support, bookings, reporting, documentation, operations.
"""
    elif instructions == REPORT_INSTRUCTIONS:
        codex_instructions = """
Eres un estratega de automatización. Genera un informe accionable para una persona no técnica.
Usa solo la conversación disponible. Si falta algo, dilo como confianza media o baja, sin inventar.

Responde solo con JSON. Debe incluir:
- summary, business_snapshot, recommended_employee, recommendation_reason, readiness.
- opportunities: array de 1-3 oportunidades con name, current_process, problem, ai_employee, what_it_would_do, impact_score, feasibility_score, scalability_score, data_sensitivity_score, composite_score, triage, tools, data_needed, risks, first_step.
- do_not_automate_yet, seven_day_plan, thirty_day_plan.
- cta con segment y message.
- crm_summary con sector, use_case, score, urgency, budget, offer, status.
"""
    else:
        codex_instructions = instructions
    prompt = (
        f"{codex_instructions}\n\n"
        "IMPORTANTE: responde exclusivamente con un único objeto JSON válido. "
        "No escribas Markdown, explicación, comandos ni texto adicional.\n\n"
        "Actúa sobre el caso real del INPUT. No repitas valores de ejemplo, nombres de campos ni placeholders del esquema. "
        "El campo reply debe contener la siguiente intervención concreta que dirías al usuario.\n\n"
        f"INPUT:\n{input_text}"
    )
    with tempfile.TemporaryDirectory(prefix="primer-empleado-codex-") as tmp:
        output_file = Path(tmp) / "last-message.json"
        subprocess.run(
            [
                CODEX_BIN,
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--output-last-message",
                str(output_file),
                prompt,
            ],
            cwd=str(ROOT),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
        )
        if not output_file.exists():
            raise RuntimeError("Codex CLI no generó respuesta final")
        return parse_json_text(output_file.read_text(encoding="utf-8"))


def call_ai(instructions: str, input_text: str) -> dict:
    if AI_PROVIDER == "fallback":
        raise RuntimeError("AI_PROVIDER=fallback")
    acquired = AI_SEMAPHORE.acquire(timeout=AI_QUEUE_WAIT_SECONDS)
    if not acquired:
        raise AiBusyError("El agente está atendiendo otro diagnóstico. Espera unos segundos y vuelve a intentarlo.")
    try:
        if AI_PROVIDER == "codex":
            return call_codex_cli(instructions, input_text)
        if AI_PROVIDER == "openai":
            return call_openai(instructions, input_text)
        if os.environ.get("OPENAI_API_KEY"):
            return call_openai(instructions, input_text)
        return call_codex_cli(instructions, input_text)
    finally:
        AI_SEMAPHORE.release()


def should_fallback() -> bool:
    return AI_PROVIDER == "fallback" or ALLOW_AI_FALLBACK


def call_openai(instructions: str, input_text: str) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurada")
    body = {
        "model": DEFAULT_MODEL,
        "instructions": instructions,
        "input": input_text,
        "max_output_tokens": 2500,
    }
    req = request.Request(
        OPENAI_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail[:500]}")
    return parse_json_text(extract_response_text(payload))


def fallback_agent(lead: dict, user_text: str) -> dict:
    text = " ".join([m.get("content", "") for m in lead["transcript"] if m.get("role") == "user"]).lower()
    combined = f"{text} {user_text}".lower()
    def score_terms(terms):
        return sum(combined.count(term) for term in terms)

    scores = {
        "email": score_terms(["email", "correo", "outlook", "gmail", "bandeja"]),
        "sales": score_terms(["lead", "leads", "venta", "ventas", "crm", "propuesta", "comprador", "compradores", "comercial"]),
        "whatsapp": score_terms(["whatsapp", "wasap", "whatsapps"]),
        "support": score_terms(["soporte", "incidencia", "cliente", "duda", "ticket", "paciente", "pacientes"]),
        "bookings": score_terms(["reserva", "reservas", "reservar", "cita", "citas", "agenda", "calendario", "doctoralia"]),
        "reporting": score_terms(["reporte", "reportes", "informe", "metricas", "dashboard"]),
        "documentation": score_terms(["documentar", "documentacion", "procedimiento", "manual"]),
        "operations": score_terms(["operacion", "proceso", "tarea", "repetitivo", "manual", "seguimiento"]),
    }
    if scores["whatsapp"] and scores["bookings"]:
        scores["bookings"] += 2
    if scores["sales"] and scores["whatsapp"]:
        scores["sales"] += 1
    signal = max(scores, key=scores.get)
    if scores[signal] == 0:
        signal = "operations"
    labels = {
        "email": "bandeja de entrada y clasificación de mensajes",
        "sales": "captación y seguimiento comercial",
        "whatsapp": "recepción y respuesta por WhatsApp",
        "support": "atención y soporte a clientes",
        "bookings": "reservas y gestión de citas",
        "reporting": "reporting y seguimiento de métricas",
        "documentation": "documentación interna",
        "operations": "operaciones repetitivas",
    }
    focus_label = labels.get(signal, signal)

    turns = len([m for m in lead["transcript"] if m.get("role") == "user"])
    gaps = []
    if not any(x in combined for x in ["cada día", "diario", "semana", "mes", "10", "15", "horas", "veces"]):
        gaps.append("frecuencia e impacto")
    if not any(x in combined for x in ["ejemplo", "caso", "ayer", "cliente", "entra", "recibo"]):
        gaps.append("ejemplo real")
    if not any(x in combined for x in ["uso", "herramienta", "gmail", "outlook", "hubspot", "notion", "excel", "sheets", "whatsapp"]):
        gaps.append("herramientas y datos")
    if not any(x in combined for x in ["riesgo", "peligro", "revisión", "aprobar", "invent"]):
        gaps.append("riesgos y revisión humana")
    if "ejemplo real" in gaps:
        reply = f"Veo una posible oportunidad en {focus_label}. Para no inventar, cuéntame un caso real reciente: qué entró, qué hiciste tú, qué decidiste y qué debería haber salido."
    elif "frecuencia e impacto" in gaps:
        reply = f"Esto ya suena automatizable en {focus_label}. Para priorizarlo: ¿con qué frecuencia ocurre, cuánto tiempo te consume y qué pierdes si sigue igual tres meses?"
    elif "herramientas y datos" in gaps:
        reply = "Ahora quiero saber si se puede construir: ¿qué herramientas usas hoy y dónde están los ejemplos o datos que tendría que mirar el empleado IA?"
    elif "riesgos y revisión humana" in gaps:
        reply = "Antes de recomendarlo, pongamos límites: ¿qué sería peligroso que la IA hiciera mal y qué tendría que quedar siempre en revisión humana?"
    else:
        reply = "Ya tengo suficiente para preparar un diagnóstico preliminar con oportunidades y riesgos claros."
    ready = turns >= 5
    if not gaps and turns >= 3:
        ready = True
    facts = lead["facts"]
    facts.setdefault("business", lead["transcript"][0]["content"] if lead["transcript"] else user_text)
    facts["selected_process"] = focus_label
    signals = lead["signals"]
    for key, score in scores.items():
        signals[key] = max(signals.get(key, 0), score)
    return {
        "reply": reply,
        "stage": "recomendacion" if ready else "profundizacion",
        "ready_for_report": ready,
        "confidence": 0.72 if ready else min(0.65, 0.25 + turns * 0.12),
        "progress_label": "Priorizando oportunidades" if ready else f"Investigando {focus_label}",
        "current_focus": focus_label,
        "open_gaps": gaps,
        "live_insights": [
            f"Hay señales de trabajo repetitivo en {focus_label}.",
            "Conviene mantener revisión humana en la primera versión.",
        ],
        "candidate_processes": [
            {
                "name": focus_label,
                "why_it_matters": "Aparece como área con fricción o pérdida de valor en la conversación.",
                "evidence": user_text[:180],
                "confidence": 0.62 if not ready else 0.78,
            }
        ],
        "facts": facts,
        "signals": signals,
        "fallback": True,
    }


def fallback_report(lead: dict) -> dict:
    signals = lead["signals"]
    best = max(signals, key=signals.get) if signals else "operations"
    employee = {
        "email": "Jefe IA de bandeja de entrada",
        "sales": "SDR IA de seguimiento comercial",
        "whatsapp": "Recepcionista IA de WhatsApp",
        "support": "Asistente IA de atención al cliente",
        "bookings": "Recepcionista IA de reservas y citas",
        "reporting": "Analista IA de reporting operativo",
        "documentation": "Documentalista IA de procesos internos",
        "operations": "Asistente IA de operaciones",
    }.get(best, "Asistente IA de operaciones")
    return {
        "summary": "Diagnóstico preliminar generado en modo local. Hay una oportunidad clara, pero conviene revisar con el agente LLM cuando OPENAI_API_KEY esté configurada.",
        "business_snapshot": lead["facts"].get("business", ""),
        "recommended_employee": employee,
        "recommendation_reason": "Es el área con más señales en la conversación y puede empezar con revisión humana.",
        "readiness": "alto potencial con revisión",
        "opportunities": [
            {
                "name": employee,
                "current_process": lead["facts"].get("selected_process", best),
                "problem": "Proceso repetitivo con valor potencial no capturado.",
                "ai_employee": employee,
                "what_it_would_do": ["clasificar entradas", "preparar borradores", "crear tareas de seguimiento", "resumir oportunidades"],
                "impact_score": 4,
                "feasibility_score": 3,
                "scalability_score": 3,
                "data_sensitivity_score": 3,
                "composite_score": 2.8,
                "triage": "REFINE",
                "tools": [],
                "data_needed": ["20 ejemplos reales"],
                "risks": ["respuesta inventada", "tono incorrecto"],
                "first_step": "Recolectar 20 casos reales y definir salidas esperadas.",
            }
        ],
        "do_not_automate_yet": ["envío automático sin revisión"],
        "seven_day_plan": ["reunir ejemplos", "etiquetar tipos", "definir salidas", "probar borradores"],
        "thirty_day_plan": ["prototipo", "revisión humana", "integración CRM", "medición"],
        "cta": {"segment": "cohort", "message": "Buen caso para hacerlo acompañado."},
        "crm_summary": {"sector": "", "use_case": best, "score": 65, "urgency": "", "budget": "", "offer": "cohort", "status": "new"},
    }


def humanize(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "; ".join(humanize(item) for item in value if humanize(item))
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            text = humanize(item)
            if text:
                parts.append(f"{key}: {text}")
        return "; ".join(parts)
    return str(value)


def score_1_to_5(value, default=3):
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = float(default)
    if score > 5:
        score = score / 2
    return max(1, min(5, round(score, 1)))


def score_0_to_100(value, fallback_score):
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = float(fallback_score)
    if score <= 5:
        score = score * 20
    elif score <= 10:
        score = score * 10
    return max(0, min(100, round(score, 1)))


def normalize_triage(value, impact, feasibility, composite):
    text = humanize(value).lower()
    if any(term in text for term in ["park", "no recomendable", "no automatizar"]):
        return "No recomendable todavía"
    if any(term in text for term in ["ordenar", "refine", "refinar", "proceso"]):
        return "Requiere ordenar proceso"
    if any(term in text for term in ["quick", "rápid", "rapido", "ahora", "proceed"]):
        return "Quick win"
    if impact >= 4 and composite >= 3.3:
        return "Alto impacto"
    if feasibility >= 4 and composite >= 3.2:
        return "Quick win"
    if composite < 2:
        return "No recomendable todavía"
    return "Requiere ordenar proceso"


def human_list(value) -> list[str]:
    return [text for text in (humanize(item) for item in ensure_list(value)) if text]


def normalize_report(report: dict, lead: dict) -> dict:
    if not isinstance(report, dict):
        report = {}
    opportunities = report.get("opportunities")
    if not isinstance(opportunities, list) or not opportunities:
        opportunities = fallback_report(lead)["opportunities"]

    normalized_opportunities = []
    for item in opportunities[:3]:
        opp = item if isinstance(item, dict) else {"name": humanize(item)}
        impact = score_1_to_5(opp.get("impact_score"), 3)
        feasibility = score_1_to_5(opp.get("feasibility_score"), 3)
        scalability = score_1_to_5(opp.get("scalability_score"), 3)
        sensitivity = score_1_to_5(opp.get("data_sensitivity_score"), 3)
        composite = opp.get("composite_score")
        try:
            composite = float(composite)
            if composite > 5:
                composite = composite / 2
        except (TypeError, ValueError):
            composite = round((impact * 0.4) + (feasibility * 0.3) + (scalability * 0.15) - (sensitivity * 0.15), 2)
        normalized_opportunities.append(
            {
                "name": humanize(opp.get("name")) or "Oportunidad de automatización",
                "current_process": humanize(opp.get("current_process")) or lead["facts"].get("selected_process", ""),
                "problem": humanize(opp.get("problem")) or "Proceso repetitivo con impacto en el negocio.",
                "ai_employee": humanize(opp.get("ai_employee")) or humanize(report.get("recommended_employee")) or "Asistente IA",
                "what_it_would_do": human_list(opp.get("what_it_would_do")),
                "impact_score": impact,
                "feasibility_score": feasibility,
                "scalability_score": scalability,
                "data_sensitivity_score": sensitivity,
                "composite_score": round(composite, 2),
                "triage": normalize_triage(opp.get("triage"), impact, feasibility, composite),
                "tools": human_list(opp.get("tools")),
                "data_needed": human_list(opp.get("data_needed")),
                "risks": human_list(opp.get("risks")),
                "first_step": humanize(opp.get("first_step")) or "Reunir ejemplos reales y definir la salida esperada.",
            }
        )

    crm_summary = report.get("crm_summary") if isinstance(report.get("crm_summary"), dict) else {}
    cta = report.get("cta") if isinstance(report.get("cta"), dict) else {}
    normalized = {
        "summary": humanize(report.get("summary")) or "Diagnóstico generado a partir de la conversación.",
        "business_snapshot": humanize(report.get("business_snapshot")) or humanize(lead.get("facts", {})),
        "recommended_employee": humanize(report.get("recommended_employee")) or normalized_opportunities[0]["ai_employee"],
        "recommendation_reason": humanize(report.get("recommendation_reason")) or "Es la oportunidad con mejor equilibrio entre impacto, factibilidad y riesgo.",
        "readiness": humanize(report.get("readiness")) or "alto potencial con revisión",
        "opportunities": normalized_opportunities,
        "do_not_automate_yet": human_list(report.get("do_not_automate_yet")) or ["Envío automático sin revisión humana."],
        "seven_day_plan": human_list(report.get("seven_day_plan")) or ["Reunir ejemplos reales.", "Definir criterios.", "Probar una primera versión con revisión humana."],
        "thirty_day_plan": human_list(report.get("thirty_day_plan")) or ["Validar el MVP.", "Medir impacto.", "Añadir integraciones solo si aporta valor."],
        "cta": {
            "segment": humanize(cta.get("segment")) or "resource",
            "message": humanize(cta.get("message")) or "El siguiente paso es probar una primera versión pequeña con revisión humana.",
        },
        "crm_summary": {
            "sector": humanize(crm_summary.get("sector")),
            "use_case": humanize(crm_summary.get("use_case")) or normalized_opportunities[0]["name"],
            "score": score_0_to_100(crm_summary.get("score"), normalized_opportunities[0]["composite_score"] * 20),
            "urgency": humanize(crm_summary.get("urgency")),
            "budget": humanize(crm_summary.get("budget")),
            "offer": humanize(crm_summary.get("offer")),
            "status": humanize(crm_summary.get("status")) or "report_generated",
        },
    }
    if report.get("reply"):
        normalized["reply"] = humanize(report.get("reply"))
    return normalized


def forbidden_static_path(path: str) -> bool:
    clean = parse.unquote(path).strip("/")
    if not clean:
        return False
    parts = [part for part in clean.split("/") if part]
    first = parts[0] if parts else ""
    name = parts[-1] if parts else ""
    suffix = Path(name).suffix.lower()
    if first in {"backups", "deploy", ".git", "__pycache__"}:
        return True
    if name in {".env", ".env.example", "crm.sqlite3", "crm_leads.jsonl"}:
        return True
    return suffix in {".py", ".pyc", ".sqlite", ".sqlite3", ".db", ".jsonl", ".log", ".toml"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        route = parse.urlparse(self.path)
        if route.path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", "/Agente_Real_CRM.html")
            self.end_headers()
            return
        if route.path == "/healthz":
            self._json({
                "ok": True,
                "provider": AI_PROVIDER,
                "transcription": transcription_status()["available"],
                "ai_concurrency": MAX_AI_CONCURRENCY,
            })
            return
        if route.path == "/api/capabilities":
            self._json({"transcription": transcription_status()})
            return
        if route.path in ("/CRM_Dashboard.html", "/api/leads", "/api/lead", "/api/metrics", "/api/export.csv") and not self._require_admin():
            return
        if route.path == "/api/leads":
            self._handle_list_leads()
            return
        if route.path == "/api/lead":
            self._handle_get_lead(route.query)
            return
        if route.path == "/api/metrics":
            self._handle_metrics()
            return
        if route.path == "/api/export.csv":
            self._handle_export_csv()
            return
        if forbidden_static_path(route.path):
            self.send_error(404, "Not found")
            return
        super().do_GET()

    def do_POST(self):
        if rate_limited(f"post:{client_ip(self)}", MAX_PUBLIC_EVENTS_PER_HOUR):
            self._json({"error": "Demasiadas peticiones. Inténtalo más tarde."}, 429)
            return
        if int(self.headers.get("Content-Length", "0")) > MAX_BODY_BYTES:
            self._json({"error": "Payload demasiado grande"}, 413)
            return
        admin_routes = {"/api/lead/update", "/api/lead/delete", "/crm"}
        if self.path in admin_routes and not self._require_admin():
            return
        routes = {
            "/api/session": self._handle_session,
            "/api/email": self._handle_email,
            "/api/chat": self._handle_chat,
            "/api/report": self._handle_report,
            "/api/feedback": self._handle_feedback,
            "/api/lead/update": self._handle_update_lead_admin,
            "/api/lead/delete": self._handle_delete_lead_admin,
            "/crm": self._handle_crm,
            "/transcribe": self._handle_transcribe,
        }
        handler = routes.get(self.path)
        if not handler:
            self.send_error(404, "Not found")
            return
        handler()

    def _require_admin(self) -> bool:
        if not ADMIN_PASSWORD:
            return True
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            self._auth_required()
            return False
        try:
            decoded = base64.b64decode(auth.removeprefix("Basic ").strip()).decode("utf-8")
        except Exception:
            self._auth_required()
            return False
        user, _, password = decoded.partition(":")
        if user == ADMIN_USER and password == ADMIN_PASSWORD:
            return True
        self._auth_required()
        return False

    def _auth_required(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Primer Empleado IA CRM"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Autenticación requerida".encode("utf-8"))

    def _handle_session(self):
        payload = read_json(self)
        email = (payload.get("email", "") or "").strip().lower()
        if email and not valid_email(email):
            self._json({"error": "Introduce un email válido."}, 400)
            return
        lead = create_lead(email)
        insert_event(lead["lead_id"], "session_created", payload)
        self._json(lead)

    def _handle_email(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        email = (payload.get("email", "") or "").strip().lower()
        if not lead_id:
            self._json({"error": "lead_id is required"}, 400)
            return
        if not valid_email(email):
            self._json({"error": "Introduce un email válido para recibir el informe."}, 400)
            return
        get_lead(lead_id)
        update_lead(lead_id, email=email)
        insert_event(lead_id, "email_captured", {"email": email})
        self._json({"ok": True, "email": email})

    def _handle_chat(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        user_text = (payload.get("message") or "").strip()
        if not lead_id or not user_text:
            self._json({"error": "lead_id and message are required"}, 400)
            return
        if len(user_text) > MAX_MESSAGE_CHARS:
            self._json({"error": "Mensaje demasiado largo. Resume la respuesta y vuelve a intentarlo."}, 400)
            return
        lead = get_lead(lead_id)
        user_turns = len([m for m in lead["transcript"] if m.get("role") == "user"])
        if user_turns >= MAX_USER_TURNS:
            self._json({"error": "Ya hay suficiente información. Genera el informe para cerrar el diagnóstico."}, 400)
            return
        transcript = lead["transcript"] + [{"role": "user", "content": user_text, "at": now()}]
        lead["transcript"] = transcript
        prompt = json.dumps({"lead": lead, "latest_user_message": user_text}, ensure_ascii=False)
        try:
            result = call_ai(AGENT_INSTRUCTIONS, prompt)
        except AiBusyError as exc:
            insert_event(lead_id, "ai_busy", {"stage": "chat", "error": str(exc)})
            self._json({"error": str(exc)}, 429)
            return
        except Exception as exc:
            if not should_fallback():
                insert_event(lead_id, "ai_error", {"stage": "chat", "error": str(exc)})
                self._json({"error": "Ahora mismo no puedo generar una respuesta fiable. Inténtalo de nuevo en un momento."}, 502)
                return
            result = fallback_agent(lead, user_text)
            result["api_error"] = str(exc)
        result = normalize_agent_result(result, lead)
        transcript.append({"role": "assistant", "content": result.get("reply", ""), "at": now()})
        update_lead(
            lead_id,
            email=payload.get("email", lead["email"]),
            stage=result.get("stage", lead["stage"]),
            facts=result.get("facts", lead["facts"]),
            signals=result.get("signals", lead["signals"]),
            transcript=transcript,
        )
        insert_event(lead_id, "chat_turn", {"user": user_text, "assistant": result})
        self._json({"lead_id": lead_id, **result})

    def _handle_report(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        if not lead_id:
            self._json({"error": "lead_id is required"}, 400)
            return
        lead = get_lead(lead_id)
        prompt = json.dumps({"lead": lead}, ensure_ascii=False)
        try:
            report = call_ai(REPORT_INSTRUCTIONS, prompt)
        except AiBusyError as exc:
            insert_event(lead_id, "ai_busy", {"stage": "report", "error": str(exc)})
            self._json({"error": str(exc)}, 429)
            return
        except Exception as exc:
            if not should_fallback():
                insert_event(lead_id, "ai_error", {"stage": "report", "error": str(exc)})
                self._json({"error": "Ahora mismo no puedo generar el informe con garantías. Inténtalo de nuevo en un momento."}, 502)
                return
            report = fallback_report(lead)
            report["api_error"] = str(exc)
        report = normalize_report(report, lead)
        update_lead(lead_id, outcome=report, stage="informe", status="report_generated")
        insert_event(lead_id, "report_generated", report)
        append_jsonl({"event": "report_generated", "lead_id": lead_id, "email": lead["email"], "outcome": report, "transcript": lead["transcript"]})
        self._json({"lead_id": lead_id, "report": report})

    def _handle_feedback(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        feedback = payload.get("feedback", {})
        if not lead_id:
            self._json({"error": "lead_id is required"}, 400)
            return
        update_lead(lead_id, feedback=feedback, status="feedback_saved")
        insert_event(lead_id, "feedback_saved", feedback)
        self._json({"ok": True})

    def _handle_update_lead_admin(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        if not lead_id:
            self._json({"error": "lead_id is required"}, 400)
            return
        try:
            lead = get_lead(lead_id)
        except KeyError:
            self._json({"error": "Lead not found"}, 404)
            return

        allowed_status = {
            "new",
            "send_resource",
            "invite_cohort",
            "invite_call",
            "not_fit",
            "client",
            "report_generated",
            "feedback_saved",
        }
        status = humanize(payload.get("status")).strip()
        offer = humanize(payload.get("offer")).strip()
        notes = humanize(payload.get("notes")).strip()
        if status and status not in allowed_status:
            self._json({"error": "Estado no válido"}, 400)
            return

        outcome = lead["outcome"] if isinstance(lead["outcome"], dict) else {}
        crm_summary = outcome.get("crm_summary") if isinstance(outcome.get("crm_summary"), dict) else {}
        if offer:
            crm_summary["offer"] = offer
        if status:
            crm_summary["status"] = status
        if notes:
            crm_summary["internal_notes"] = notes
        if crm_summary:
            outcome["crm_summary"] = crm_summary

        update_lead(
            lead_id,
            status=status or None,
            outcome=outcome if outcome else lead["outcome"],
        )
        insert_event(
            lead_id,
            "lead_admin_updated",
            {"status": status or lead["status"], "offer": offer or crm_summary.get("offer", ""), "notes": notes},
        )
        self._json({"ok": True, "lead": get_lead(lead_id)})

    def _handle_delete_lead_admin(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        confirm = humanize(payload.get("confirm")).strip().lower()
        if not lead_id:
            self._json({"error": "lead_id is required"}, 400)
            return
        if confirm != "delete":
            self._json({"error": "Confirmación requerida"}, 400)
            return
        try:
            lead = get_lead(lead_id)
        except KeyError:
            self._json({"error": "Lead not found"}, 404)
            return
        snapshot = {
            "email": lead["email"],
            "stage": lead["stage"],
            "status": lead["status"],
            "turns": len([m for m in lead["transcript"] if m.get("role") == "user"]),
        }
        with db() as conn:
            conn.execute("DELETE FROM events WHERE lead_id = ?", (lead_id,))
            conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        insert_event(None, "lead_deleted", {"lead_id": lead_id, **snapshot})
        self._json({"ok": True, "deleted": lead_id})

    def _handle_list_leads(self):
        with db() as conn:
            rows = conn.execute(
                """
                SELECT id, email, created_at, updated_at, stage, status, facts_json, signals_json,
                       outcome_json, feedback_json, transcript_json
                FROM leads
                ORDER BY updated_at DESC
                LIMIT 100
                """
            ).fetchall()
        leads = []
        for row in rows:
            outcome = json.loads(row["outcome_json"]) if row["outcome_json"] else None
            facts = json.loads(row["facts_json"] or "{}")
            signals = json.loads(row["signals_json"] or "{}")
            feedback = json.loads(row["feedback_json"]) if row["feedback_json"] else None
            transcript = json.loads(row["transcript_json"] or "[]")
            leads.append(
                {
                    "id": row["id"],
                    "email": row["email"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "stage": row["stage"],
                    "status": row["status"],
                    "sector": outcome.get("crm_summary", {}).get("sector") if outcome else "",
                    "use_case": outcome.get("crm_summary", {}).get("use_case") if outcome else facts.get("selected_process", ""),
                    "score": score_0_to_100(outcome.get("crm_summary", {}).get("score"), 0) if outcome else 0,
                    "offer": outcome.get("crm_summary", {}).get("offer") if outcome else "",
                    "signals": signals,
                    "has_feedback": bool(feedback),
                    "turns": len([m for m in transcript if m.get("role") == "user"]),
                    "recommended_employee": outcome.get("recommended_employee") if outcome else None,
                    "crm_summary": outcome.get("crm_summary") if outcome else None,
                }
            )
        self._json({"leads": leads})

    def _handle_get_lead(self, query: str):
        params = parse.parse_qs(query)
        lead_id = (params.get("id") or [""])[0]
        if not lead_id:
            self._json({"error": "id is required"}, 400)
            return
        try:
            lead = get_lead(lead_id)
        except KeyError:
            self._json({"error": "Lead not found"}, 404)
            return
        self._json({"lead": lead})

    def _handle_metrics(self):
        with db() as conn:
            lead_rows = conn.execute(
                """
                SELECT email, stage, status, outcome_json, feedback_json, transcript_json, updated_at
                FROM leads
                """
            ).fetchall()
            event_rows = conn.execute(
                """
                SELECT event, COUNT(*) AS count
                FROM events
                GROUP BY event
                """
            ).fetchall()

        total = len(lead_rows)
        with_email = 0
        with_report = 0
        with_feedback = 0
        started_chat = 0
        total_turns = 0
        offer_counts: dict[str, int] = {}
        use_case_counts: dict[str, int] = {}
        recent_reports = []
        for row in lead_rows:
            transcript = json.loads(row["transcript_json"] or "[]")
            turns = len([m for m in transcript if m.get("role") == "user"])
            total_turns += turns
            if turns:
                started_chat += 1
            if row["email"]:
                with_email += 1
            if row["feedback_json"]:
                with_feedback += 1
            outcome = json.loads(row["outcome_json"]) if row["outcome_json"] else None
            if outcome:
                with_report += 1
                crm = outcome.get("crm_summary", {})
                offer = humanize(crm.get("offer")) or "sin oferta"
                use_case = humanize(crm.get("use_case")) or humanize(outcome.get("recommended_employee")) or "sin caso"
                offer_counts[offer] = offer_counts.get(offer, 0) + 1
                use_case_counts[use_case] = use_case_counts.get(use_case, 0) + 1
                recent_reports.append(
                    {
                        "updated_at": row["updated_at"],
                        "email": row["email"] or "sin email",
                        "recommended_employee": humanize(outcome.get("recommended_employee")),
                        "use_case": use_case,
                        "score": score_0_to_100(crm.get("score"), 0),
                    }
                )

        def pct(part):
            return round((part / total) * 100, 1) if total else 0

        def top_items(items):
            return [
                {"name": name, "count": count}
                for name, count in sorted(items.items(), key=lambda pair: pair[1], reverse=True)[:5]
            ]

        metrics = {
            "total_leads": total,
            "started_chat": started_chat,
            "email_captured": with_email,
            "reports_generated": with_report,
            "feedback_received": with_feedback,
            "chat_start_rate": pct(started_chat),
            "email_capture_rate": pct(with_email),
            "report_rate": pct(with_report),
            "feedback_rate": pct(with_feedback),
            "avg_user_turns": round(total_turns / total, 1) if total else 0,
            "events": {row["event"]: row["count"] for row in event_rows},
            "top_offers": top_items(offer_counts),
            "top_use_cases": top_items(use_case_counts),
            "recent_reports": sorted(recent_reports, key=lambda item: item["updated_at"], reverse=True)[:5],
        }
        self._json({"metrics": metrics})

    def _handle_export_csv(self):
        with db() as conn:
            rows = conn.execute(
                """
                SELECT id, email, created_at, updated_at, stage, status, facts_json, outcome_json,
                       feedback_json, transcript_json
                FROM leads
                ORDER BY updated_at DESC
                """
            ).fetchall()

        output = io.StringIO()
        fieldnames = [
            "id",
            "email",
            "created_at",
            "updated_at",
            "stage",
            "status",
            "sector",
            "use_case",
            "score",
            "urgency",
            "budget",
            "offer",
            "recommended_employee",
            "turns",
            "has_feedback",
            "summary",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            outcome = json.loads(row["outcome_json"]) if row["outcome_json"] else {}
            facts = json.loads(row["facts_json"] or "{}")
            feedback = json.loads(row["feedback_json"]) if row["feedback_json"] else None
            transcript = json.loads(row["transcript_json"] or "[]")
            crm = outcome.get("crm_summary", {})
            writer.writerow(
                {
                    "id": row["id"],
                    "email": row["email"] or "",
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "stage": row["stage"],
                    "status": row["status"],
                    "sector": humanize(crm.get("sector")),
                    "use_case": humanize(crm.get("use_case")) or humanize(facts.get("selected_process")),
                    "score": score_0_to_100(crm.get("score"), 0) if outcome else 0,
                    "urgency": humanize(crm.get("urgency")),
                    "budget": humanize(crm.get("budget")),
                    "offer": humanize(crm.get("offer")),
                    "recommended_employee": humanize(outcome.get("recommended_employee")),
                    "turns": len([m for m in transcript if m.get("role") == "user"]),
                    "has_feedback": "yes" if feedback else "no",
                    "summary": humanize(outcome.get("summary")),
                }
            )
        encoded = output.getvalue().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="primer-empleado-ia-leads.csv"')
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _handle_crm(self):
        payload = read_json(self)
        append_jsonl(payload)
        insert_event(payload.get("lead_id"), payload.get("event", "legacy_crm"), payload)
        self._json({"ok": True, "path": str(JSONL_FILE), "db": str(DB_FILE)})

    def _handle_transcribe(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            self._json({"error": "No audio received"}, 400)
            return
        body = self.rfile.read(length)
        try:
            text = transcribe_audio(body)
            self._json({"text": text})
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def _json(self, payload, status=200):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def append_jsonl(payload: dict):
    with JSONL_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def transcribe_audio(body: bytes) -> str:
    status = transcription_status()
    if not status["whisper"]:
        raise RuntimeError("Whisper no está instalado o WHISPER_BIN no apunta a un binario válido")
    if not status["ffmpeg"]:
        raise RuntimeError("ffmpeg no está instalado o FFMPEG_BIN no apunta a un binario válido")

    with tempfile.TemporaryDirectory(prefix="primer-empleado-ia-") as tmp:
        tmpdir = Path(tmp)
        webm = tmpdir / "audio.webm"
        wav = tmpdir / "audio.wav"
        webm.write_bytes(body)

        subprocess.run(
            [status["ffmpeg"], "-y", "-i", str(webm), "-ar", "16000", "-ac", "1", str(wav)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                status["whisper"],
                str(wav),
                "--model",
                "tiny",
                "--language",
                "Spanish",
                "--fp16",
                "False",
                "--output_format",
                "txt",
                "--output_dir",
                str(tmpdir),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )

        txt = wav.with_suffix(".txt")
        if not txt.exists():
            raise RuntimeError("Whisper no generó transcripción")
        return txt.read_text(encoding="utf-8").strip()


def main():
    init_db()
    os.chdir(ROOT)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving MVP on http://{HOST}:{PORT}/Agente_Real_CRM.html")
    print(f"CRM dashboard on http://{HOST}:{PORT}/CRM_Dashboard.html")
    print("SQLite CRM:", DB_FILE)
    print("AI provider:", AI_PROVIDER)
    print("AI fallback:", "enabled" if ALLOW_AI_FALLBACK else "disabled")
    print("CRM auth:", "enabled" if ADMIN_PASSWORD else "disabled")
    print("Local transcription endpoint enabled at /transcribe")
    server.serve_forever()


if __name__ == "__main__":
    main()
