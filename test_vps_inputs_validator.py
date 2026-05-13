#!/usr/bin/env python3
import tempfile
from pathlib import Path

import validate_vps_inputs


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


VALID_INPUTS = """# Inputs para desplegar en VPS

## Acceso y dominio

- Dominio/subdominio público: diagnostico.example.com
- IP del VPS: 203.0.113.10
- Usuario SSH: deploy
- Puerto SSH: 22
- Sistema operativo: Ubuntu 24.04
- ¿El dominio ya apunta al VPS?: sí
- Ruta de instalación: /opt/primer-empleado-ia

## IA y transcripción

- Proveedor IA inicial: codex
- Ruta de Codex CLI en VPS: /usr/local/bin/codex
- Usuario systemd que tendrá sesión Codex: primeria
- ¿Codex CLI ya está logueado con ese usuario?: sí
- ¿El micro entra en la primera beta?: no

## CRM y seguridad

- Usuario admin CRM: admin
- Contraseña real CRM: clave-super-larga-2026
- ¿Webhook externo desde el día 1?: no
- Destino webhook: Sin webhook externo
- URL webhook:
- Secreto webhook:
- ¿Enviar conversación completa al webhook?: no

## Privacidad

- Responsable legal: Pablo Tapias
- NIF/CIF o razón social: NIF 00000000X
- Email de contacto privacidad: privacidad@example.com
- Proveedor VPS/hosting: VPS europeo
- Proveedor IA: Codex en servidor
- Proveedor transcripción: Whisper local si se activa
- Proveedor email: Sin email automatizado inicial
- Destino CRM/webhook: SQLite local en VPS
- Plazo de conservación: 6 meses desde la última interacción
- ¿El diagnóstico suscribe automáticamente a newsletter?: No, solo consentimiento separado
"""


def write_tmp(text):
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False)
    handle.write(text)
    handle.close()
    return Path(handle.name)


def test_empty_template_fails():
    result = validate_vps_inputs.validate(validate_vps_inputs.DEFAULT_PATH)
    assert_true(not result["ok"], "La plantilla sin rellenar debería fallar")
    assert_true(result["errors"], "El validador debería explicar qué falta")
    assert_true(
        any("Proveedor IA inicial" in error for error in result["errors"]),
        "Los textos de ayuda no deberían contar como proveedor IA rellenado",
    )
    assert_true(
        any("¿El micro entra en la primera beta?" in error for error in result["errors"]),
        "Las opciones sí/no de ayuda no deberían contar como decisión de micro",
    )
    assert_true(
        any("Usuario admin CRM" in error for error in result["errors"]),
        "El valor por defecto documentado no debería contar como respuesta real",
    )


def test_valid_inputs_pass():
    path = write_tmp(VALID_INPUTS)
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(result["ok"], result)
    assert_true(result["filled_fields"] == result["required_fields"], "Debería contar todos los campos obligatorios")


def test_webhook_requires_url():
    path = write_tmp(VALID_INPUTS.replace("¿Webhook externo desde el día 1?: no", "¿Webhook externo desde el día 1?: sí"))
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(not result["ok"], "Webhook sí debería exigir URL")
    assert_true(any("URL webhook" in error for error in result["errors"]), result)


def test_codex_requires_logged_in_service_user():
    path = write_tmp(
        VALID_INPUTS.replace(
            "¿Codex CLI ya está logueado con ese usuario?: sí",
            "¿Codex CLI ya está logueado con ese usuario?: no",
        )
    )
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(not result["ok"], "Codex sin login del usuario systemd debería bloquear")
    assert_true(any("Codex CLI" in error for error in result["errors"]), result)


def test_domain_must_point_to_vps_for_https_launch():
    path = write_tmp(VALID_INPUTS.replace("¿El dominio ya apunta al VPS?: sí", "¿El dominio ya apunta al VPS?: no"))
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(not result["ok"], "DNS sin apuntar debería bloquear lanzamiento HTTPS")
    assert_true(any("dominio debe apuntar" in error for error in result["errors"]), result)


def test_yes_no_fields_reject_ambiguous_answers():
    path = write_tmp(VALID_INPUTS.replace("¿El micro entra en la primera beta?: no", "¿El micro entra en la primera beta?: quizá"))
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(not result["ok"], "Las decisiones sí/no no deberían aceptar respuestas ambiguas")
    assert_true(any("sí o no" in error for error in result["errors"]), result)


def test_env_values_reject_characters_that_break_systemd_env_files():
    path = write_tmp(VALID_INPUTS.replace("Contraseña real CRM: clave-super-larga-2026", "Contraseña real CRM: clave con espacios 2026"))
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(not result["ok"], "La contraseña con espacios debería bloquearse antes de generar .env")
    assert_true(any("compatible con .env/systemd" in error for error in result["errors"]), result)


def test_env_paths_must_be_absolute():
    path = write_tmp(VALID_INPUTS.replace("Ruta de Codex CLI en VPS: /usr/local/bin/codex", "Ruta de Codex CLI en VPS: codex"))
    try:
        result = validate_vps_inputs.validate(path)
    finally:
        path.unlink(missing_ok=True)
    assert_true(not result["ok"], "La ruta de Codex debería ser absoluta para systemd")
    assert_true(any("Ruta de Codex CLI" in error for error in result["errors"]), result)


if __name__ == "__main__":
    test_empty_template_fails()
    test_valid_inputs_pass()
    test_webhook_requires_url()
    test_codex_requires_logged_in_service_user()
    test_domain_must_point_to_vps_for_https_launch()
    test_yes_no_fields_reject_ambiguous_answers()
    test_env_values_reject_characters_that_break_systemd_env_files()
    test_env_paths_must_be_absolute()
    print("vps_inputs_validator ok")
