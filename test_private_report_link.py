#!/usr/bin/env python3
import json
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import app_server


class QuietHandler(app_server.Handler):
    def log_message(self, _format, *_args):
        return


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def request_text(base: str, path: str):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")


def main():
    original_db = app_server.DB_FILE
    original_noindex = app_server.BETA_NOINDEX
    server = None
    try:
        with tempfile.TemporaryDirectory(prefix="primer-empleado-report-link-") as tmp:
            app_server.DB_FILE = Path(tmp) / "crm.sqlite3"
            app_server.BETA_NOINDEX = True
            app_server.init_db()
            lead = app_server.create_lead("tester@example.com")
            token = "test-token-private"
            app_server.update_lead(
                lead["lead_id"],
                facts={"report_token": token},
                transcript=[{"role": "user", "content": "mensaje privado del tester"}],
                outcome={
                    "summary": "Diagnóstico accionable del negocio.",
                    "recommended_employee": "Empleado IA de seguimiento comercial",
                    "recommendation_reason": "Hay fuga de leads y se puede empezar con revisión humana.",
                    "evidence_summary": ["Llegan leads por email", "Hay revisión humana"],
                    "opportunities": [
                        {
                            "name": "Seguimiento de leads",
                            "problem": "Muchos leads quedan sin respuesta.",
                            "ai_employee": "Asistente IA de seguimiento",
                            "first_step": "Reunir 20 conversaciones reales.",
                        }
                    ],
                    "seven_day_plan": ["Reunir ejemplos", "Definir categorías"],
                    "do_not_automate_yet": ["Cerrar ventas sin revisión"],
                },
                stage="informe",
                status="report_generated",
            )
            server = app_server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            path = app_server.public_report_url(lead["lead_id"], token)
            status, headers, html = request_text(base, path)
            expect(status == 200, "El enlace privado debería cargar")
            expect("noindex" in headers.get("X-Robots-Tag", ""), "El enlace privado debería ser noindex")
            expect("Empleado IA de seguimiento comercial" in html, "El informe público debería mostrar recomendación")
            expect("tester@example.com" not in html, "El enlace privado no debería exponer email")
            expect("mensaje privado del tester" not in html, "El enlace privado no debería exponer conversación")
            try:
                request_text(base, f"/r/{lead['lead_id']}/token-malo")
                raise AssertionError("Un token incorrecto no debería cargar")
            except urllib.error.HTTPError as exc:
                expect(exc.code == 404, "Un token incorrecto debería devolver 404")
            print(json.dumps({"ok": True, "path": path}, ensure_ascii=False))
    finally:
        if server:
            server.shutdown()
            server.server_close()
        app_server.DB_FILE = original_db
        app_server.BETA_NOINDEX = original_noindex


if __name__ == "__main__":
    raise SystemExit(main())
