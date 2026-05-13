#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from pathlib import Path


def skip(message: str) -> int:
    print(json.dumps({"ok": True, "skipped": True, "reason": message}, ensure_ascii=False, indent=2))
    return 0


def assert_true(condition, message: str):
    if not condition:
        raise AssertionError(message)


TEST_IP = f"198.51.{os.getpid() % 250}.{int(time.time() * 1000) % 250 + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba visual/funcional rápida de la página pública")
    parser.add_argument("--base", default="http://localhost:8787")
    parser.add_argument("--screenshots", default="", help="Carpeta opcional para guardar capturas")
    args = parser.parse_args()

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return skip(f"Playwright no está instalado: {exc}")

    screenshot_dir = Path(args.screenshots) if args.screenshots else None
    if screenshot_dir:
        screenshot_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "ok": False,
        "base": args.base,
        "checks": [],
    }

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as exc:
            return skip(f"Chromium de Playwright no está instalado: {exc}")

        try:
            context = browser.new_context(
                viewport={"width": 1440, "height": 950},
                extra_http_headers={"X-Forwarded-For": TEST_IP},
            )
            page = context.new_page()
            page.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=desktop", wait_until="networkidle")
            page.get_by_text("¿Dónde se te escapa tiempo, dinero o clientes?").wait_for(timeout=5000)
            page.get_by_text("analiza tu negocio como lo haría un consultor").wait_for(timeout=5000)
            page.get_by_text("Discovery en vivo").wait_for(timeout=5000)
            page.get_by_text("No formulario · preguntas según tu caso").wait_for(timeout=5000)
            page.get_by_text("Oportunidades sin seguimiento").wait_for(timeout=5000)
            page.get_by_text("La IA prepara; la persona aprueba.").wait_for(timeout=5000)
            cta_text = page.locator("section.starter button.start-primary").inner_text().strip()
            assert_true(cta_text == "Empezar diagnóstico", "El CTA principal debe sonar a sesión de diagnóstico, no a formulario genérico")
            assert_true(page.locator("#emailGate").count() == 0, "El email no debe pedirse antes de empezar")
            result["checks"].append("desktop_hero_copy_and_preview")
            if screenshot_dir:
                page.screenshot(path=str(screenshot_dir / "desktop-hero.png"), full_page=True)

            mobile_context = browser.new_context(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                extra_http_headers={"X-Forwarded-For": f"198.51.{(os.getpid() + 1) % 250}.{int(time.time() * 1000) % 250 + 1}"},
            )
            mobile = mobile_context.new_page()
            mobile.goto(f"{args.base}/Agente_Real_CRM.html?ui_test=mobile", wait_until="networkidle")
            hero_box = mobile.get_by_text("¿Dónde se te escapa tiempo, dinero o clientes?").bounding_box()
            cta_box = mobile.locator("section.starter button.start-primary").bounding_box()
            assert_true(hero_box and hero_box["y"] < 260, "El gancho principal debe aparecer pronto en móvil")
            assert_true(cta_box and cta_box["y"] < 840, "El CTA inicial debe estar visible sin fricción en móvil")
            result["checks"].append("mobile_above_fold")
            if screenshot_dir:
                mobile.screenshot(path=str(screenshot_dir / "mobile-hero.png"), full_page=True)
            mobile_context.close()

            page.locator("section.starter button.start-primary").click()
            page.wait_for_selector("textarea#input:not([disabled])", timeout=8000)
            page.get_by_text("Voy a hacerte de consultor durante unos minutos").wait_for(timeout=8000)
            page.get_by_text("última escena donde sentiste que se escapaba tiempo").wait_for(timeout=8000)
            assert_true(page.locator("#starter").count() == 0, "El bloque inicial debe desaparecer al arrancar")
            result["checks"].append("start_without_email")

            def chat_handler(route):
                time.sleep(1.8)
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "reply": (
                                "Veo una señal clara en email: entran oportunidades o conversaciones "
                                "que se quedan sin respuesta. Antes de recomendar nada, dime qué tipo "
                                "de email tendría más valor rescatar primero: leads, colaboraciones, "
                                "soporte o lectores que cuentan su caso."
                            ),
                            "ready_for_report": False,
                            "current_focus": "email y oportunidades sin responder",
                            "progress_label": "Explorando email con valor comercial",
                            "facts": {
                                "business_type": "newsletter",
                                "selected_process": "email",
                            },
                            "signals": [
                                "Hay correos diarios que podrían contener leads o aprendizajes de mercado",
                                "El usuario necesita clasificación y borradores, no respuestas autónomas",
                            ],
                            "candidate_processes": [
                                {
                                    "name": "triage de email",
                                    "why_it_matters": "reduce oportunidades perdidas",
                                    "confidence": 4,
                                }
                            ],
                            "open_gaps": ["volumen por tipo de correo", "criterios de respuesta"],
                            "stage": "deep_dive",
                        }
                    ),
                )

            page.route("**/api/chat", chat_handler)
            page.fill("#input", "Tengo una newsletter y recibo 10 o 15 emails al día que no sé cómo aprovechar.")
            page.click("#send")
            page.get_by_text("El agente está leyendo tu respuesta y extrayendo señales").wait_for(timeout=5000)
            page.get_by_text("Explorando email con valor comercial").wait_for(timeout=8000)
            page.get_by_text("Veo una señal clara en email").wait_for(timeout=8000)
            page.get_by_text("email y oportunidades sin responder").wait_for(timeout=5000)
            assert_true(page.get_by_text("Profundizando").count() >= 1, "La etapa interna debe traducirse a lenguaje humano")
            assert_true(page.get_by_text("deep_dive").count() == 0, "La UI no debe enseñar estados internos del agente")
            result["checks"].append("adaptive_chat_wait_state")
            if screenshot_dir:
                page.screenshot(path=str(screenshot_dir / "chat-wait-tested.png"), full_page=True)

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
