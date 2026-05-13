#!/usr/bin/env python3
import argparse
import json
import time


def skip(message: str) -> int:
    print(json.dumps({"ok": True, "skipped": True, "reason": message}, ensure_ascii=False, indent=2))
    return 0


def assert_true(condition, message: str):
    if not condition:
        raise AssertionError(message)


def sample_report() -> dict:
    return {
        "summary": "Tu negocio pierde oportunidades porque el email mezcla lectores, posibles clientes y mensajes internos sin una prioridad clara.",
        "business_snapshot": "Newsletter y servicios de IA para profesionales no técnicos, con oportunidades entrantes por email.",
        "recommended_employee": "Empleado IA de triaje y seguimiento de email",
        "recommendation_reason": "Es frecuente, tiene impacto comercial y puede empezar supervisado sin responder de forma autónoma.",
        "readiness": "listo para piloto supervisado",
        "evidence_summary": [
            "El usuario recibe correos diarios con posibles oportunidades.",
            "El riesgo principal es que la IA invente respuestas.",
            "Outlook puede ser el primer punto de entrada.",
        ],
        "opportunities": [
            {
                "name": "Triage de email entrante",
                "current_process": "Los correos entran en Outlook y muchos quedan sin respuesta.",
                "problem": "Se pierden conversaciones con valor comercial o aprendizaje de mercado.",
                "ai_employee": "Asistente IA de clasificación y borradores supervisados",
                "what_it_would_do": ["Clasificar emails", "Detectar intención", "Preparar borradores", "Proponer siguiente acción"],
                "impact_score": 5,
                "feasibility_score": 4,
                "scalability_score": 4,
                "data_sensitivity_score": 2,
                "composite_score": 4.4,
                "triage": "Quick win",
                "data_needed": ["emails de ejemplo", "categorías", "criterios de respuesta"],
                "tools": ["Outlook", "n8n", "base de conocimiento"],
                "risks": ["respuestas inventadas", "tono incorrecto"],
                "first_step": "Exportar 30 emails reales y definir 5 categorías de respuesta.",
            },
            {
                "name": "Base de conocimiento de respuestas",
                "current_process": "Las respuestas dependen de memoria y criterio del fundador.",
                "problem": "Cada email exige decidir desde cero.",
                "ai_employee": "Documentador IA de criterios comerciales",
                "what_it_would_do": ["Extraer patrones", "Crear plantillas", "Mantener criterios"],
                "impact_score": 4,
                "feasibility_score": 3,
                "scalability_score": 4,
                "data_sensitivity_score": 2,
                "composite_score": 3.8,
                "triage": "Requiere ordenar proceso",
                "data_needed": ["respuestas buenas", "ofertas", "criterios"],
                "tools": ["Notion", "Google Docs"],
                "risks": ["documentar demasiado pronto"],
                "first_step": "Recopilar 10 respuestas que sí te habría gustado enviar.",
            },
        ],
        "do_not_automate_yet": ["Responder autónomamente emails sensibles", "Cerrar ventas sin revisión humana"],
        "seven_day_plan": ["Reunir ejemplos", "Definir categorías", "Probar borradores supervisados"],
        "thirty_day_plan": ["Medir ahorro", "Añadir seguimiento", "Conectar CRM externo"],
        "cta": {"segment": "cohort", "message": "Te encaja hacerlo acompañado: primero piloto supervisado y luego automatización gradual."},
        "crm_summary": {"sector": "newsletter", "use_case": "email", "score": 88, "offer": "cohort"},
        "sales_intelligence": {"objections": ["miedo a respuestas inventadas"], "content_ideas": ["Cómo automatizar email sin perder control"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba de navegador del cierre: email final, informe y feedback")
    parser.add_argument("--base", default="http://localhost:8787")
    args = parser.parse_args()

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return skip(f"Playwright no está instalado: {exc}")

    result = {"ok": False, "base": args.base, "checks": []}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as exc:
            return skip(f"Chromium de Playwright no está instalado: {exc}")
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 920})

            def chat_handler(route):
                time.sleep(0.6)
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "reply": "Con esto ya tengo suficiente para preparar una recomendación útil y aterrizada.",
                            "ready_for_report": True,
                            "current_focus": "email entrante y oportunidades sin respuesta",
                            "progress_label": "Evidencia suficiente para informe",
                            "facts": {"business_type": "newsletter", "selected_process": "email"},
                            "signals": ["10-15 emails diarios", "riesgo de respuestas inventadas", "Outlook como herramienta base"],
                            "candidate_processes": [{"name": "triage de email", "confidence": 5}],
                            "open_gaps": [],
                            "stage": "recomendacion",
                        }
                    ),
                )

            def email_handler(route):
                route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "email": "tester@example.com"}))

            def report_handler(route):
                time.sleep(0.6)
                route.fulfill(status=200, content_type="application/json", body=json.dumps({"lead_id": "ui-test", "report": sample_report()}))

            def feedback_handler(route):
                route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True}))

            page.route("**/api/chat", chat_handler)
            page.route("**/api/email", email_handler)
            page.route("**/api/report", report_handler)
            page.route("**/api/feedback", feedback_handler)

            page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=report", wait_until="networkidle")
            page.locator("section.starter button.start-primary").click()
            page.wait_for_selector("textarea#input:not([disabled])", timeout=8000)
            page.fill("#input", "Tengo una newsletter y se me quedan correos importantes sin responder.")
            page.click("#send")
            page.get_by_text("Ya tengo suficiente para prepararte un diagnóstico útil").wait_for(timeout=10000)
            page.locator("#report").wait_for(state="visible", timeout=5000)
            result["checks"].append("agent_closes_discovery")

            page.locator("#report").click()
            page.get_by_text("Ya tengo suficiente para preparar tu informe.").wait_for(timeout=5000)
            page.locator("#finalEmail").fill("tester@example.com")
            page.locator("#finalConsent").check()
            page.locator(".email-gate button").click()
            page.get_by_text("Generando diagnóstico").wait_for(timeout=3000)
            page.get_by_text("Tu primer empleado IA debería ser: Empleado IA de triaje y seguimiento de email").wait_for(timeout=10000)
            page.get_by_text("Matriz de priorización").wait_for(timeout=5000)
            page.get_by_text("Ayúdanos a mejorar este diagnóstico").wait_for(timeout=5000)
            result["checks"].append("email_gate_report_rendered")

            page.locator("input[name='feedbackRating'][value='5']").check()
            page.locator("#feedbackLiked").fill("Me aclaró qué automatizar primero.")
            page.locator("#feedbackMissing").fill("Coste aproximado.")
            page.locator("#feedbackImprove").fill("Añadir ejemplos por sector.")
            page.get_by_role("button", name="Guardar feedback").click()
            page.get_by_text("Feedback guardado. Gracias.").wait_for(timeout=5000)
            result["checks"].append("feedback_saved")

            page.evaluate("localStorage.clear()")
            retry_page = browser.new_page(viewport={"width": 1280, "height": 920})

            def report_needs_more_handler(route):
                route.fulfill(
                    status=409,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "error": "Aún no tengo suficiente evidencia para generar un diagnóstico útil. Continúa la conversación un poco más.",
                            "missing": ["un proceso concreto a evaluar", "evidencia sobre frecuencia, impacto, herramientas o riesgos"],
                        }
                    ),
                )

            retry_page.route("**/api/chat", chat_handler)
            retry_page.route("**/api/email", email_handler)
            retry_page.route("**/api/report", report_needs_more_handler)
            retry_page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=report_retry", wait_until="networkidle")
            retry_page.locator("section.starter button.start-primary").click()
            retry_page.wait_for_selector("textarea#input:not([disabled])", timeout=8000)
            retry_page.fill("#input", "Tengo correos importantes sin responder.")
            retry_page.click("#send")
            retry_page.get_by_text("Ya tengo suficiente para prepararte un diagnóstico útil").wait_for(timeout=10000)
            retry_page.locator("#report").wait_for(state="visible", timeout=5000)
            retry_page.locator("#report").click()
            retry_page.locator("#finalEmail").fill("tester@example.com")
            retry_page.locator("#finalConsent").check()
            retry_page.locator(".email-gate button").click()
            retry_page.get_by_text("Todavía no quiero darte un informe flojo.").wait_for(timeout=10000)
            retry_page.wait_for_selector("textarea#input:not([disabled])", timeout=5000)
            assert_true(not retry_page.locator("#report").is_visible(), "El botón de informe debería ocultarse si falta discovery")
            result["checks"].append("report_quality_gate_returns_to_chat")
            retry_page.close()

            result["ok"] = True
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        except (AssertionError, PlaywrightTimeoutError) as exc:
            result["error"] = str(exc)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
