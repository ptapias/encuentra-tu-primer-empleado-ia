#!/usr/bin/env python3
import json
import sys
import time
import urllib.error
import urllib.request


BASE = "http://localhost:8787"


CASES = [
    {
        "name": "clinica_dental",
        "email": "clinica-test@example.com",
        "messages": [
            "Tengo una clínica dental en Valencia. Nos llegan pacientes por llamadas, WhatsApp y formulario web, pero muchas consultas se quedan sin responder rápido.",
            "Pasa todos los días. Entrarán unas 15 consultas, y quizá 4 o 5 se responden tarde. Perdemos reservas de tratamientos caros.",
            "Usamos WhatsApp Business, Gmail y Doctoralia. Me gustaría que la IA clasificara urgencia, tratamiento y probabilidad de reservar.",
            "El riesgo es que prometa precios o diagnósticos. Siempre debería dejar la respuesta final en revisión humana.",
        ],
    },
    {
        "name": "inmobiliaria",
        "email": "inmobiliaria-test@example.com",
        "messages": [
            "Somos una inmobiliaria pequeña en Málaga. Recibimos leads de Idealista, llamadas y WhatsApp.",
            "El problema es que contestamos lento y no sabemos priorizar compradores reales frente a curiosos.",
            "Cada día entran 20 o 30 contactos. Usamos WhatsApp, Gmail y una hoja de cálculo.",
            "La IA no debería cerrar nada sola, pero sí clasificar, preparar respuesta y crear seguimiento.",
        ],
    },
    {
        "name": "consultor_b2b",
        "email": "consultor-test@example.com",
        "messages": [
            "Soy consultor B2B y vendo proyectos de transformación con IA a empresas medianas.",
            "Me llegan correos y mensajes de LinkedIn. Muchos son interesantes, pero se quedan sin seguimiento.",
            "Cada semana pierdo unas 3 horas revisando mensajes y pensando qué responder.",
            "Uso Gmail, LinkedIn y Notion. Quiero detectar oportunidades, preparar respuesta y registrar siguientes pasos.",
        ],
    },
]


def post(path, payload, timeout=240):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def run_case(case):
    session = post("/api/session", {})
    lead_id = session["lead_id"]
    last = None
    start = time.time()
    for message in case["messages"]:
        last = post("/api/chat", {"lead_id": lead_id, "message": message})
    assert_true(last, "No hubo respuesta del agente")
    assert_true(last.get("reply"), "Falta reply")
    assert_true(last.get("current_focus"), "Falta current_focus")
    assert_true(isinstance(last.get("open_gaps"), list), "open_gaps no es lista")
    assert_true(isinstance(last.get("live_insights"), list), "live_insights no es lista")
    assert_true(isinstance(last.get("candidate_processes"), list), "candidate_processes no es lista")
    assert_true(last.get("confidence", 0) > 0.25, "confidence demasiado baja")
    assert_true(last.get("ready_for_report"), "El agente no cerró la discovery tras 4 turnos con evidencia suficiente")

    post("/api/email", {"lead_id": lead_id, "email": case["email"], "consent": True, "privacy_version": "test"})
    report = post("/api/report", {"lead_id": lead_id})["report"]
    assert_true(report.get("recommended_employee"), "Falta recommended_employee")
    assert_true(report.get("opportunities"), "Faltan opportunities")
    assert_true(report.get("evidence_summary"), "Faltan señales de evidencia en el informe")
    assert_true(report.get("seven_day_plan"), "Falta seven_day_plan")

    return {
        "case": case["name"],
        "seconds": round(time.time() - start, 1),
        "lead_id": lead_id,
        "ready_for_report": last.get("ready_for_report"),
        "confidence": last.get("confidence"),
        "focus": last.get("current_focus"),
        "gaps": last.get("open_gaps"),
        "insights": last.get("live_insights"),
        "recommended_employee": report.get("recommended_employee"),
        "opportunities": len(report.get("opportunities", [])),
        "fallback": bool(last.get("fallback")),
    }


def main():
    try:
        health = get("/healthz")
    except urllib.error.URLError as exc:
        print(f"No puedo conectar con {BASE}. Arranca app_server.py antes. Detalle: {exc}", file=sys.stderr)
        return 1

    results = []
    for case in CASES:
        results.append(run_case(case))
    print(json.dumps({"health": health, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
