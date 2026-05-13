#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import render_privacy
import validate_manual_production_test
import validate_vps_inputs
import generate_vps_inputs


ROOT = Path(__file__).resolve().parent


def file_state(path: Path) -> dict:
    return {"path": str(path), "exists": path.exists()}


def privacy_state(path: Path) -> dict:
    state = file_state(path)
    if not path.exists():
        state.update({"ok": False, "errors": ["Falta privacy_config.json final"]})
        return state
    try:
        render_privacy.load_config(path)
        state.update({"ok": True, "errors": []})
    except SystemExit as exc:
        state.update({"ok": False, "errors": [str(exc)]})
    return state


def answers_state(path: Path) -> dict:
    state = file_state(path)
    if not path.exists():
        state.update({"ok": False, "errors": ["Falta VPS_ANSWERS.local.json"], "empty_required": []})
        return state
    try:
        answers = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        state.update({"ok": False, "errors": [f"JSON inválido: {exc}"], "empty_required": []})
        return state
    required = [label for label in validate_vps_inputs.REQUIRED_LABELS if not str(answers.get(label, "")).strip()]
    known_labels = {label for _section, label, _default, _help in generate_vps_inputs.FIELDS}
    unknown = sorted(label for label in answers if label not in known_labels)
    state.update(
        {
            "ok": not required and not unknown,
            "errors": [f"Faltan campos obligatorios en JSON: {', '.join(required[:6])}"] if required else [],
            "warnings": [f"Campos no reconocidos en JSON: {', '.join(unknown[:6])}"] if unknown else [],
            "empty_required": required,
            "filled_required": len(validate_vps_inputs.REQUIRED_LABELS) - len(required),
            "required_fields": len(validate_vps_inputs.REQUIRED_LABELS),
        }
    )
    return state


