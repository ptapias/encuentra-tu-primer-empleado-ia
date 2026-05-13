#!/usr/bin/env python3
from app_server import AGENT_INSTRUCTIONS, attach_discovery_state, enforce_readiness_window, normalize_agent_result, normalize_report, repair_repetitive_reply, report_readiness


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_repeated_example_request_is_repaired():
    lead = {
        "stage": "profundizacion",
        "facts": {"selected_process": "email y priorización"},
        "signals": {},
        "transcript": [
            {
                "role": "assistant",
                "content": "Te sigo, pero necesito un poco más de carne para no inventarme el diagnóstico. Dame un ejemplo concreto con qué entra, qué haces tú y qué resultado debería salir.",
            }
        ],
    }
    user_text = (
        "Pues mira, por ejemplo fue el caso real de un profesor que se presentó diciendo que "
        "quería implementar IA, no tenía tiempo, le interesaba mucho lo que publico y se quedó "
        "sin respuesta porque recibo muchos correos así al día."
    )
    raw_result = {
        "reply": "Te sigo, pero necesito un poco más de carne. Dame un ejemplo concreto con qué entra, qué haces tú y qué resultado debería salir.",
        "stage": "profundizacion",
        "ready_for_report": False,
        "confidence": 0.45,
        "progress_label": "Investigando email",
        "current_focus": "email y priorización",
        "open_gaps": ["ejemplo real", "frecuencia e impacto"],
        "live_insights": ["Hay una oportunidad en email."],
        "candidate_processes": [],
        "facts": {"selected_process": "email y priorización"},
        "signals": {},
    }

    normalized = normalize_agent_result(raw_result, lead)
    repaired = repair_repetitive_reply(normalized, lead, user_text)

    reply = repaired["reply"].lower()
    assert_true("ejemplo concreto" not in reply, "El agente siguió pidiendo el mismo ejemplo")
    assert_true(
        "priorizar" in reply or "herramienta" in reply or "límites" in reply or "limites" in reply,
        "La reparación no avanzó al siguiente dato útil",
    )
    assert_true("ejemplo real" not in repaired["open_gaps"], "No eliminó el gap de ejemplo ya respondido")


def test_frustration_is_acknowledged():
    lead = {
        "stage": "profundizacion",
        "facts": {"selected_process": "leads por WhatsApp"},
        "signals": {},
        "transcript": [
            {"role": "assistant", "content": "Cuéntame un caso real reciente."},
            {"role": "assistant", "content": "Dame un ejemplo concreto para no inventar."},
        ],
    }
    raw_result = {
        "reply": "Dame un ejemplo concreto para no inventar.",
        "stage": "profundizacion",
        "ready_for_report": False,
        "confidence": 0.5,
        "current_focus": "leads por WhatsApp",
        "open_gaps": ["frecuencia e impacto"],
        "facts": {"selected_process": "leads por WhatsApp"},
        "signals": {},
    }

    repaired = repair_repetitive_reply(normalize_agent_result(raw_result, lead), lead, "Te lo estoy diciendo")
    assert_true(repaired["reply"].startswith("Tienes razón"), "No reconoció la frustración del usuario")


def test_unknown_output_is_rescued_with_options():
    lead = {
        "stage": "profundizacion",
        "facts": {"selected_process": "email y priorización"},
        "signals": {},
        "transcript": [
            {"role": "assistant", "content": "Dame un ejemplo concreto con qué entra, qué haces tú y qué resultado debería salir."},
        ],
    }
    raw_result = {
        "reply": "Entiendo. ¿Qué resultado debería salir exactamente cuando entra ese email?",
        "stage": "profundizacion",
        "ready_for_report": False,
        "confidence": 0.5,
        "current_focus": "email y priorización",
        "open_gaps": ["resultado esperado"],
        "facts": {"selected_process": "email y priorización"},
        "signals": {},
    }

    repaired = repair_repetitive_reply(
        normalize_agent_result(raw_result, lead),
        lead,
        "Entra: email. Hago: nada. Debería salir: no sé.",
    )
    reply = repaired["reply"].lower()
    assert_true("no pasa nada" in reply, "No normalizó que el usuario no sepa definir el output")
    assert_true("clasificar" in reply and "resumir" in reply and "revisión humana" in reply, "No propuso salidas posibles")
    assert_true("qué resultado debería salir" not in reply, "Volvió a pedir el output en vez de ayudar a definirlo")


def test_high_confidence_four_turns_can_close():
    lead = {
        "stage": "evaluacion",
        "facts": {"selected_process": "cualificación de leads por WhatsApp"},
        "signals": {},
        "transcript": [
            {"role": "user", "content": "Somos una inmobiliaria pequeña."},
            {"role": "user", "content": "Nos entran 20 o 30 leads al día."},
            {"role": "user", "content": "Usamos WhatsApp, Gmail y una hoja."},
            {"role": "user", "content": "No debería cerrar nada sola, solo preparar seguimiento."},
        ],
    }
    raw_result = {
        "reply": "Antes necesito saber más criterios de clasificación.",
        "stage": "evaluacion",
        "ready_for_report": False,
        "confidence": 0.78,
        "current_focus": "cualificación de leads por WhatsApp",
        "open_gaps": ["criterios concretos", "cadencia de seguimiento"],
        "live_insights": ["Hay volumen y pérdida comercial."],
        "candidate_processes": [{"name": "cualificación de leads", "confidence": 0.8}],
        "facts": {
            "selected_process": "cualificación de leads por WhatsApp",
            "frequency": "20 o 30 leads al día",
            "impact": "contestación lenta y pérdida comercial",
            "tools": "WhatsApp, Gmail y hoja de cálculo",
        },
        "signals": {},
    }

    closed = enforce_readiness_window(normalize_agent_result(raw_result, lead), lead)
    assert_true(closed["ready_for_report"], "No cerró una discovery con confianza alta y suficiente evidencia")
    assert_true("suficiente" in closed["reply"].lower(), "El cierre no explica que ya hay base para informe")


