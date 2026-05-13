#!/usr/bin/env python3
import tempfile
from pathlib import Path

import print_vps_deploy_commands
from test_vps_inputs_validator import VALID_INPUTS


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_deploy_commands_from_valid_inputs():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-commands-") as tmp:
        inputs = Path(tmp) / "VPS_INPUTS.local.md"
        inputs.write_text(VALID_INPUTS, encoding="utf-8")
        result = print_vps_deploy_commands.deploy_commands(inputs)
    assert_true(result["ok"], result)
    text = "\n".join(result["commands"])
    assert_true("deploy@203.0.113.10" in text, "Debería usar usuario/IP de la ficha")
    assert_true("scp -P 22" in text, "Debería incluir comando scp con puerto")
    assert_true("VPS_INPUTS.local.md" in text, "Debería copiar la ficha local al VPS")
    assert_true("deploy/launch_from_inputs.sh" in text, "Debería lanzar el instalador guiado")
    assert_true("DOMAIN=diagnostico.example.com" in text, "Debería pasar el dominio real al lanzador/verificador")
    assert_true("clave-super-larga-2026" not in text, "No debería imprimir la contraseña CRM en comandos")


def test_invalid_inputs_do_not_print_commands():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-commands-") as tmp:
        inputs = Path(tmp) / "VPS_INPUTS.local.md"
        inputs.write_text(VALID_INPUTS.replace("¿El dominio ya apunta al VPS?: sí", "¿El dominio ya apunta al VPS?: no"), encoding="utf-8")
        result = print_vps_deploy_commands.deploy_commands(inputs)
    assert_true(not result["ok"], "No debería generar comandos si la ficha no valida")
    assert_true(result["errors"], "Debería explicar errores de validación")
    assert_true("commands" not in result, "No debería devolver comandos con inputs inválidos")


if __name__ == "__main__":
    test_deploy_commands_from_valid_inputs()
    test_invalid_inputs_do_not_print_commands()
    print("print_vps_deploy_commands ok")
