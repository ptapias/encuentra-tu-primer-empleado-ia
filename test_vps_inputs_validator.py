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


if __name__ == "__main__":
    test_empty_template_fails()
    test_valid_inputs_pass()
    test_webhook_requires_url()
    print("vps_inputs_validator ok")
