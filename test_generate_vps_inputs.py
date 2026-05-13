#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import generate_vps_inputs
from test_vps_inputs_validator import VALID_INPUTS
import validate_vps_inputs


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def answers_from_valid_inputs() -> dict[str, str]:
    return validate_vps_inputs.extract_fields(VALID_INPUTS)


def test_generate_valid_local_inputs():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-wizard-") as tmp:
        output = Path(tmp) / "VPS_INPUTS.local.md"
        result = generate_vps_inputs.generate(output, answers_from_valid_inputs(), force=False)
        assert_true(result["ok"], result)
        assert_true(
            "sudo env DOMAIN=tu-dominio ./deploy/launch_from_inputs.sh" in result["next_actions"],
            "La siguiente acción debería conservar DOMAIN al ejecutar con sudo",
        )
        text = output.read_text(encoding="utf-8")
        assert_true("diagnostico.example.com" in text, "No escribió dominio")
        assert_true("clave-super-larga-2026" in text, "No escribió contraseña de prueba")
        assert_true(validate_vps_inputs.validate(output)["ok"], "El archivo generado no valida")


def test_generate_refuses_overwrite_without_force():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-wizard-") as tmp:
        output = Path(tmp) / "VPS_INPUTS.local.md"
        output.write_text("contenido existente\n", encoding="utf-8")
        result = generate_vps_inputs.generate(output, answers_from_valid_inputs(), force=False)
        assert_true(not result["ok"], "No debería sobrescribir sin --force")
        assert_true(output.read_text(encoding="utf-8") == "contenido existente\n", "Pisó archivo existente")


def test_cli_with_answers_json_generates_file():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-wizard-") as tmp:
        base = Path(tmp)
        answers = base / "answers.json"
        output = base / "VPS_INPUTS.local.md"
        answers.write_text(json.dumps(answers_from_valid_inputs(), ensure_ascii=False), encoding="utf-8")
        result = generate_vps_inputs.generate(output, json.loads(answers.read_text(encoding="utf-8")), force=True)
        assert_true(result["ok"], result)


def test_answers_template_has_all_fields_and_defaults():
    template = generate_vps_inputs.answers_template()
    labels = [label for _section, label, _default, _help in generate_vps_inputs.FIELDS]
    assert_true(set(template) == set(labels), "La plantilla JSON debería cubrir todas las preguntas")
    assert_true(template["Puerto SSH"] == "22", "La plantilla debería conservar defaults útiles")
    assert_true(template["Contraseña real CRM"] == "", "La plantilla no debería inventar contraseña")


if __name__ == "__main__":
    test_generate_valid_local_inputs()
    test_generate_refuses_overwrite_without_force()
    test_cli_with_answers_json_generates_file()
    test_answers_template_has_all_fields_and_defaults()
    print("generate_vps_inputs ok")