def readiness(inputs_path: Path, manual_path: Path, env_path: Path, privacy_path: Path, answers_path: Path | None = None) -> dict:
    checks = {}
    blockers = []
    next_actions = []
    answers_path = answers_path or (ROOT / "VPS_ANSWERS.local.json")
    answers = answers_state(answers_path)
    checks["answers_json"] = answers

    inputs = validate_vps_inputs.validate(inputs_path) if inputs_path.exists() else {
        "ok": False,
        "path": str(inputs_path),
        "errors": ["Falta VPS_INPUTS.local.md"],
        "warnings": [],
    }
    checks["vps_inputs"] = inputs
    if not inputs.get("ok"):
        blockers.append("Faltan datos reales de VPS/privacidad/CRM.")
        next_actions.append("Abre `NEXT_DEPLOYMENT_HANDOFF.md` si quieres la versión corta: 8 datos pendientes, comandos y gate final.")
        if answers["exists"]:
            next_actions.append("Rellena `VPS_ANSWERS.local.json` y después ejecuta `python3 generate_vps_inputs.py --answers-json VPS_ANSWERS.local.json`.")
        else:
            next_actions.append("Ejecuta `python3 generate_vps_inputs.py` para crear `VPS_INPUTS.local.md` de forma guiada y validable.")
            next_actions.append("Si prefieres rellenarlo en un archivo, ejecuta `python3 generate_vps_inputs.py --print-answers-template > VPS_ANSWERS.local.json`, edítalo y luego `python3 generate_vps_inputs.py --answers-json VPS_ANSWERS.local.json`.")
        next_actions.append("Después ejecuta `python3 validate_vps_inputs.py --path VPS_INPUTS.local.md`.")

    env = file_state(env_path)
    env["ok"] = env["exists"]
    checks["env"] = env
    if not env["ok"]:
        blockers.append("Falta `.env` o `.env.generated` para el VPS.")
        next_actions.append("Ejecuta `python3 prepare_vps_launch_files.py --inputs VPS_INPUTS.local.md` y usa `.env.generated` para instalar.")

    privacy = privacy_state(privacy_path)
    checks["privacy_config"] = privacy
    if not privacy.get("ok"):
        blockers.append("Falta privacidad final sin placeholders.")
        if env["ok"]:
            next_actions.append("Genera o revisa `privacy_config.json` y después renderiza con `python3 render_privacy.py --config privacy_config.json`.")
        else:
            next_actions.append("El preparador también generará `privacy_config.json`; después renderiza con `python3 render_privacy.py --config privacy_config.json`.")

    manual = validate_manual_production_test.validate(manual_path) if manual_path.exists() else {
        "ok": False,
        "path": str(manual_path),
        "errors": ["Falta MANUAL_PRODUCTION_TEST.local.md validado contra HTTPS"],
        "warnings": [],
    }
    checks["manual_production_test"] = manual
    if not manual.get("ok"):
        blockers.append("Falta prueba manual de producción validada.")
        next_actions.append("Tras desplegar en HTTPS, copia `MANUAL_PRODUCTION_TEST.md` a `.local.md`, rellénalo y valida con `python3 validate_manual_production_test.py`.")

    if not blockers:
        status = "ready_for_public_go_no_go"
        next_actions.append("Ejecuta `DOMAIN=tu-dominio PUBLIC_BETA=true BROWSER_CHECKS=true TRANSCRIPTION_CHECK=true MANUAL_PRODUCTION_TESTED=true MANUAL_TEST_PATH=MANUAL_PRODUCTION_TEST.local.md CRM_REVIEWED=true MIC_TESTED=true ./deploy/verify_vps.sh` contra el dominio HTTPS.")
        next_actions.append("Si el micro queda fuera de la primera beta, usa `MIC_OPTIONAL=true` en lugar de `MIC_TESTED=true`.")
    elif inputs.get("ok") and env.get("ok") and privacy.get("ok"):
        status = "ready_for_vps_manual_test"
    elif inputs.get("ok"):
        status = "ready_to_generate_launch_files"
    else:
        status = "blocked_on_launch_inputs"

    return {
        "ok": not blockers,
        "status": status,
        "blockers": blockers,
        "next_actions": next_actions,
        "checks": checks,
    }


def plain_report(result: dict) -> str:
    lines = []
    if result.get("ok"):
        lines.append("Estado: listo para go/no-go público.")
    else:
        lines.append(f"Estado: {result.get('status', 'desconocido')}.")
    blockers = result.get("blockers") or []
    if blockers:
        lines.append("")
        lines.append("Bloqueos:")
        for blocker in blockers:
            lines.append(f"- {blocker}")
    answers = result.get("checks", {}).get("answers_json", {})
    missing = answers.get("empty_required") or []
    if missing:
        lines.append("")
        lines.append("Datos que faltan en VPS_ANSWERS.local.json:")
        for item in missing:
            lines.append(f"- {item}")
    actions = result.get("next_actions") or []
    if actions:
        lines.append("")
        lines.append("Siguiente acción:")
        for index, action in enumerate(actions, start=1):
            lines.append(f"{index}. {action}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume el estado real de preparación para beta pública")
    parser.add_argument("--inputs", default=str(ROOT / "VPS_INPUTS.local.md"))
    parser.add_argument("--manual-test", default=str(ROOT / "MANUAL_PRODUCTION_TEST.local.md"))
    parser.add_argument("--env", default=str(ROOT / ".env.generated"))
    parser.add_argument("--privacy", default=str(ROOT / "privacy_config.json"))
    parser.add_argument("--answers-json", default=str(ROOT / "VPS_ANSWERS.local.json"))
    parser.add_argument("--plain", action="store_true", help="Muestra una salida legible para revisar qué falta")
    args = parser.parse_args()
    result = readiness(Path(args.inputs), Path(args.manual_test), Path(args.env), Path(args.privacy), Path(args.answers_json))
    if args.plain:
        print(plain_report(result), end="")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
