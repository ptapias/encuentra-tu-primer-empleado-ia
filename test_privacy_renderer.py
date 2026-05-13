#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import render_privacy


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


VALID_CONFIG = {
    "controller_name": "Pablo Tapias / Tu Primer Empleado IA",
    "controller_legal_id": "NIF 00000000X",
    "contact_email": "privacidad@example.com",
    "hosting_provider": "VPS propio en proveedor europeo",
    "ai_provider": "Codex/OpenAI ejecutado desde la cuenta configurada en el servidor",
    "transcription_provider": "Whisper local en el servidor, si se activa el micrófono",
    "crm_provider": "SQLite local en el VPS y CRM interno de la aplicación",
    "webhook_destination": "Sin webhook externo configurado",
    "email_provider": "Sin proveedor de email automatizado en la beta inicial",
    "retention_period": "6 meses desde la última interacción, salvo solicitud de supresión previa",
    "newsletter_use": "El diagnóstico no suscribe automáticamente a la newsletter salvo consentimiento separado.",
    "last_updated": "2026-05-13",
}


def test_placeholder_config_fails():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-privacy-") as tmp_dir:
        path = Path(tmp_dir) / "privacy_config.json"
        config = {**VALID_CONFIG, "controller_legal_id": "Completar NIF/CIF"}
        path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        try:
            render_privacy.load_config(path)
            raise AssertionError("La configuración con placeholders debería fallar")
        except SystemExit as exc:
            assert_true("placeholders" in str(exc), "El error debería explicar que hay placeholders")


def test_valid_config_renders_final_policy_without_beta_markers():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-privacy-") as tmp_dir:
        path = Path(tmp_dir) / "privacy_config.json"
        path.write_text(json.dumps(VALID_CONFIG, ensure_ascii=False), encoding="utf-8")
        cfg = render_privacy.load_config(path)
        markdown = render_privacy.render_markdown(cfg)
        html = render_privacy.render_html(cfg)

    forbidden = [
        "Completar",
        "Definir",
        "revisarse antes de publicación definitiva",
        "Antes de abrir tráfico público amplio",
        "política legal definitiva",
        "datos fiscales",
        "proveedores concretos",
    ]
    combined = markdown + "\n" + html
    for marker in forbidden:
        assert_true(marker.lower() not in combined.lower(), f"La política generada conserva marcador: {marker}")

    assert_true("privacidad@example.com" in markdown and "mailto:privacidad@example.com" in html, "Falta email de contacto")
    assert_true("6 meses desde la última interacción" in markdown, "Falta plazo de conservación")
    assert_true("No vendemos tus datos" in html, "Falta compromiso de no venta")


if __name__ == "__main__":
    test_placeholder_config_fails()
    test_valid_config_renders_final_policy_without_beta_markers()
    print("privacy_renderer ok")
