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

            RESTORE_LEAD_ID = "test-restore-lead-001"
            RESTORE_TRANSCRIPT = [
                {"role": "user", "content": "Soy consultor B2B y pierdo seguimiento de leads que entran por email y LinkedIn."},
                {"role": "assistant", "content": "Veo un proceso claro en seguimiento comercial. Antes de cerrar, quiero entender la frecuencia y el riesgo."},
            ]

            def lead_handler(route):
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "lead_id": RESTORE_LEAD_ID,
                        "transcript": RESTORE_TRANSCRIPT,
                        "facts": {
                            "focus": "seguimiento comercial",
                            "signals": ["leads entrantes", "seguimiento manual"],
                            "gaps": ["frecuencia", "criterios de prioridad"],
                        },
                    }),
                )

            page.route("**/api/capabilities", capabilities_handler)
            page.route("**/api/chat", chat_handler)
            page.route("**/api/lead**", lead_handler)
            page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=restore", wait_until="networkidle")
            # Inject stored lead_id to simulate a previous session
            page.evaluate(f"localStorage.setItem('primer_empleado_lead_id', '{RESTORE_LEAD_ID}')")
            page.reload(wait_until="networkidle")
            page.get_by_text("Bienvenido de vuelta").wait_for(timeout=5000)
            page.get_by_role("button", name="Continuar").wait_for(timeout=5000)
            result["checks"].append("mid_discovery_restore")

            # Verify "Empezar de cero" clears session and reloads to fresh starter
            page.evaluate(f"localStorage.setItem('primer_empleado_lead_id', '{RESTORE_LEAD_ID}')")
            page.reload(wait_until="networkidle")
            page.get_by_text("Bienvenido de vuelta").wait_for(timeout=5000)
            page.get_by_role("button", name="Empezar de cero").click()
            # After reload triggered by "Empezar de cero", welcome-back should not appear
            page.wait_for_load_state("networkidle")
            assert page.locator("#starter").count() > 0
            result["checks"].append("ready_for_report_restore")

            stale_page = context.new_page()

            def missing_lead_handler(route):
                route.fulfill(
                    status=404,
                    content_type="application/json",
                    body=json.dumps({"error": "No encuentro este diagnóstico. Empieza uno nuevo para continuar."}),
                )

            stale_page.route("**/api/capabilities", capabilities_handler)
            stale_page.route("**/api/lead**", missing_lead_handler)
            stale_page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=stale_restore", wait_until="networkidle")
            stale_page.evaluate("localStorage.setItem('primer_empleado_lead_id', 'stale-lead')")
            stale_page.reload(wait_until="networkidle")
            # When /api/lead returns 404, session key is cleared and normal starter is shown
            stale_page.locator("#starter").wait_for(state="visible", timeout=5000)
            # Welcome-back UI must NOT appear — the starter should be the original one
            assert stale_page.get_by_text("Bienvenido de vuelta").count() == 0
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
