#!/usr/bin/env python3
import argparse
import launch_go_no_go


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def args(**overrides):
    base = {
        "base": "https://diagnostico.example.com",
        "public_beta": True,
        "admin_password": "clave-real",
        "manual_production_tested": True,
        "crm_reviewed": True,
        "mic_required": True,
        "mic_tested": True,
        "with_browser": True,
        "with_transcription": True,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_public_beta_go():
    result = launch_go_no_go.evaluate(args(), {"ok": True, "steps": [], "command": "release"})
    assert_true(result["verdict"] == "GO", f"Debería permitir apertura: {result}")


def test_public_beta_blocks_localhost_and_manual_missing():
    result = launch_go_no_go.evaluate(
        args(base="http://localhost:8787", manual_production_tested=False, crm_reviewed=False, mic_tested=False),
        {"ok": True, "steps": [], "command": "release"},
    )
    assert_true(result["verdict"] == "NO_GO", "Localhost y pruebas manuales pendientes deberían bloquear beta pública")
    joined = "\n".join(result["blockers"])
    assert_true("HTTPS" in joined and "localhost" in joined and "prueba manual" in joined and "micro" in joined, joined)


def test_release_failure_blocks():
    result = launch_go_no_go.evaluate(
        args(),
        {"ok": False, "steps": [{"name": "privacy_beta", "ok": False, "output": "Privacidad final pendiente"}], "command": "release"},
    )
    assert_true(result["verdict"] == "NO_GO", "Un release_check fallido debe bloquear")
    assert_true("privacy_beta" in result["blockers"][0], result["blockers"])


if __name__ == "__main__":
    test_public_beta_go()
    test_public_beta_blocks_localhost_and_manual_missing()
    test_release_failure_blocks()
    print("launch_go_no_go ok")
