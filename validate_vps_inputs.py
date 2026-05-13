#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path


DEFAULT_PATH = Path(__file__).resolve().parent / "VPS_INPUTS.md"
PLACEHOLDER_MARKERS = {
    "",
    "por ejemplo `diagnostico.tuprimerempleadoia.com`.",
    "valor por defecto: `/opt/primer-empleado-ia`",
    "valor por defecto: `primeria`",
    "valor por defecto: `admin`",
    "make / n8n / zapier / airtable / hubspot / otro:",
    "recomendación beta: `6 meses desde la última interacción, salvo solicitud de supresión previa`.",
    "recomendación: `no; solo con consentimiento separado`.",
}
FORBIDDEN_TEXT = ["Completar", "Definir", "tu-dominio", "PASSWORD_REAL", "change-me"]
REQUIRED_LABELS = [
    "Dominio/subdominio público",
    "IP del VPS",
    "Usuario SSH",
    "Puerto SSH",
    "Sistema operativo",
    "¿El dominio ya apunta al VPS?",
    "Proveedor IA inicial",
    "Ruta de Codex CLI en VPS",
    "Usuario systemd que tendrá sesión Codex",
    "¿Codex CLI ya está logueado con ese usuario?",
    "¿El micro entra en la primera beta?",
    "Usuario admin CRM",
    "Contraseña real CRM",
    "¿Webhook externo desde el día 1?",
    "Responsable legal",
    "NIF/CIF o razón social",
    "Email de contacto privacidad",
    "Proveedor VPS/hosting",
    "Proveedor IA",
    "Proveedor transcripción",
    "Proveedor email",
    "Destino CRM/webhook",
    "Plazo de conservación",
    "¿El diagnóstico suscribe automáticamente a newsletter?",
]


def extract_fields(text: str) -> dict[str, str]:
    fields = {}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^- ([^:\n]+):\s*(.*)$", line)
        if not match:
            continue
        label = match.group(1).strip()
        value = match.group(2).strip()
        continuation = []
        cursor = index + 1
        while cursor < len(lines) and re.match(r"^\s+- ", lines[cursor]):
            continuation.append(lines[cursor].strip().removeprefix("- ").strip())
            cursor += 1
        if not value and continuation:
            value = " ".join(continuation)
        fields[label] = value
    return fields


def validate(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fields = extract_fields(text)
    errors = []
    warnings = []

    for label in REQUIRED_LABELS:
        value = fields.get(label, "").strip()
        if value.lower() in PLACEHOLDER_MARKERS or not value:
            errors.append(f"Falta rellenar: {label}")

    lowered = text.lower()
    for marker in FORBIDDEN_TEXT:
        if marker.lower() in lowered:
            errors.append(f"Queda marcador o placeholder: {marker}")

    domain = fields.get("Dominio/subdominio público", "")
    if domain and not re.search(r"^[a-z0-9.-]+\.[a-z]{2,}$", domain.lower()):
        errors.append("Dominio/subdominio público no parece un dominio válido")

    port = fields.get("Puerto SSH", "")
    if port and not port.isdigit():
        errors.append("Puerto SSH debe ser numérico")

    email = fields.get("Email de contacto privacidad", "")
    if email and not re.search(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Email de contacto privacidad no parece válido")

    admin_password = fields.get("Contraseña real CRM", "")
    if admin_password and len(admin_password) < 16:
        errors.append("Contraseña real CRM debería tener al menos 16 caracteres")

    ai_provider = fields.get("Proveedor IA inicial", "").lower()
    if ai_provider and all(option not in ai_provider for option in ["codex", "openai"]):
        warnings.append("Proveedor IA inicial no menciona codex ni openai")

    webhook_answer = fields.get("¿Webhook externo desde el día 1?", "").lower()
    webhook_url = fields.get("URL webhook", "").strip()
    if webhook_answer.startswith("s") and not webhook_url:
        errors.append("Has marcado webhook externo, pero falta URL webhook")

    mic_answer = fields.get("¿El micro entra en la primera beta?", "").lower()
    if mic_answer.startswith("s") and "whisper" not in text.lower():
        warnings.append("Micro activado: confirma rutas de ffmpeg y whisper en .env")

    return {
        "ok": not errors,
        "path": str(path),
        "errors": errors,
        "warnings": warnings,
        "filled_fields": len([label for label in REQUIRED_LABELS if fields.get(label, "").strip()]),
        "required_fields": len(REQUIRED_LABELS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida que VPS_INPUTS.md esté listo antes del despliegue")
    parser.add_argument("--path", default=str(DEFAULT_PATH))
    args = parser.parse_args()
    result = validate(Path(args.path))
    import json

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
