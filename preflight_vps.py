#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent


def load_env(path: Path) -> dict:
    values = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check(condition, name, message, *, level="error"):
    return {"ok": bool(condition), "name": name, "level": level, "message": message}


def command_exists(path_or_name: str) -> bool:
    if not path_or_name:
        return False
    path = Path(path_or_name)
    if path.is_absolute() or "/" in path_or_name:
        return path.exists() and os.access(path, os.X_OK)
    return shutil.which(path_or_name) is not None


def can_write(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".preflight-", dir=directory, delete=True) as handle:
            handle.write(b"ok")
        return True
    except OSError:
        return False


def codex_live_check(codex_bin: str) -> dict:
    try:
        result = subprocess.run(
            [codex_bin, "exec", "--skip-git-repo-check", "--ephemeral", "Responde solo: ok"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=90,
        )
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
    output = (result.stdout or "").strip()
    return {"ok": result.returncode == 0 and "ok" in output.lower(), "message": output[-500:]}


def main():
    parser = argparse.ArgumentParser(description="Preflight VPS para Encuentra Tu Primer Empleado IA")
    parser.add_argument("--env", default=".env", help="Ruta al archivo .env")
    parser.add_argument("--check-codex-live", action="store_true", help="Ejecuta una llamada real a Codex CLI")
    args = parser.parse_args()

    env_path = Path(args.env)
    if not env_path.is_absolute():
        env_path = ROOT / env_path
    env = {**os.environ, **load_env(env_path)}

    provider = env.get("AI_PROVIDER", "codex").lower()
    codex_bin = env.get("CODEX_BIN") or shutil.which("codex") or ""
    openai_key = env.get("OPENAI_API_KEY", "")
    admin_password = env.get("ADMIN_PASSWORD", "")
    allow_fallback = env.get("ALLOW_AI_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
    host = env.get("HOST", "")
    port = env.get("PORT", "")
    max_ai_concurrency = env.get("MAX_AI_CONCURRENCY", "1")
    ai_queue_wait = env.get("AI_QUEUE_WAIT_SECONDS", "8")
    whisper_bin = env.get("WHISPER_BIN") or shutil.which("whisper") or ""
    ffmpeg_bin = env.get("FFMPEG_BIN") or shutil.which("ffmpeg") or ""

    checks = [
        check(sys.version_info >= (3, 10), "python_version", "Python 3.10+ disponible"),
        check(env_path.exists(), "env_file", f"Archivo env encontrado: {env_path}"),
        check(provider in {"codex", "openai", "fallback"}, "ai_provider", f"AI_PROVIDER={provider}"),
        check(bool(host), "host", f"HOST={host or 'vacío'}", level="warning"),
        check(bool(port and str(port).isdigit()), "port", f"PORT={port or 'vacío'}"),
        check(str(max_ai_concurrency).isdigit() and int(max_ai_concurrency) >= 1, "max_ai_concurrency", f"MAX_AI_CONCURRENCY={max_ai_concurrency}"),
        check(str(ai_queue_wait).replace(".", "", 1).isdigit(), "ai_queue_wait", f"AI_QUEUE_WAIT_SECONDS={ai_queue_wait}"),
        check(bool(admin_password and admin_password != "change-me"), "admin_password", "ADMIN_PASSWORD debe estar configurado y no ser el valor de ejemplo"),
        check(not allow_fallback, "ai_fallback_disabled", "ALLOW_AI_FALLBACK debería estar en false para beta pública"),
        check(can_write(ROOT), "app_directory_writable", f"Directorio escribible: {ROOT}"),
    ]

    if provider == "codex":
        checks.append(check(command_exists(codex_bin), "codex_bin", f"Codex CLI disponible: {codex_bin or 'no encontrado'}"))
        if args.check_codex_live and command_exists(codex_bin):
            live = codex_live_check(codex_bin)
            checks.append(check(live["ok"], "codex_live", live["message"]))
    elif provider == "openai":
        checks.append(check(bool(openai_key), "openai_api_key", "OPENAI_API_KEY configurada"))
    else:
        checks.append(check(False, "fallback_provider", "AI_PROVIDER=fallback sirve para pruebas, no para beta pública", level="warning"))

    checks.append(check(command_exists(ffmpeg_bin), "ffmpeg", f"ffmpeg disponible: {ffmpeg_bin or 'no encontrado'}", level="warning"))
    checks.append(check(command_exists(whisper_bin), "whisper", f"Whisper disponible: {whisper_bin or 'no encontrado'}", level="warning"))

    errors = [item for item in checks if item["level"] == "error" and not item["ok"]]
    warnings = [item for item in checks if item["level"] == "warning" and not item["ok"]]
    result = {
        "ok": not errors,
        "env": str(env_path),
        "provider": provider,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
