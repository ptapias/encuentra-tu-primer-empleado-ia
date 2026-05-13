#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import beta_readiness_status
import generate_vps_inputs
import prepare_vps_launch_files
from test_manual_production_validator import filled_doc
from test_vps_inputs_validator import VALID_INPUTS


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_default_repo_is_blocked_on_launch_inputs():
    result = beta_readiness_status.readiness(
        beta_readiness_status.ROOT / "VPS_INPUTS.local.md",
        beta_readiness_status.ROOT / "MANUAL_PRODUCTION_TEST.local.md",
        beta_readiness_status.ROOT / ".env.generated",
        beta_readiness_status.ROOT / "privacy_config.json",
    )
    assert_true(not result["ok"], "El repo sin inputs locales no debería estar listo para público")
    assert_true(result["status"] in {"blocked_on_launch_inputs", "ready_to_generate_launch_files", "ready_for_vps_manual_test"}, result)
    assert_true(
        any("generate_vps_inputs.py" in action for action in result["next_actions"]),
        "El siguiente paso debería recomendar el generador guiado de inputs",
    )
    assert_true(
        any("VPS_ANSWERS.local.json" in action for action in result["next_actions"]),
        "El semáforo debería enseñar también la ruta no interactiva con JSON local",
    )


def test_existing_answers_json_is_reported_and_prioritized():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-readiness-") as tmp:
        base = Path(tmp)
        answers = base / "VPS_ANSWERS.local.json"
        answers.write_text(
            '{\n  "Dominio/subdominio público": "diagnostico.example.com",\n  "Puerto SSH": "22"\n}\n',
            encoding="utf-8",
        )
        result = beta_readiness_status.readiness(
            base / "VPS_INPUTS.local.md",
            base / "MANUAL_PRODUCTION_TEST.local.md",
            base / ".env.generated",
            base / "privacy_config.json",
            answers,
        )
    assert_true(not result["ok"], result)
    assert_true(result["checks"]["answers_json"]["exists"], "Debería detectar la ficha JSON local")
    assert_true(result["checks"]["answers_json"]["empty_required"], "Debería listar campos obligatorios vacíos")
    assert_true(
        any("Rellena `VPS_ANSWERS.local.json`" in action for action in result["next_actions"]),
        "Si existe JSON local, debería priorizar rellenarlo",
    )


def test_complete_artifacts_are_ready_for_public_go_no_go():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-readiness-") as tmp:
        base = Path(tmp)
        inputs = base / "VPS_INPUTS.local.md"
        manual = base / "MANUAL_PRODUCTION_TEST.local.md"
        env = base / ".env.generated"
        privacy = base / "privacy_config.json"
        inputs.write_text(VALID_INPUTS, encoding="utf-8")
        manual.write_text(filled_doc(), encoding="utf-8")
        prepared = prepare_vps_launch_files.prepare(inputs, env, privacy)
        assert_true(prepared["ok"], prepared)
        result = beta_readiness_status.readiness(inputs, manual, env, privacy)
    assert_true(result["ok"], result)
    assert_true(result["status"] == "ready_for_public_go_no_go", result)
    assert_true(
        any("deploy/verify_vps.sh" in action and "PUBLIC_BETA=true" in action for action in result["next_actions"]),
        "El estado listo debería recomendar el verificador VPS público completo",
    )
    assert_true(
        any("MIC_OPTIONAL=true" in action for action in result["next_actions"]),
        "Debe explicar cómo lanzar si el micro queda fuera de la primera beta",
    )


def test_complete_answers_json_state_is_ok():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-readiness-") as tmp:
        answers = Path(tmp) / "VPS_ANSWERS.local.json"
        full = generate_vps_inputs.answers_template()
        for label in full:
            if not str(full[label]).strip():
                full[label] = "valor-validado"
        answers.write_text(json.dumps(full, ensure_ascii=False), encoding="utf-8")
        state = beta_readiness_status.answers_state(answers)
    assert_true(state["ok"], state)
    assert_true(state["filled_required"] == state["required_fields"], state)


if __name__ == "__main__":
    test_default_repo_is_blocked_on_launch_inputs()
    test_existing_answers_json_is_reported_and_prioritized()
    test_complete_artifacts_are_ready_for_public_go_no_go()
    test_complete_answers_json_state_is_ok()
    print("beta_readiness_status ok")
