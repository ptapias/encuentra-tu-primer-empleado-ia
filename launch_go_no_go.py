#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOCAL_HOST_MARKERS = ("localhost", "127.0.0.1", "::1")


def run_release_check(args) -> dict:
    command = [
        sys.executable,
        "release_check.py",
        "--env",
        args.env,
        "--base",
        args.base,
        "--admin-user",
        args.admin_user,
        "--admin-password",
        args.admin_password,
    ]
    if args.public_beta:
        command.append("--public-beta")
    if args.check_codex_live:
        command.append("--check-codex-live")
    if args.service_user:
        command += ["--service-user", args.service_user]
    if args.with_browser:
        command.append("--with-browser")
    if args.with_transcription:
        command.append("--with-transcription")
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=args.timeout,
    )
    output = completed.stdout or ""
    try:
        parsed = json.loads(output)
    except Exception:
        parsed = {"ok": False, "parse_error": True, "raw_output": output[-4000:]}
    parsed["command"] = " ".join(command)
    parsed["returncode"] = completed.returncode
    return parsed


def failed_steps(release_result: dict) -> list[dict]:
    return [
        {"name": step.get("name", "unknown"), "output": step.get("output") or step.get("message") or step}
        for step in release_result.get("steps", [])
        if not step.get("ok") and step.get("level") != "warning"
    ]


def evaluate(args, release_result: dict) -> dict:
    blockers = []
    warnings = []
    next_actions = []

    if not release_result.get("ok"):
        for step in failed_steps(release_result):
            blockers.append(f"Falla `{step['name']}`: {str(step['output'])[:500]}")
        if not blockers:
            blockers.append("release_check.py no terminó correctamente o no devolvió JSON válido.")

    if args.public_beta:
        if not args.base.startswith("https://"):
            blockers.append("La beta pública exige HTTPS.")
        if any(marker in args.base for marker in LOCAL_HOST_MARKERS):
            blockers.append("La beta pública no puede apuntar a localhost.")
        if not args.admin_password or args.admin_password == "change-me":
            blockers.append("Falta una contraseña real para el CRM.")
        if not args.manual_production_tested:
            blockers.append("Falta confirmar prueba manual en producción con `--manual-production-tested`.")
        if not args.crm_reviewed:
            blockers.append("Falta confirmar revisión de CRM/CSV con `--crm-reviewed`.")
        if args.mic_required and not args.mic_tested:
            blockers.append("El micro está marcado como requerido, pero falta `--mic-tested`.")
    else:
        if args.base.startswith("http://") and not any(marker in args.base for marker in LOCAL_HOST_MARKERS):
            warnings.append("La URL no usa HTTPS. Vale para local, no para testers externos.")
        if not args.manual_production_tested:
            warnings.append("Para mandar testers reales, registra al menos una prueba manual con MANUAL_PRODUCTION_TEST.md.")
        if not args.crm_reviewed:
            warnings.append("Antes de testers, revisa que el lead aparece completo en CRM y CSV.")

    if not args.with_browser:
        warnings.append("No se ejecutaron pruebas de navegador. Añade `--with-browser` antes de enseñar la beta.")
    if args.mic_required and not args.with_transcription:
        warnings.append("El micro importa en la experiencia, pero no se ejecutó `--with-transcription`.")

    if blockers:
        next_actions.append("Corrige los bloqueos y vuelve a ejecutar este go/no-go.")
    elif args.public_beta:
        next_actions.append("Abrir beta controlada a 5-10 testers y monitorizar CRM, latencia IA y feedback durante 48 horas.")
    else:
        next_actions.append("Puedes usarlo como validación local/controlada; para testers externos ejecuta con `--public-beta` contra HTTPS.")

    return {
        "verdict": "GO" if not blockers else "NO_GO",
        "base": args.base,
        "public_beta": args.public_beta,
        "blockers": blockers,
        "warnings": warnings,
        "next_actions": next_actions,
        "release_ok": bool(release_result.get("ok")),
        "release_command": release_result.get("command", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Go/no-go operativo antes de abrir la beta")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--base", required=True)
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-password", default="")
    parser.add_argument("--service-user", default="")
    parser.add_argument("--public-beta", action="store_true")
    parser.add_argument("--check-codex-live", action="store_true")
    parser.add_argument("--with-browser", action="store_true")
    parser.add_argument("--with-transcription", action="store_true")
    parser.add_argument("--manual-production-tested", action="store_true")
    parser.add_argument("--crm-reviewed", action="store_true")
    parser.add_argument("--mic-tested", action="store_true")
    parser.add_argument("--mic-required", action="store_true", default=True)
    parser.add_argument("--timeout", type=int, default=420)
    args = parser.parse_args()

    release_result = run_release_check(args)
    verdict = evaluate(args, release_result)
    verdict["release_summary"] = {
        "ok": release_result.get("ok"),
        "returncode": release_result.get("returncode"),
        "failed_steps": failed_steps(release_result),
    }
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0 if verdict["verdict"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
