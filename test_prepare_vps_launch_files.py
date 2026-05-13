#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import prepare_vps_launch_files
from test_vps_inputs_validator import VALID_INPUTS


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_prepare_generates_env_and_privacy_config():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-files-") as tmp:
        base = Path(tmp)
        inputs = base / "VPS_INPUTS.local.md"
        env_output = base / ".env.generated"
        privacy_output = base / "privacy_config.json"
        inputs.write_text(VALID_INPUTS, encoding="utf-8")
        result = prepare_vps_launch_files.prepare(inputs, env_output, privacy_output)
        assert_true(result["ok"], result)
        env_text = env_output.read_text(encoding="utf-8")
        privacy = json.loads(privacy_output.read_text(encoding="utf-8"))
        assert_true("AI_PROVIDER=codex" in env_text, "No generó proveedor IA")
        assert_true("ADMIN_PASSWORD=clave-super-larga-2026" in env_text, "No generó contraseña CRM")
        assert_true("CRM_WEBHOOK_URL=" in env_text, "No generó variables webhook")
        assert_true(privacy["contact_email"] == "privacidad@example.com", "No generó privacidad desde inputs")
        assert_true("Completar" not in json.dumps(privacy, ensure_ascii=False), "La privacidad conserva placeholders")


def test_prepare_blocks_unfilled_inputs():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-files-") as tmp:
        base = Path(tmp)
        env_output = base / ".env.generated"
        privacy_output = base / "privacy_config.json"
        result = prepare_vps_launch_files.prepare(prepare_vps_launch_files.ROOT / "VPS_INPUTS.md", env_output, privacy_output)
        assert_true(not result["ok"], "La plantilla sin rellenar no debería generar archivos")
        assert_true(not env_output.exists() and not privacy_output.exists(), "No debería crear archivos si faltan inputs")


if __name__ == "__main__":
    test_prepare_generates_env_and_privacy_config()
    test_prepare_blocks_unfilled_inputs()
    print("prepare_vps_launch_files ok")
