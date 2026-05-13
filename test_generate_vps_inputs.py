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


def test_fill_missing_answers_preserves_existing_values():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-wizard-") as tmp:
        answers = Path(tmp) / "VPS_ANSWERS.local.json"
        partial = generate_vps_inputs.answers_template()
        partial["Dominio/subdominio público"] = "diagnostico.example.com"
        answers.write_text(json.dumps(partial, ensure_ascii=False), encoding="utf-8")
        fill_values = answers_from_valid_inputs()
        fill_values["Dominio/subdominio público"] = "otro.example.com"
        result = generate_vps_inputs.fill_missing_answers(answers, fill_values)
        saved = json.loads(answers.read_text(encoding="utf-8"))
    assert_true(result["ok"], result)
    assert_true(saved["Dominio/subdominio público"] == "diagnostico.example.com", "No debería pisar valores ya rellenados")
    assert_true(saved["Contraseña real CRM"] == "clave-super-larga-2026", "Debería rellenar campos obligatorios vacíos")
    assert_true("Contraseña real CRM" in result["updated"], "Debería reportar campos actualizados")


def test_fill_missing_answers_reviews_blocking_values():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-vps-wizard-") as tmp:
        answers = Path(tmp) / "VPS_ANSWERS.local.json"
        full = answers_from_valid_inputs()
        full["Proveedor IA inicial"] = "codex"
        full["¿Codex CLI ya está logueado con ese usuario?"] = "no"
        full["Contraseña real CRM"] = "corta"
        answers.write_text(json.dumps(full, ensure_ascii=False), encoding="utf-8")
        provided = {
            "¿Codex CLI ya está logueado con ese usuario?": "sí",
            "Contraseña real CRM": "clave-super-larga-2026",
        }
        result = generate_vps_inputs.fill_missing_answers(answers, provided)
        saved = json.loads(answers.read_text(encoding="utf-8"))
    assert_true(result["ok"], result)
    assert_true(saved["¿Codex CLI ya está logueado con ese usuario?"] == "sí", "Debería actualizar decisiones bloqueantes")
    assert_true(saved["Contraseña real CRM"] == "clave-super-larga-2026", "Debería actualizar valores inválidos")
    assert_true("¿Codex CLI ya está logueado con ese usuario?" in result["updated"], "Debería reportar el campo revisado")


def test_deployment_handoff_uses_exact_json_keys():
    handoff = Path("NEXT_DEPLOYMENT_HANDOFF.md").read_text(encoding="utf-8")
    for label in [
        "Dominio/subdominio público",
        "IP del VPS",
        "Usuario SSH",
        "Contraseña real CRM",
        "Responsable legal",
        "NIF/CIF o razón social",
        "Email de contacto privacidad",
        "Proveedor VPS/hosting",
    ]:
        assert_true(f"`{label}`" in handoff, f"El handoff no contiene la clave exacta `{label}`")
    assert_true("no renombres las claves" in handoff, "El handoff debería advertir que no se renombren las claves JSON")
    assert_true("generate_vps_inputs.py --fill-missing-answers VPS_ANSWERS.local.json" in handoff, "El handoff debería incluir el asistente de campos pendientes")
    assert_true("copia `VPS_INPUTS.local.md` al VPS" in handoff, "El handoff debería priorizar la ficha local para el lanzador guiado")
    assert_true("python3 print_vps_deploy_commands.py --inputs VPS_INPUTS.local.md" in handoff, "El handoff debería incluir el generador de comandos")
    assert_true("deploy/launch_from_inputs.sh" in handoff, "El handoff debería nombrar el lanzador guiado")
    assert_true("deploy/install_vps.sh" in handoff, "El handoff debería reservar install_vps.sh para instalación manual")


if __name__ == "__main__":
    test_generate_valid_local_inputs()
    test_generate_refuses_overwrite_without_force()
    test_cli_with_answers_json_generates_file()
    test_answers_template_has_all_fields_and_defaults()
    test_fill_missing_answers_preserves_existing_values()
    test_fill_missing_answers_reviews_blocking_values()
    test_deployment_handoff_uses_exact_json_keys()
    print("generate_vps_inputs ok")
