#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import render_privacy
import validate_manual_production_test
import validate_vps_inputs


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


def readiness(inputs_path: Path, manual_path: Path, env_path: Path, privacy_path: Path) -> dict:
    checks = {}
    blockers = []
    next_actions = []

    inputs = validate_vps_inputs.validate(inputs_path) if inputs_path.exists() else {
        "ok": False,
        "path": str(inputs_path),
        "errors": ["Falta VPS_INPUTS.local.md"],
        "warnings": [],
    }
    checks["vps_inputs"] = inputs
    if not inputs.get("ok"):
        blockers.append("Faltan datos reales de VPS/privacidad/CRM.")
        next_actions.append("Ejecuta `python3 generate_vps_inputs.py` para crear `VPS_INPUTS.local.md` de forma guiada y validable.")
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
        next_actions.append("Genera `privacy_config.json` y después `python3 render_privacy.py --config privacy_config.json`.")

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
        next_actions.append("Ejecuta `python3 launch_go_no_go.py --public-beta ...` contra el dominio HTTPS.")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume el estado real de preparación para beta pública")
    parser.add_argument("--inputs", default=str(ROOT / "VPS_INPUTS.local.md"))
    parser.add_argument("--manual-test", default=str(ROOT / "MANUAL_PRODUCTION_TEST.local.md"))
    parser.add_argument("--env", default=str(ROOT / ".env.generated"))
    parser.add_argument("--privacy", default=str(ROOT / "privacy_config.json"))
    args = parser.parse_args()
    result = readiness(Path(args.inputs), Path(args.manual_test), Path(args.env), Path(args.privacy))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
