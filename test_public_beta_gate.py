#!/usr/bin/env python3
import argparse

import release_check


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def args(**overrides):
    base = {
        "base": "https://diagnostico.example.com",
        "admin_user": "admin",
        "admin_password": "clave-real",
        "check_codex_live": True,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_public_gate_allows_valid_https_with_matching_password_and_codex_check():
    result = release_check.public_beta_gate(args(), {"ADMIN_PASSWORD": "clave-real", "AI_PROVIDER": "codex"})
    assert_true(result["ok"], f"Gate público debería pasar con HTTPS, auth y Codex live checked: {result}")


def test_public_gate_blocks_localhost_http_and_missing_codex_check():
    result = release_check.public_beta_gate(
        args(base="http://localhost:8787", admin_password="change-me", check_codex_live=False),
        {"ADMIN_PASSWORD": "otra-clave", "AI_PROVIDER": "codex"},
    )
    assert_true(not result["ok"], "Gate público no debería pasar en localhost/http")
    missing = set(result["missing"])
    expected = {
        "base_is_https",
        "base_is_not_localhost",
        "admin_credentials_supplied",
        "admin_password_matches_env",
        "codex_live_checked",
    }
    assert_true(expected.issubset(missing), f"Faltan bloqueos esperados: {missing}")


def test_public_gate_does_not_require_codex_live_when_provider_is_openai():
    result = release_check.public_beta_gate(
        args(check_codex_live=False),
        {"ADMIN_PASSWORD": "clave-real", "AI_PROVIDER": "openai"},
    )
    assert_true(result["ok"], f"OpenAI no debería exigir check live de Codex: {result}")


if __name__ == "__main__":
    test_public_gate_allows_valid_https_with_matching_password_and_codex_check()
    test_public_gate_blocks_localhost_http_and_missing_codex_check()
    test_public_gate_does_not_require_codex_live_when_provider_is_openai()
    print("public_beta_gate ok")
