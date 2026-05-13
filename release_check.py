#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUBLIC_PAGE = ROOT / "Agente_Real_CRM.html"
PRIVACY_PAGE = ROOT / "PRIVACY_BETA.md"
PUBLIC_PRIVACY_PAGE = ROOT / "PRIVACY_BETA.html"
APP_SERVICE = ROOT / "deploy" / "primer-empleado-ia.service"
BACKUP_SERVICE = ROOT / "deploy" / "primer-empleado-ia-backup.service"
BACKUP_TIMER = ROOT / "deploy" / "primer-empleado-ia-backup.timer"
CADDYFILE = ROOT / "deploy" / "Caddyfile.example"
INSTALL_SCRIPT = ROOT / "deploy" / "install_vps.sh"
VERIFY_SCRIPT = ROOT / "deploy" / "verify_vps.sh"
PRIVACY_RENDERER = ROOT / "render_privacy.py"
PRIVACY_CONFIG_EXAMPLE = ROOT / "privacy_config.example.json"
MANUAL_PRODUCTION_TEST = ROOT / "MANUAL_PRODUCTION_TEST.md"


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
        "Señales detectadas",
        "Cómo funcionaría en la práctica",
        "Matriz de priorización",
        "Acepto que se use mi email y esta conversación",
        "Ayúdanos a mejorar este diagnóstico",
        "Qué echaste en falta",
        "Utilidad del diagnóstico",
    ]
    forbidden = ["Descargar JSON", "informe potente", "Ver mi diagnóstico"]
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
    public_text = PUBLIC_PRIVACY_PAGE.read_text(encoding="utf-8") if PUBLIC_PRIVACY_PAGE.exists() else ""
    placeholders = ["Completar", "Definir", "revisarse antes de publicación definitiva"]
    public_beta_markers = [
        "Antes de abrir tráfico público amplio",
        "política legal definitiva",
        "datos fiscales",
        "proveedores concretos",
    ]
    found = [item for item in placeholders if item.lower() in text.lower()]
    public_found = [item for item in public_beta_markers if item.lower() in public_text.lower()]
    return {
        "name": "privacy_beta",
        "ok": (not found and not public_found) if require_final else True,
        "level": "error" if require_final else "warning",
        "placeholders": found,
        "public_beta_markers": public_found,
        "message": "Privacidad final pendiente" if (found or public_found) else "Privacidad sin placeholders detectados",
    }


def deploy_config_check() -> dict:
    app_service = APP_SERVICE.read_text(encoding="utf-8") if APP_SERVICE.exists() else ""
    backup_service = BACKUP_SERVICE.read_text(encoding="utf-8") if BACKUP_SERVICE.exists() else ""
    backup_timer = BACKUP_TIMER.read_text(encoding="utf-8") if BACKUP_TIMER.exists() else ""
    caddyfile = CADDYFILE.read_text(encoding="utf-8") if CADDYFILE.exists() else ""
    install_script = INSTALL_SCRIPT.read_text(encoding="utf-8") if INSTALL_SCRIPT.exists() else ""
    verify_script = VERIFY_SCRIPT.read_text(encoding="utf-8") if VERIFY_SCRIPT.exists() else ""
    required = {
        "app_service_NoNewPrivileges": "NoNewPrivileges=true" in app_service,
        "app_service_local_write_path": "ReadWritePaths=/opt/primer-empleado-ia" in app_service,
        "app_service_network_online": "network-online.target" in app_service,
        "backup_service_NoNewPrivileges": "NoNewPrivileges=true" in backup_service,
        "backup_service_exec_path": "ExecStart=/usr/bin/python3 /opt/primer-empleado-ia/backup_crm.py" in backup_service,
        "backup_service_write_path": "ReadWritePaths=/opt/primer-empleado-ia" in backup_service,
        "backup_timer_persistent": "Persistent=true" in backup_timer,
        "backup_timer_enabled_target": "WantedBy=timers.target" in backup_timer,
        "caddy_hsts": "Strict-Transport-Security" in caddyfile,
        "caddy_microphone_policy": "microphone=(self)" in caddyfile,
        "caddy_body_limit": "max_size 2MB" in caddyfile,
        "caddy_reverse_proxy_local": "reverse_proxy 127.0.0.1:8787" in caddyfile,
        "install_script_executable": INSTALL_SCRIPT.exists() and bool(INSTALL_SCRIPT.stat().st_mode & 0o111),
        "install_script_env_guard": "ADMIN_PASSWORD=change-me" in install_script,
        "install_script_smoke": "test_beta_smoke.py" in install_script,
        "install_script_preflight_service_user": "--service-user" in install_script and "CHECK_CODEX_LIVE" in install_script,
        "verify_script_executable": VERIFY_SCRIPT.exists() and bool(VERIFY_SCRIPT.stat().st_mode & 0o111),
        "verify_script_public_beta_gate": "PUBLIC_BETA" in verify_script and "--public-beta" in verify_script,
        "verify_script_https_smoke": "https://${DOMAIN}" in verify_script and "test_beta_smoke.py" in verify_script,
        "verify_script_preflight_service_user": "--service-user" in verify_script and "APP_USER" in verify_script,
        "privacy_renderer_exists": PRIVACY_RENDERER.exists(),
        "privacy_config_example_exists": PRIVACY_CONFIG_EXAMPLE.exists(),
        "manual_production_test_exists": MANUAL_PRODUCTION_TEST.exists(),
    }
    missing = [name for name, ok in required.items() if not ok]
    return {
        "name": "deploy_config",
        "ok": not missing,
        "missing": missing,
    }


