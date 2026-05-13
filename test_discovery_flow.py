#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


DEFAULT_BASE = "http://localhost:8787"


CASES = [
    {
        "name": "clinica_dental",
        "email": "clinica-test@example.com",
        "messages": [
            "Tengo una clínica dental en Valencia. Nos llegan pacientes por llamadas, WhatsApp y formulario web, pero muchas consultas se quedan sin responder rápido.",
            "Pasa todos los días. Entrarán unas 15 consultas, y quizá 4 o 5 se responden tarde. Perdemos reservas de tratamientos caros.",
            "Usamos WhatsApp Business, Gmail y Doctoralia. Me gustaría que la IA clasificara urgencia, tratamiento y probabilidad de reservar.",
            "El riesgo es que prometa precios o diagnósticos. Siempre debería dejar la respuesta final en revisión humana.",
            "Para empezar preferiría algo acompañado y sencillo este mes, sin presupuesto cerrado todavía.",
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
            "Me interesa implementarlo con ayuda externa si vemos que recupera visitas o clientes perdidos.",
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
            "Lo haría acompañado. No tengo presupuesto cerrado, pero sí quiero validar un primer flujo en las próximas semanas.",
        ],
    },
]


def post(base, path, payload, timeout=240, client_ip=""):
    headers = {"Content-Type": "application/json"}
    if client_ip:
        headers["X-Forwarded-For"] = client_ip
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get(base, path, timeout=30):
    with urllib.request.urlopen(base + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def run_case(base, case, client_ip=""):
    session = post(base, "/api/session", {}, client_ip=client_ip)
    lead_id = session["lead_id"]
    last = None
    start = time.time()
    for message in case["messages"]:
        last = post(base, "/api/chat", {"lead_id": lead_id, "message": message}, client_ip=client_ip)
    assert_true(last, "No hubo respuesta del agente")
    assert_true(last.get("reply"), "Falta reply")
    assert_true(last.get("current_focus"), "Falta current_focus")
    assert_true(isinstance(last.get("open_gaps"), list), "open_gaps no es lista")
    assert_true(isinstance(last.get("live_insights"), list), "live_insights no es lista")
    assert_true(isinstance(last.get("candidate_processes"), list), "candidate_processes no es lista")
    assert_true(last.get("confidence", 0) > 0.25, "confidence demasiado baja")
    assert_true(last.get("ready_for_report"), "El agente no cerró la discovery tras 5 turnos con evidencia suficiente")

    post(base, "/api/email", {"lead_id": lead_id, "email": case["email"], "consent": True, "privacy_version": "test"}, client_ip=client_ip)
    report = post(base, "/api/report", {"lead_id": lead_id}, client_ip=client_ip)["report"]
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
    parser = argparse.ArgumentParser(description="Prueba discovery real con varios negocios")
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--client-ip", default=os.environ.get("TEST_CLIENT_IP", ""))
    args = parser.parse_args()
    base = args.base.rstrip("/")

    try:
        health = get(base, "/healthz")
    except urllib.error.URLError as exc:
        print(f"No puedo conectar con {base}. Arranca app_server.py antes. Detalle: {exc}", file=sys.stderr)
        return 1

    results = []
    for index, case in enumerate(CASES, start=1):
        client_ip = args.client_ip
        if args.client_ip and args.client_ip.count(".") == 3:
            parts = args.client_ip.split(".")
            if parts[-1].isdigit():
                parts[-1] = str(min(254, max(1, int(parts[-1]) + index - 1)))
                client_ip = ".".join(parts)
        results.append(run_case(base, case, client_ip=client_ip))
    print(json.dumps({"health": health, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
