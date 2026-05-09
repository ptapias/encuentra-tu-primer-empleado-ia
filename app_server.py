#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request, error, parse
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parent
WHISPER = "/opt/homebrew/bin/whisper"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
DB_FILE = ROOT / "crm.sqlite3"
JSONL_FILE = ROOT / "crm_leads.jsonl"
OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")


AGENT_INSTRUCTIONS = """
Eres el agente real de diagnóstico de "Encuentra Tu Primer Empleado IA".

Tu misión es conversar en español con una persona no técnica para descubrir qué procesos de su negocio son automatizables con IA. No eres un formulario. Eres un consultor práctico: escuchas, resumes, detectas señales, haces preguntas adaptadas y avanzas cuando ya tienes suficiente información.

Reglas:
- Haz una sola pregunta por turno, pero puede ser una pregunta densa.
- No repitas la misma pregunta si el usuario ya dio señal útil.
- Si el usuario dice "no sé", ofrece opciones plausibles.
- Si el usuario se frustra, resume lo entendido y avanza.
- Investiga: negocio, cliente, canales, procesos repetitivos, ejemplo real, frecuencia, impacto, herramientas/datos, riesgo, nivel técnico, preferencia de implementación.
- No recomiendes automatizar decisiones delicadas sin revisión humana.
- Prioriza oportunidades con intención comercial: leads, ventas, email, WhatsApp, soporte, reservas, reporting y documentación.
- Cierra cuando haya confianza suficiente, normalmente en 7-10 minutos, pero puedes seguir si el caso lo exige.

Framework de evaluación:
Composite = (Impacto x 0.40) + (Factibilidad x 0.30) + (Escalabilidad x 0.15) - (Sensibilidad de datos x 0.15)
Triage: PROCEED >= 3.5, REFINE 2.0-3.4, PARK < 2.0.

Devuelve siempre JSON válido con esta forma:
{
  "reply": "mensaje natural al usuario",
  "stage": "contexto|exploracion|profundizacion|evaluacion|recomendacion|informe",
  "ready_for_report": false,
  "confidence": 0.0,
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
Genera un informe potente y accionable en español para "Encuentra Tu Primer Empleado IA".

Usa la conversación y facts disponibles. Si falta algo, explícitalo como "confianza media/baja", no inventes.

Devuelve JSON válido:
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


def parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        text = text[start : end + 1]
    return json.loads(text)


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
    signal = "operations"
    if any(x in combined for x in ["email", "correo", "outlook", "gmail"]):
        signal = "email"
    if any(x in combined for x in ["lead", "venta", "crm", "propuesta"]):
        signal = "sales"
    if any(x in combined for x in ["whatsapp", "wasap"]):
        signal = "whatsapp"
    if any(x in combined for x in ["soporte", "incidencia", "cliente"]):
        signal = "support"

    turns = len([m for m in lead["transcript"] if m.get("role") == "user"])
    questions = [
        "Cuéntame el flujo actual con un ejemplo real: qué entra, qué haces tú, qué decides y qué debería salir.",
        "¿Con qué frecuencia ocurre, cuánto tiempo consume y qué pierdes si sigue igual 3 meses?",
        "¿Qué herramientas usas y dónde viven los datos o ejemplos reales?",
        "¿Qué sería peligroso que una IA hiciera mal y qué debería quedar siempre en revisión humana?",
        "¿Prefieres aprender a montarlo, hacerlo acompañado o que alguien lo implemente? ¿Hay urgencia o presupuesto aproximado?",
    ]
    ready = turns >= 5
    facts = lead["facts"]
    facts.setdefault("business", lead["transcript"][0]["content"] if lead["transcript"] else user_text)
    facts["selected_process"] = signal
    signals = lead["signals"]
    signals[signal] = signals.get(signal, 0) + 1
    return {
        "reply": "Tengo suficiente para generar un diagnóstico preliminar." if ready else questions[min(turns, len(questions) - 1)],
        "stage": "recomendacion" if ready else "profundizacion",
        "ready_for_report": ready,
        "confidence": 0.55 if ready else 0.3,
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


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        route = parse.urlparse(self.path)
        if route.path == "/api/leads":
            self._handle_list_leads()
            return
        if route.path == "/api/lead":
            self._handle_get_lead(route.query)
            return
        super().do_GET()

    def do_POST(self):
        routes = {
            "/api/session": self._handle_session,
            "/api/chat": self._handle_chat,
            "/api/report": self._handle_report,
            "/api/feedback": self._handle_feedback,
            "/crm": self._handle_crm,
            "/transcribe": self._handle_transcribe,
        }
        handler = routes.get(self.path)
        if not handler:
            self.send_error(404, "Not found")
            return
        handler()

    def _handle_session(self):
        payload = read_json(self)
        lead = create_lead(payload.get("email", ""))
        insert_event(lead["lead_id"], "session_created", payload)
        self._json(lead)

    def _handle_chat(self):
        payload = read_json(self)
        lead_id = payload.get("lead_id")
        user_text = (payload.get("message") or "").strip()
        if not lead_id or not user_text:
            self._json({"error": "lead_id and message are required"}, 400)
            return
        lead = get_lead(lead_id)
        transcript = lead["transcript"] + [{"role": "user", "content": user_text, "at": now()}]
        lead["transcript"] = transcript
        prompt = json.dumps({"lead": lead, "latest_user_message": user_text}, ensure_ascii=False)
        try:
            result = call_openai(AGENT_INSTRUCTIONS, prompt)
        except Exception as exc:
            result = fallback_agent(lead, user_text)
            result["api_error"] = str(exc)
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
            report = call_openai(REPORT_INSTRUCTIONS, prompt)
        except Exception as exc:
            report = fallback_report(lead)
            report["api_error"] = str(exc)
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
                    "score": outcome.get("crm_summary", {}).get("score") if outcome else 0,
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
    if not Path(WHISPER).exists():
        raise RuntimeError("Whisper local no está instalado en /opt/homebrew/bin/whisper")
    if not Path(FFMPEG).exists():
        raise RuntimeError("ffmpeg local no está instalado en /opt/homebrew/bin/ffmpeg")

    with tempfile.TemporaryDirectory(prefix="primer-empleado-ia-") as tmp:
        tmpdir = Path(tmp)
        webm = tmpdir / "audio.webm"
        wav = tmpdir / "audio.wav"
        webm.write_bytes(body)

        subprocess.run(
            [FFMPEG, "-y", "-i", str(webm), "-ar", "16000", "-ac", "1", str(wav)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                WHISPER,
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
    server = ThreadingHTTPServer(("localhost", 8787), Handler)
    print("Serving MVP on http://localhost:8787/Agente_Real_CRM.html")
    print("Legacy prototype available at http://localhost:8787/Prototipo_Conversacional.html")
    print("SQLite CRM:", DB_FILE)
    print("Local transcription endpoint enabled at /transcribe")
    server.serve_forever()


if __name__ == "__main__":
    main()
