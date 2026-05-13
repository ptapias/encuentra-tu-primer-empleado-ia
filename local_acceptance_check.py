#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def git_head_short() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def git_worktree_dirty() -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return False
    return result.returncode == 0 and bool((result.stdout or "").strip())


def run_step(name: str, command: list[str], *, timeout: int = 420) -> dict:
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    output = completed.stdout or ""
    parsed = None
    try:
        parsed = json.loads(output)
    except Exception:
        parsed = None
    return {
        "name": name,
        "ok": completed.returncode == 0 and (parsed.get("ok", True) if isinstance(parsed, dict) else True),
        "returncode": completed.returncode,
        "command": " ".join(command),
        "parsed": parsed,
        "output": output.strip()[-4000:],
    }


def read_json(url: str, timeout: int = 8) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def find_codex_bin() -> str:
    return shutil.which("codex") or "/Applications/Codex.app/Contents/Resources/codex"


def write_temp_env(base: str) -> Path:
    tmp = Path(tempfile.NamedTemporaryFile("w", delete=False, prefix="primer-empleado-local-", suffix=".env").name)
    parsed_host = "localhost"
    parsed_port = "8787"
    if ":" in base.rsplit("/", 1)[0]:
        parsed_port = base.rsplit(":", 1)[-1].split("/", 1)[0]
    tmp.write_text(
        "\n".join(
            [
                "HOST=localhost",
                f"PORT={parsed_port}",
                "AI_PROVIDER=codex",
                f"CODEX_BIN={find_codex_bin()}",
                "ALLOW_AI_FALLBACK=false",
                "ADMIN_USER=admin",
                "ADMIN_PASSWORD=local-check-password",
                "MAX_AI_CONCURRENCY=1",
                "AI_QUEUE_WAIT_SECONDS=8",
                "BETA_NOINDEX=true",
                f"APP_VERSION={git_head_short()}",
                f"WHISPER_BIN={shutil.which('whisper') or ''}",
                f"FFMPEG_BIN={shutil.which('ffmpeg') or ''}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return tmp


def main() -> int:
    parser = argparse.ArgumentParser(description="Semáforo local antes de enseñar el diagnóstico o pasar al VPS")
    parser.add_argument("--base", default="http://localhost:8787")
    parser.add_argument("--with-transcription", action="store_true", help="Prueba audio real local si Whisper/ffmpeg están disponibles")
    parser.add_argument("--with-real-agent", action="store_true", help="Ejecuta casos completos con Codex real; puede tardar varios minutos")
    parser.add_argument("--timeout", type=int, default=420)
    args = parser.parse_args()

    checks = []
    blockers = []
    warnings = []
    next_actions = []
    expected_version = git_head_short()
    worktree_dirty = git_worktree_dirty()
    if worktree_dirty:
        warnings.append(
            "Hay cambios locales sin commit. El semáforo valida que el servidor coincide con el último commit, pero conviene cerrar o commitear antes de invitar testers."
        )

    try:
        health = read_json(f"{args.base.rstrip('/')}/healthz")
        server_check = {
            "name": "server_running",
            "ok": True,
            "health": health,
            "expected_version": expected_version,
            "worktree_dirty": worktree_dirty,
        }
        if expected_version and str(health.get("version")) != expected_version:
            server_check["ok"] = False
            blockers.append(
                f"El servidor vivo expone /healthz.version={health.get('version')}, pero el código actual es {expected_version}. Reinicia la beta local."
            )
        checks.append(server_check)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        checks.append({"name": "server_running", "ok": False, "error": str(exc)})
        blockers.append(f"No puedo conectar con {args.base}. Arranca `python3 app_server.py` y vuelve a ejecutar este chequeo.")
        print(
            json.dumps(
                {
                    "ok": False,
                    "verdict": "NO_GO_LOCAL",
                    "blockers": blockers,
                    "warnings": warnings,
                    "next_actions": ["Arrancar servidor local y repetir `python3 local_acceptance_check.py`."],
                    "checks": checks,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    env_path = write_temp_env(args.base)
    release_command = [
        sys.executable,
        "release_check.py",
        "--env",
        str(env_path),
        "--base",
        args.base,
        "--with-browser",
    ]
    if args.with_transcription:
        release_command.append("--with-transcription")
    release = run_step("release_check_local", release_command, timeout=args.timeout)
    checks.append(release)
    if not release["ok"]:
        blockers.append("Falla el release check local. Mira `checks.release_check_local` para el detalle.")

    if args.with_real_agent:
        discovery = run_step(
            "real_agent_discovery_cases",
            [
                sys.executable,
                "test_discovery_flow.py",
                "--base",
                args.base,
                "--client-ip",
                "198.51.100.40",
            ],
            timeout=900,
        )
        checks.append(discovery)
        if not discovery["ok"]:
            blockers.append("Falla la prueba de discovery con agente real.")
    else:
        warnings.append("No se ejecutaron casos completos con Codex real. Añade `--with-real-agent` antes de invitar testers externos.")

    if not args.with_transcription:
        warnings.append("No se probó transcripción de audio real. Añade `--with-transcription` si el micro es parte central de la prueba.")

    if blockers:
        next_actions.append("Corrige los bloqueos y repite el semáforo local.")
    else:
        next_actions.append("Puedes hacer una prueba manual local completa: conversación, informe, email final, feedback y revisión en CRM.")
        next_actions.append("Para beta externa, rellena `VPS_INPUTS.local.md` y sigue `VPS_LAUNCH_PACKET.md`.")

    result = {
        "ok": not blockers,
        "verdict": "GO_LOCAL" if not blockers else "NO_GO_LOCAL",
        "base": args.base,
        "blockers": blockers,
        "warnings": warnings,
        "next_actions": next_actions,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
