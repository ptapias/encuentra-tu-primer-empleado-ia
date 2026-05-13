#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib import request


def skip(reason: str) -> int:
    print(json.dumps({"ok": True, "skipped": True, "reason": reason}, ensure_ascii=False, indent=2))
    return 0


TEST_IP = f"198.51.{os.getpid() % 250}.{int(time.time() * 1000) % 250 + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba local opcional de transcripción con audio real")
    parser.add_argument("--base", default="http://localhost:8787")
    parser.add_argument("--text", default="Mi negocio recibe correos todos los días y quiero priorizarlos mejor.")
    parser.add_argument("--expect-word", default="", help="Opcional: palabra que debería aparecer en la transcripción")
    args = parser.parse_args()

    say_bin = shutil.which("say")
    ffmpeg_bin = shutil.which("ffmpeg")
    if not say_bin:
        return skip("No está disponible el comando macOS say para generar audio de prueba")
    if not ffmpeg_bin:
        return skip("No está disponible ffmpeg para convertir audio de prueba")

    try:
        with request.urlopen(f"{args.base}/api/capabilities", timeout=5) as response:
            capabilities = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"No se pudo leer /api/capabilities: {exc}"}, ensure_ascii=False, indent=2))
        return 1
    if not capabilities.get("transcription", {}).get("available"):
        return skip("El servidor no tiene transcripción disponible según /api/capabilities")

    with tempfile.TemporaryDirectory(prefix="primer-empleado-transcribe-test-") as tmp:
        tmpdir = Path(tmp)
        aiff = tmpdir / "sample.aiff"
        webm = tmpdir / "sample.webm"
        subprocess.run([say_bin, "-o", str(aiff), args.text], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(
            [ffmpeg_bin, "-y", "-i", str(aiff), "-c:a", "libopus", "-b:a", "32k", str(webm)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        req = request.Request(
            f"{args.base}/transcribe",
            data=webm.read_bytes(),
            headers={"Content-Type": "audio/webm", "X-Forwarded-For": TEST_IP},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=180) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"/transcribe falló: {exc}"}, ensure_ascii=False, indent=2))
            return 1

    text = (payload.get("text") or "").strip()
    ok = bool(text)
    if args.expect_word:
        ok = ok and args.expect_word.lower() in text.lower()
    print(
        json.dumps(
            {
                "ok": ok,
                "base": args.base,
                "input_text": args.text,
                "transcribed_text": text,
                "expect_word": args.expect_word,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
