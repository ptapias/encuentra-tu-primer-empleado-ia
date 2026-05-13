#!/usr/bin/env python3
import app_server
import json


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeHandler:
    def __init__(self, peer_ip, forwarded=""):
        self.client_address = (peer_ip, 12345)
        self.headers = {"X-Forwarded-For": forwarded} if forwarded else {}


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


def test_admin_example_password_is_misconfigured():
    original = app_server.ADMIN_PASSWORD
    try:
        app_server.ADMIN_PASSWORD = "change-me"
        assert_true(app_server.admin_auth_misconfigured(), "La contraseña de ejemplo debería marcarse como mala configuración")
        app_server.ADMIN_PASSWORD = "clave-real"
        assert_true(not app_server.admin_auth_misconfigured(), "Una contraseña real no debería marcarse como mala configuración")
    finally:
        app_server.ADMIN_PASSWORD = original


def test_admin_without_password_only_allowed_on_local_host():
    assert_true(app_server.local_host_header("localhost:8787"), "localhost debería permitir CRM sin contraseña en desarrollo")
    assert_true(app_server.local_host_header("127.0.0.1:8787"), "127.0.0.1 debería permitir CRM sin contraseña en desarrollo")
    assert_true(app_server.local_host_header("[::1]:8787"), "::1 debería permitir CRM sin contraseña en desarrollo")
    assert_true(not app_server.local_host_header("diagnostico.example.com"), "un dominio público no debería permitir CRM sin contraseña")
    assert_true(not app_server.local_host_header("203.0.113.10:8787"), "una IP pública no debería permitir CRM sin contraseña")


def test_client_ip_only_trusts_proxy_header_from_loopback():
    assert_true(
        app_server.client_ip(FakeHandler("127.0.0.1", "203.0.113.25, 127.0.0.1")) == "203.0.113.25",
        "Debería respetar X-Forwarded-For cuando la petición viene del proxy local",
    )
    assert_true(
        app_server.client_ip(FakeHandler("198.51.100.9", "203.0.113.25")) == "198.51.100.9",
        "No debería aceptar X-Forwarded-For falsificado desde una conexión directa",
    )


def test_crm_webhook_payload_and_secret_header():
    original_url = app_server.CRM_WEBHOOK_URL
    original_secret = app_server.CRM_WEBHOOK_SECRET
    original_urlopen = app_server.request.urlopen
    calls = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(req, timeout):
        calls.append({"req": req, "timeout": timeout})
        return FakeResponse()

    try:
        app_server.CRM_WEBHOOK_URL = ""
        assert_true(not app_server.send_crm_webhook("report_generated", "lead-1", {"ok": True}), "Sin URL no debería enviar webhook")

        app_server.CRM_WEBHOOK_URL = "https://example.com/webhook"
        app_server.CRM_WEBHOOK_SECRET = "secreto"
        app_server.request.urlopen = fake_urlopen
        assert_true(app_server.send_crm_webhook("report_generated", "lead-1", {"ok": True}), "Webhook configurado debería enviarse")
        sent = calls[0]["req"]
        body = json.loads(sent.data.decode("utf-8"))
        assert_true(body["event"] == "report_generated" and body["lead_id"] == "lead-1", "Payload de webhook incompleto")
        assert_true(sent.headers.get("X-crm-webhook-secret") == "secreto", "Falta cabecera de secreto del webhook")
    finally:
        app_server.CRM_WEBHOOK_URL = original_url
        app_server.CRM_WEBHOOK_SECRET = original_secret
        app_server.request.urlopen = original_urlopen


if __name__ == "__main__":
    test_rate_limit_blocks_after_limit()
    test_valid_email_rejects_bad_values()
    test_admin_example_password_is_misconfigured()
    test_admin_without_password_only_allowed_on_local_host()
    test_client_ip_only_trusts_proxy_header_from_loopback()
    test_crm_webhook_payload_and_secret_header()
    print("server_guards ok")
