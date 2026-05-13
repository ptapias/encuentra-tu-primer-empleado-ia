#!/usr/bin/env python3
import tempfile
from pathlib import Path

import beta_readiness_status
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


if __name__ == "__main__":
    test_default_repo_is_blocked_on_launch_inputs()
    test_complete_artifacts_are_ready_for_public_go_no_go()
    print("beta_readiness_status ok")
