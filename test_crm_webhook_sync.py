#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class CaptureHandler(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        self.__class__.calls.append({"headers": dict(self.headers), "body": json.loads(body)})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        return


def create_sample_db(path: Path):
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            """
            CREATE TABLE leads (
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
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                event TEXT NOT NULL,
                payload_json TEXT,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO leads (
                id, email, created_at, updated_at, stage, status, facts_json,
                signals_json, outcome_json, transcript_json, feedback_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "lead-123",
                "persona@example.com",
                1,
                2,
                "informe",
                "feedback_saved",
                json.dumps({"attribution": {"source": "youtube"}, "cta_interest": {"segment": "cohort"}}),
                json.dumps(["10 emails al día"]),
                json.dumps({"recommended_employee": {"name": "Asistente de email"}, "crm_summary": {"score": 82}}),
                json.dumps([{"role": "user", "content": "Recibo muchos emails"}]),
                json.dumps({"rating": "5"}),
            ),
        )


def main():
    with tempfile.TemporaryDirectory(prefix="crm-sync-test-") as tmp:
        db_path = Path(tmp) / "crm.sqlite3"
        create_sample_db(db_path)

        CaptureHandler.calls = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "sync_crm_webhook.py"),
                    "--db",
                    str(db_path),
                    "--url",
                    f"http://127.0.0.1:{port}/hook",
                    "--secret",
                    "secreto",
                    "--limit",
                    "10",
                ],
                cwd=str(ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=20,
            )
            assert_true(result.returncode == 0, result.stdout)
            data = json.loads(result.stdout)
            assert_true(data["ok"] and data["sent"] == 1, "La sincronización debería enviar un lead")
            assert_true(len(CaptureHandler.calls) == 1, "El receptor debería recibir un webhook")
            call = CaptureHandler.calls[0]
            assert_true(call["headers"].get("X-Crm-Webhook-Secret") == "secreto", "Falta secreto del webhook")
            assert_true(call["headers"].get("X-Crm-Event") == "lead_snapshot_synced", "Falta tipo de evento")
            body = call["body"]
            assert_true(body["event"] == "lead_snapshot_synced", "Evento incorrecto")
            assert_true(body["payload"]["lead"]["email"] == "persona@example.com", "Email no incluido")
            assert_true(body["payload"]["lead"]["outcome"]["crm_summary"]["score"] == 82, "Outcome no incluido")
            with sqlite3.connect(str(db_path)) as conn:
                row = conn.execute("SELECT event FROM events WHERE lead_id = ?", ("lead-123",)).fetchone()
            assert_true(row and row[0] == "crm_webhook_snapshot_synced", "Debe quedar recibo local de sincronización")
        finally:
            server.shutdown()
            thread.join(timeout=5)

    print("crm_webhook_sync ok")


if __name__ == "__main__":
    main()
