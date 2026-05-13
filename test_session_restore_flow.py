#!/usr/bin/env python3
import argparse
import json
import os
import time


def skip(message: str) -> int:
    print(json.dumps({"ok": True, "skipped": True, "reason": message}, ensure_ascii=False, indent=2))
    return 0


TEST_IP = f"198.51.{os.getpid() % 250}.{int(time.time() * 1000) % 250 + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba de navegador para recuperación de sesión tras recarga")
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
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                extra_http_headers={"X-Forwarded-For": TEST_IP},
            )
            page = context.new_page()

            def capabilities_handler(route):
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"transcription": {"available": True, "whisper": "test", "ffmpeg": "test"}}),
                )

            def chat_handler(route):
                time.sleep(0.4)
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "reply": "Veo un proceso claro en seguimiento comercial. Antes de cerrar, quiero entender la frecuencia y el riesgo.",
                            "ready_for_report": False,
                            "current_focus": "seguimiento comercial",
                            "progress_label": "Profundizando seguimiento comercial",
                            "facts": {"business_type": "consultoría", "selected_process": "seguimiento comercial"},
                            "signals": ["leads entrantes", "seguimiento manual", "riesgo comercial bajo si hay revisión"],
                            "candidate_processes": [{"name": "seguimiento comercial", "confidence": 4}],
                            "open_gaps": ["frecuencia", "criterios de prioridad"],
                            "stage": "profundizacion",
                        }
                    ),
                )

            page.route("**/api/capabilities", capabilities_handler)
            page.route("**/api/chat", chat_handler)
            page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=restore", wait_until="networkidle")
            page.locator("section.starter button.start-primary").click()
            page.wait_for_selector("textarea#input:not([disabled])", timeout=8000)
            page.fill("#input", "Soy consultor B2B y pierdo seguimiento de leads que entran por email y LinkedIn.")
            page.click("#send")
            page.get_by_text("Profundizando seguimiento comercial").wait_for(timeout=8000)
            page.reload(wait_until="networkidle")
            page.get_by_text("He recuperado tu diagnóstico en este navegador.").wait_for(timeout=5000)
            page.get_by_text("Soy consultor B2B").wait_for(timeout=5000)
            page.locator("#focusText").get_by_text("seguimiento comercial").wait_for(timeout=5000)
            page.wait_for_selector("textarea#input:not([disabled])", timeout=5000)
            result["checks"].append("mid_discovery_restore")

            page.evaluate(
                """
                localStorage.setItem('primerEmpleadoIaSession', JSON.stringify({
                  leadId: 'restore-ready',
                  capturedEmail: '',
                  stage: 'recomendacion',
                  status: 'Ya puedo preparar tu diagnóstico.',
                  readyForReport: true,
                  reportGenerated: false,
                  transcript: [
                    {role: 'user', content: 'Tengo una inmobiliaria y llegan leads por WhatsApp.'},
                    {role: 'assistant', content: 'Ya tengo suficiente para prepararte un diagnóstico útil.'}
                  ],
                  lastDiscovery: {
                    current_focus: 'leads inmobiliarios',
                    confidence: 0.82,
                    signals: ['20 leads diarios', 'WhatsApp', 'seguimiento manual'],
                    open_gaps: [],
                    ready_for_report: true,
                    progress_label: 'Listo para informe'
                  }
                }));
                """
            )
            page.reload(wait_until="networkidle")
            page.get_by_text("Diagnóstico recuperado. Ya puedes ver el informe.").wait_for(timeout=5000)
            page.locator("#report").wait_for(state="visible", timeout=5000)
            assert page.locator("#input").is_disabled()
            result["checks"].append("ready_for_report_restore")

            stale_page = context.new_page()

            def missing_chat_handler(route):
                route.fulfill(
                    status=404,
                    content_type="application/json",
                    body=json.dumps({"error": "No encuentro este diagnóstico. Empieza uno nuevo para continuar."}),
                )

            stale_page.route("**/api/capabilities", capabilities_handler)
            stale_page.route("**/api/chat", missing_chat_handler)
            stale_page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=stale_restore", wait_until="networkidle")
            stale_page.evaluate(
                """
                localStorage.setItem('primerEmpleadoIaSession', JSON.stringify({
                  leadId: 'stale-lead',
                  capturedEmail: '',
                  stage: 'profundizacion',
                  status: 'Diagnóstico recuperado.',
                  readyForReport: false,
                  reportGenerated: false,
                  transcript: [
                    {role: 'user', content: 'Tengo una agencia y quiero automatizar seguimiento.'},
                    {role: 'assistant', content: 'Estoy entendiendo el proceso de seguimiento.'}
                  ],
                  lastDiscovery: {
                    current_focus: 'seguimiento comercial',
                    confidence: 0.48,
                    open_gaps: ['frecuencia', 'impacto'],
                    ready_for_report: false,
                    progress_label: 'Profundizando seguimiento'
                  }
                }));
                """
            )
            stale_page.reload(wait_until="networkidle")
            stale_page.wait_for_selector("textarea#input:not([disabled])", timeout=5000)
            stale_page.fill("#input", "Ocurre todos los días.")
            stale_page.click("#send")
            stale_page.get_by_role("heading", name="Este diagnóstico ya no está disponible.").wait_for(timeout=5000)
            stale_page.get_by_role("button", name="Empezar diagnóstico nuevo").wait_for(timeout=5000)
            assert stale_page.locator("#input").is_disabled()
            result["checks"].append("stale_session_recovers")
            stale_page.close()

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