def public_beta_gate(args, env: dict) -> dict:
    checks = {
        "base_is_https": args.base.startswith("https://"),
        "base_is_not_localhost": not any(host in args.base for host in ["localhost", "127.0.0.1", "::1"]),
        "admin_credentials_supplied": bool(args.admin_user and args.admin_password and args.admin_password != "change-me"),
        "admin_password_matches_env": bool(args.admin_password and args.admin_password == env.get("ADMIN_PASSWORD", "")),
        "privacy_final_required": True,
        "codex_live_checked": bool(args.check_codex_live or env.get("AI_PROVIDER", "codex").lower() != "codex"),
    }
    missing = [name for name, ok in checks.items() if not ok]
    return {
        "name": "public_beta_gate",
        "ok": not missing,
        "missing": missing,
        "message": "Gate final para abrir beta pública en VPS con HTTPS, auth, privacidad final y proveedor IA verificado.",
    }


def main():
    parser = argparse.ArgumentParser(description="Release check de beta para Encuentra Tu Primer Empleado IA")
    parser.add_argument("--env", default=".env", help="Archivo .env que validará preflight_vps.py")
    parser.add_argument("--base", default="", help="URL base ya arrancada para ejecutar smoke test")
    parser.add_argument("--admin-user", default="")
    parser.add_argument("--admin-password", default="")
    parser.add_argument("--check-codex-live", action="store_true")
    parser.add_argument("--with-browser", action="store_true", help="Ejecuta pruebas Playwright de UI pública si --base está definido")
    parser.add_argument("--with-transcription", action="store_true", help="Ejecuta prueba local de audio real contra /transcribe si --base está definido")
    parser.add_argument("--service-user", default="", help="Usuario systemd para comprobar Codex en VPS")
    parser.add_argument("--require-privacy-final", action="store_true", help="Falla si PRIVACY_BETA.md sigue con placeholders")
    parser.add_argument("--public-beta", action="store_true", help="Gate estricto antes de abrir la beta pública en VPS")
    args = parser.parse_args()
    env_path = Path(args.env)
    if not env_path.is_absolute():
        env_path = ROOT / env_path
    env = load_env(env_path)
    require_privacy_final = args.require_privacy_final or args.public_beta
    check_codex_live = args.check_codex_live or args.public_beta
    if args.public_beta:
        args.check_codex_live = check_codex_live

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
                "test_ai_concurrency.py",
                "test_agent_quality_guard.py",
                "test_server_guards.py",
                "test_backup_crm.py",
                "test_privacy_renderer.py",
                "test_public_ui_flow.py",
                "test_public_report_flow.py",
                "test_crm_webhook_sync.py",
                "test_transcription_local.py",
                "render_privacy.py",
                "sync_crm_webhook.py",
            ],
        ),
        run_step("ai_concurrency", [sys.executable, "test_ai_concurrency.py"]),
        run_step("agent_quality_guard", [sys.executable, "test_agent_quality_guard.py"]),
        run_step("server_guards", [sys.executable, "test_server_guards.py"]),
        run_step("backup_crm", [sys.executable, "test_backup_crm.py"]),
        run_step("privacy_renderer", [sys.executable, "test_privacy_renderer.py"]),
        run_step("crm_webhook_sync", [sys.executable, "test_crm_webhook_sync.py"]),
        static_page_check(),
        privacy_check(require_privacy_final),
        deploy_config_check(),
    ]
    if args.public_beta:
        steps.append(public_beta_gate(args, env))

    preflight_cmd = [sys.executable, "preflight_vps.py", "--env", args.env]
    if args.service_user:
        preflight_cmd += ["--service-user", args.service_user]
    if check_codex_live:
        preflight_cmd.append("--check-codex-live")
    steps.append(run_step("preflight", preflight_cmd, timeout=180 if check_codex_live else 60))

    if args.base:
        smoke_cmd = [sys.executable, "test_beta_smoke.py", "--base", args.base]
        if args.admin_user and args.admin_password:
            smoke_cmd += ["--admin-user", args.admin_user, "--admin-password", args.admin_password]
        steps.append(run_step("smoke", smoke_cmd, timeout=60))
        if args.with_browser:
            steps.append(run_step("public_ui_flow", [sys.executable, "test_public_ui_flow.py", "--base", args.base], timeout=60))
            steps.append(run_step("public_report_flow", [sys.executable, "test_public_report_flow.py", "--base", args.base], timeout=60))
        if args.with_transcription:
            steps.append(run_step("transcription_local", [sys.executable, "test_transcription_local.py", "--base", args.base], timeout=240))
    elif args.with_browser or args.with_transcription:
        steps.append(
            {
                "name": "interactive_checks_requested",
                "ok": False,
                "output": "--with-browser y --with-transcription necesitan --base para saber qué servidor probar.",
            }
        )

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
