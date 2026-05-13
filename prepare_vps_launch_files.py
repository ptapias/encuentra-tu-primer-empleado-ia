#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import render_privacy
import validate_vps_inputs


ROOT = Path(__file__).resolve().parent


def value(fields: dict[str, str], key: str, default: str = "") -> str:
    return fields.get(key, "").strip() or default


def infer_ai_provider(text: str) -> str:
    lowered = text.lower()
    if "openai" in lowered:
        return "openai"
    return "codex"


def render_env(fields: dict[str, str]) -> str:
    ai_provider = infer_ai_provider(value(fields, "Proveedor IA inicial"))
    webhook_enabled = value(fields, "¿Webhook externo desde el día 1?").lower().startswith("s")
    mic_enabled = value(fields, "¿El micro entra en la primera beta?").lower().startswith("s")
    return "\n".join(
        [
            "HOST=127.0.0.1",
            "PORT=8787",
            f"AI_PROVIDER={ai_provider}",
            f"CODEX_BIN={value(fields, 'Ruta de Codex CLI en VPS', '/usr/local/bin/codex')}",
            "ALLOW_AI_FALLBACK=false",
            "APP_VERSION=",
            f"WHISPER_BIN={'/usr/local/bin/whisper' if mic_enabled else ''}",
            f"FFMPEG_BIN={'/usr/bin/ffmpeg' if mic_enabled else ''}",
            f"ADMIN_USER={value(fields, 'Usuario admin CRM', 'admin')}",
            f"ADMIN_PASSWORD={value(fields, 'Contraseña real CRM')}",
            f"CRM_WEBHOOK_URL={value(fields, 'URL webhook') if webhook_enabled else ''}",
            f"CRM_WEBHOOK_SECRET={value(fields, 'Secreto webhook') if webhook_enabled else ''}",
            "CRM_WEBHOOK_TIMEOUT=5",
            "MAX_PUBLIC_EVENTS_PER_HOUR=80",
            "MAX_MESSAGE_CHARS=3500",
            "MAX_USER_TURNS=14",
            "MAX_BODY_BYTES=1200000",
            "MAX_AI_CONCURRENCY=1",
            "AI_QUEUE_WAIT_SECONDS=8",
            "BETA_NOINDEX=true",
            "OPENAI_MODEL=gpt-4.1-mini",
            "OPENAI_API_KEY=",
            "",
        ]
    )


def privacy_config(fields: dict[str, str]) -> dict:
    return {
        "controller_name": value(fields, "Responsable legal"),
        "controller_legal_id": value(fields, "NIF/CIF o razón social"),
        "contact_email": value(fields, "Email de contacto privacidad"),
        "hosting_provider": value(fields, "Proveedor VPS/hosting"),
        "ai_provider": value(fields, "Proveedor IA"),
        "transcription_provider": value(fields, "Proveedor transcripción"),
        "crm_provider": "SQLite local en el VPS y CRM interno de la aplicación",
        "webhook_destination": value(fields, "Destino CRM/webhook"),
        "email_provider": value(fields, "Proveedor email"),
        "retention_period": value(fields, "Plazo de conservación"),
        "newsletter_use": value(fields, "¿El diagnóstico suscribe automáticamente a newsletter?"),
        "last_updated": "2026-05-13",
    }


def prepare(inputs_path: Path, env_output: Path, privacy_output: Path) -> dict:
    validation = validate_vps_inputs.validate(inputs_path)
    if not validation["ok"]:
        return {
            "ok": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "inputs": str(inputs_path),
        }
    fields = validate_vps_inputs.extract_fields(inputs_path.read_text(encoding="utf-8"))
    privacy = privacy_config(fields)
    # Reuse the privacy renderer validation so generated policy cannot keep placeholders.
    temp_config = privacy_output.with_suffix(".tmp.json")
    temp_config.write_text(json.dumps(privacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        render_privacy.load_config(temp_config)
    finally:
        temp_config.unlink(missing_ok=True)
    env_output.write_text(render_env(fields), encoding="utf-8")
    privacy_output.write_text(json.dumps(privacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "inputs": str(inputs_path),
        "env_output": str(env_output),
        "privacy_output": str(privacy_output),
        "warnings": validation["warnings"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera .env y privacy_config.json desde VPS_INPUTS.local.md")
    parser.add_argument("--inputs", default=str(validate_vps_inputs.DEFAULT_PATH))
    parser.add_argument("--env-output", default=str(ROOT / ".env.generated"))
    parser.add_argument("--privacy-output", default=str(ROOT / "privacy_config.json"))
    args = parser.parse_args()
    result = prepare(Path(args.inputs), Path(args.env_output), Path(args.privacy_output))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
