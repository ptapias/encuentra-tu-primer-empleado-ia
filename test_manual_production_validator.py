#!/usr/bin/env python3
import tempfile
from pathlib import Path

import validate_manual_production_test


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def filled_doc(final="Abrir"):
    rows = "\n".join(
        f"| {label} | Esperado | OK | captura/log |"
        for label in validate_manual_production_test.CRITICAL_ROWS
    )
    return f"""# Prueba manual de producción

## Datos de la prueba

| Campo | Valor |
|---|---|
| Fecha | 2026-05-13 |
| Dominio probado | https://diagnostico.example.com |
| Commit `/healthz.version` | abc1234 |
| Tester | Pablo |
| Dispositivo | Escritorio |
| Navegador | Chrome |
| Origen/UTM usado | utm_source=test |

## Checks

| Check | Esperado | Resultado | Evidencia |
|---|---|---|---|
{rows}

## Notas y decisión

Resultado final: {final}

Notas:

- Prueba completa sin incidencias críticas.
"""


def test_template_fails():
    result = validate_manual_production_test.validate(validate_manual_production_test.TEMPLATE_PATH)
    assert_true(not result["ok"], "La plantilla vacía debería fallar")
    assert_true(result["errors"], "Debería explicar errores")


def test_filled_doc_passes():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-manual-test-") as tmp:
        path = Path(tmp) / "manual.md"
        path.write_text(filled_doc(), encoding="utf-8")
        result = validate_manual_production_test.validate(path)
    assert_true(result["ok"], result)


def test_template_tracks_core_product_promises():
    template = validate_manual_production_test.TEMPLATE_PATH.read_text(encoding="utf-8")
    for label in [
        "Discovery en vivo",
        "Discovery adaptativa",
        "Progreso lateral",
        "Latencia IA",
    ]:
        assert_true(label in template, f"La prueba manual debería cubrir `{label}`")
        assert_true(label in validate_manual_production_test.CRITICAL_ROWS, f"`{label}` debería ser crítico antes de abrir beta")


def test_no_go_final_blocks():
    with tempfile.TemporaryDirectory(prefix="primer-empleado-manual-test-") as tmp:
        path = Path(tmp) / "manual.md"
        path.write_text(filled_doc(final="No abrir"), encoding="utf-8")
        result = validate_manual_production_test.validate(path)
    assert_true(not result["ok"], "No abrir debería bloquear")


if __name__ == "__main__":
    test_template_fails()
    test_filled_doc_passes()
    test_template_tracks_core_product_promises()
    test_no_go_final_blocks()
    print("manual_production_validator ok")
