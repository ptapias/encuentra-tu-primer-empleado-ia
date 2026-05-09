#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WHISPER = "/opt/homebrew/bin/whisper"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
CRM_FILE = ROOT / "crm_leads.jsonl"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path == "/crm":
            self._handle_crm()
            return

        if self.path != "/transcribe":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            self._json({"error": "No audio received"}, 400)
            return

        body = self.rfile.read(length)
        try:
            text = transcribe_audio(body)
            self._json({"text": text})
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def _handle_crm(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            self._json({"error": "No payload received"}, 400)
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            with CRM_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._json({"ok": True, "path": str(CRM_FILE)})
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def _json(self, payload, status=200):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def transcribe_audio(body: bytes) -> str:
    if not Path(WHISPER).exists():
        raise RuntimeError("Whisper local no está instalado en /opt/homebrew/bin/whisper")
    if not Path(FFMPEG).exists():
        raise RuntimeError("ffmpeg local no está instalado en /opt/homebrew/bin/ffmpeg")

    with tempfile.TemporaryDirectory(prefix="primer-empleado-ia-") as tmp:
        tmpdir = Path(tmp)
        webm = tmpdir / "audio.webm"
        wav = tmpdir / "audio.wav"
        webm.write_bytes(body)

        subprocess.run(
            [FFMPEG, "-y", "-i", str(webm), "-ar", "16000", "-ac", "1", str(wav)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                WHISPER,
                str(wav),
                "--model",
                "tiny",
                "--language",
                "Spanish",
                "--fp16",
                "False",
                "--output_format",
                "txt",
                "--output_dir",
                str(tmpdir),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )

        txt = wav.with_suffix(".txt")
        if not txt.exists():
            raise RuntimeError("Whisper no generó transcripción")
        return txt.read_text(encoding="utf-8").strip()


def main():
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("localhost", 8787), Handler)
    print("Serving MVP on http://localhost:8787/Prototipo_Conversacional.html")
    print("Local transcription endpoint enabled at /transcribe")
    server.serve_forever()


if __name__ == "__main__":
    main()
