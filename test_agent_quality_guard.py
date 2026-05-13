#!/usr/bin/env python3
from app_server import enforce_readiness_window, normalize_agent_result, repair_repetitive_reply


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
        "facts": {"selected_process": "cualificación de leads por WhatsApp"},
        "signals": {},
    }

    closed = enforce_readiness_window(normalize_agent_result(raw_result, lead), lead)
    assert_true(closed["ready_for_report"], "No cerró una discovery con confianza alta y suficiente evidencia")
    assert_true("suficiente" in closed["reply"].lower(), "El cierre no explica que ya hay base para informe")


if __name__ == "__main__":
    test_repeated_example_request_is_repaired()
    test_frustration_is_acknowledged()
    test_high_confidence_four_turns_can_close()
    print("agent_quality_guard ok")
