#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUBLIC_PAGE = ROOT / "Agente_Real_CRM.html"
PRIVACY_PAGE = ROOT / "PRIVACY_BETA.md"


def run_step(name: str, command: list[str], *, timeout=120) -> dict:
    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except Exception as exc:
        return {"name": name, "ok": False, "output": str(exc)}
    return {
        "name": name,
        "ok": result.returncode == 0,
        "output": (result.stdout or "").strip()[-4000:],
        "command": " ".join(command),
    }


def static_page_check() -> dict:
    html = PUBLIC_PAGE.read_text(encoding="utf-8")
    required = [
        "¿Dónde se te escapa tiempo, dinero o clientes?",
        "analiza tu negocio como lo haría un consultor",
        "Por qué esta va primero",
        "Cómo funcionaría en la práctica",
        "¿Qué mejorarías de este diagnóstico?",
    ]
    forbidden = ["Descargar JSON", "informe potente"]
    missing = [item for item in required if item not in html]
    leaked = [item for item in forbidden if item.lower() in html.lower()]
    return {
        "name": "static_public_page",
        "ok": not missing and not leaked,
        "missing": missing,
        "leaked": leaked,
    }


def privacy_check(require_final: bool) -> dict:
    text = PRIVACY_PAGE.read_text(encoding="utf-8") if PRIVACY_PAGE.exists() else ""
    placeholders = ["Completar", "Definir", "revisarse antes de publicación definitiva"]
    found = [item for item in placeholders if item.lower() in text.lower()]
    return {
        "name": "privacy_beta",
        "ok": not found if require_final else True,
        "level": "error" if require_final else "warning",
        "placeholders": found,
        "message": "Privacidad final pendiente" if found else "Privacidad sin placeholders detectados",
    }


def main():
    parser = argparse.ArgumentParser(description="Release check de beta para Encuentra Tu Primer Empleado IA")
    parser.add_argument("--env", default=".env", help="Archivo .env que validará preflight_vps.py")
    parser.add_argument("--base", default="", help="URL base ya arrancada para ejecutar smoke test")
    parser.add_argument("--admin-user", default="")
    parser.add_argument("--admin-password", default="")
    parser.add_argument("--check-codex-live", action="store_true")
    parser.add_argument("--require-privacy-final", action="store_true", help="Falla si PRIVACY_BETA.md sigue con placeholders")
    args = parser.parse_args()

    steps = [
        run_step(
            "python_compile",
            [
                sys.executable,
                "-m",
                "py_compile",
                "app_server.py",
                "test_beta_smoke.py",
                "test_discovery_flow.py",
                "preflight_vps.py",
                "backup_crm.py",
                "release_check.py",
            ],
        ),
        static_page_check(),
        privacy_check(args.require_privacy_final),
    ]

    preflight_cmd = [sys.executable, "preflight_vps.py", "--env", args.env]
    if args.check_codex_live:
        preflight_cmd.append("--check-codex-live")
    steps.append(run_step("preflight", preflight_cmd, timeout=180 if args.check_codex_live else 60))

    if args.base:
        smoke_cmd = [sys.executable, "test_beta_smoke.py", "--base", args.base]
        if args.admin_user and args.admin_password:
            smoke_cmd += ["--admin-user", args.admin_user, "--admin-password", args.admin_password]
        steps.append(run_step("smoke", smoke_cmd, timeout=60))

    hard_failures = [step for step in steps if not step.get("ok") and step.get("level") != "warning"]
    result = {
        "ok": not hard_failures,
        "base": args.base,
        "env": args.env,
        "steps": steps,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
