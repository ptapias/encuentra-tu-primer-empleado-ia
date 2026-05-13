#!/usr/bin/env python3
import app_server


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_rate_limit_blocks_after_limit():
    app_server.RATE_BUCKETS.clear()
    key = "test:rate-limit"
    assert_true(app_server.rate_limited(key, 2, window_seconds=3600) is False, "Primera petición no debería bloquear")
    assert_true(app_server.rate_limited(key, 2, window_seconds=3600) is False, "Segunda petición no debería bloquear")
    assert_true(app_server.rate_limited(key, 2, window_seconds=3600) is True, "Tercera petición debería bloquear")


def test_valid_email_rejects_bad_values():
    assert_true(app_server.valid_email("persona@empresa.com"), "Email normal debería ser válido")
    assert_true(not app_server.valid_email("persona"), "Email sin dominio debería fallar")
    assert_true(not app_server.valid_email("persona@empresa"), "Email sin TLD debería fallar")


if __name__ == "__main__":
    test_rate_limit_blocks_after_limit()
    test_valid_email_rejects_bad_values()
    print("server_guards ok")