def test_compressed_discovery_can_close_with_solid_evidence():
    lead = {
        "stage": "evaluacion",
        "facts": {},
        "signals": {},
        "transcript": [
            {"role": "user", "content": "Soy consultor B2B."},
            {"role": "user", "content": "Me entran correos y mensajes de LinkedIn."},
            {"role": "user", "content": "Pierdo 3 horas semanales revisando y pensando respuestas."},
            {"role": "user", "content": "Uso Gmail, LinkedIn y Notion y quiero registrar siguientes pasos."},
        ],
    }
    raw_result = {
        "reply": "Antes necesito los criterios exactos.",
        "stage": "profundizacion",
        "ready_for_report": False,
        "confidence": 0.72,
        "current_focus": "detección, respuesta y registro de leads entrantes",
        "candidate_processes": [{"name": "seguimiento comercial de leads", "confidence": 0.8}],
        "facts": {
            "selected_process": "seguimiento comercial de leads",
            "frequency": "cada semana",
            "impact": "3 horas semanales y oportunidades sin seguimiento",
            "tools": "Gmail, LinkedIn y Notion",
            "preference": "detectar oportunidades, preparar respuesta y registrar siguientes pasos",
        },
        "signals": {},
    }
    closed = enforce_readiness_window(normalize_agent_result(raw_result, lead), lead)
    assert_true(closed["ready_for_report"], "Una discovery comprimida con evidencia sólida debería cerrar")


def test_report_always_exposes_evidence_summary():
    lead = {
        "facts": {
            "selected_process": "clasificación de emails",
            "frequency": "10-15 emails al día",
            "impact": "oportunidades comerciales sin responder",
            "tools": "Outlook",
            "risk": "que la IA invente respuestas",
        },
        "signals": {"email": 4},
    }
    raw_report = {
        "summary": "Hay una oportunidad clara en email.",
        "business_snapshot": "Newsletter con lectores que escriben por correo.",
        "recommended_employee": "Asistente IA de bandeja de entrada",
        "opportunities": [
            {
                "name": "Priorización de emails",
                "impact_score": 4,
                "feasibility_score": 4,
                "scalability_score": 3,
                "data_sensitivity_score": 3,
            }
        ],
    }

    report = normalize_report(raw_report, lead)
    assert_true(report["evidence_summary"], "El informe normalizado debería incluir señales de evidencia")
    assert_true(
        any("10-15 emails" in item for item in report["evidence_summary"]),
        "La evidencia debería aprovechar datos concretos del diagnóstico",
    )


def test_report_readiness_blocks_empty_discovery():
    lead = {
        "stage": "contexto",
        "facts": {},
        "transcript": [{"role": "user", "content": "Hola"}],
    }
    ready, missing = report_readiness(lead)
    assert_true(not ready, "Un diagnóstico sin discovery no debería poder generar informe")
    assert_true(missing, "La puerta de informe debería explicar qué falta")


def test_report_readiness_allows_evidenced_discovery():
    result = normalize_agent_result(
        {
            "reply": "Con esto ya puedo cerrar.",
            "stage": "recomendacion",
            "ready_for_report": True,
            "confidence": 0.78,
            "current_focus": "triage de email",
            "candidate_processes": [{"name": "triage de email", "confidence": 0.8}],
            "facts": {
                "selected_process": "triage de email",
                "frequency": "10-15 emails al día",
                "impact": "oportunidades comerciales sin responder",
                "tools": "Outlook",
            },
        },
        {"stage": "evaluacion", "facts": {}, "signals": {}, "transcript": []},
    )
    lead = {
        "stage": result["stage"],
        "facts": attach_discovery_state(result, result["facts"]),
        "transcript": [
            {"role": "user", "content": "Tengo una newsletter."},
            {"role": "user", "content": "Me llegan emails todos los días."},
            {"role": "user", "content": "Uso Outlook."},
            {"role": "user", "content": "Pierdo oportunidades comerciales."},
        ],
    }
    ready, missing = report_readiness(lead)
    assert_true(ready, f"Una discovery con evidencia debería permitir informe: {missing}")


def test_agent_prompt_prioritizes_adaptive_discovery():
    prompt = AGENT_INSTRUCTIONS.lower()
    assert_true("no eres un formulario" in prompt, "El prompt debe rechazar comportamiento de formulario")
    assert_true("dónde se escapa tiempo, dinero o clientes" in prompt, "El prompt debe conservar el marco comercial")
    assert_true("outlook" in prompt and "10-15 emails al día" in prompt, "El prompt debe tratar respuestas cortas como señal útil")
    assert_true("no pidas \"más detalle\" de forma genérica" in prompt, "El prompt debe evitar repreguntas genéricas")
    assert_true("clasificación" in prompt and "registro en crm" in prompt, "El prompt debe rescatar respuestas tipo 'no sé' con opciones")


if __name__ == "__main__":
    test_repeated_example_request_is_repaired()
    test_frustration_is_acknowledged()
    test_unknown_output_is_rescued_with_options()
    test_high_confidence_four_turns_can_close()
    test_compressed_discovery_can_close_with_solid_evidence()
    test_report_always_exposes_evidence_summary()
    test_report_readiness_blocks_empty_discovery()
    test_report_readiness_allows_evidenced_discovery()
    test_agent_prompt_prioritizes_adaptive_discovery()
    print("agent_quality_guard ok")
