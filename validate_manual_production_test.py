#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "MANUAL_PRODUCTION_TEST.md"
LOCAL_PATH = ROOT / "MANUAL_PRODUCTION_TEST.local.md"
DEFAULT_PATH = LOCAL_PATH if LOCAL_PATH.exists() else TEMPLATE_PATH

REQUIRED_FIELDS = [
    "Fecha",
    "Dominio probado",
    "Commit `/healthz.version`",
    "Tester",
    "Dispositivo",
    "Navegador",
    "Origen/UTM usado",
]
CRITICAL_ROWS = [
    "`DOMAIN=... ./deploy/verify_vps.sh`",
    "/healthz",
    "CRM sin login",
    "CRM con login",
    "Privacidad",
    "Abrir landing",
    "Discovery en vivo",
    "Discovery adaptativa",
    "Progreso lateral",
    "Micrófono HTTPS",
    "Email-gate",
    "Informe",
    "Enlace privado",
    "CTA",
    "Feedback",
    "Lead nuevo",
    "Consentimiento",
    "Outcome",
    "Latencia IA",
    "CSV",
]


def table_value(text: str, label: str) -> str:
    pattern = rf"^\|\s*{re.escape(label)}\s*\|\s*(.*?)\s*\|$"
    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            return match.group(1).strip()
    return ""


def row_result(text: str, label: str) -> tuple[str, str]:
    pattern = rf"^\|\s*{re.escape(label)}\s*\|.*?\|\s*(.*?)\s*\|\s*(.*?)\s*\|$"
    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return "", ""


def validate(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    errors = []
    warnings = []
    for field in REQUIRED_FIELDS:
        value = table_value(text, field)
        if not value:
            errors.append(f"Falta rellenar dato de prueba: {field}")

    for row in CRITICAL_ROWS:
        result, evidence = row_result(text, row)
        if not result:
            errors.append(f"Falta resultado para: {row}")
        if result and result.lower() not in {"ok", "pasa", "sí", "si", "validado"}:
            errors.append(f"Resultado no OK para {row}: {result}")
        if not evidence:
            warnings.append(f"Sin evidencia adjunta para: {row}")

    final_match = re.search(r"Resultado final:\s*(.+)", text)
    final_value = final_match.group(1).strip().lower() if final_match else ""
    if final_value not in {"abrir", "go", "abrir beta", "abrir beta controlada"}:
        errors.append("Resultado final debe ser Abrir/GO para permitir beta")

    notes = text.split("Notas:", 1)[-1].strip() if "Notas:" in text else ""
    if notes in {"", "-"}:
        warnings.append("Añade una nota breve con el criterio de apertura")

    return {
        "ok": not errors,
        "path": str(path),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida la prueba manual de producción antes de abrir beta")
    parser.add_argument("--path", default=str(DEFAULT_PATH), help="Por defecto usa MANUAL_PRODUCTION_TEST.local.md si existe")
    args = parser.parse_args()
    result = validate(Path(args.path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
