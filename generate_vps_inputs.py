#!/usr/bin/env python3
import argparse
import getpass
import json
from pathlib import Path

import validate_vps_inputs


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "VPS_INPUTS.local.md"
DEFAULT_ANSWERS = ROOT / "VPS_ANSWERS.local.json"


FIELDS = [
    ("Acceso y dominio", "Dominio/subdominio público", "", "Ejemplo: diagnostico.tudominio.com"),
    ("Acceso y dominio", "IP del VPS", "", "IP pública del servidor"),
    ("Acceso y dominio", "Usuario SSH", "", "Usuario con el que entras al VPS"),
    ("Acceso y dominio", "Puerto SSH", "22", "Normalmente 22"),
    ("Acceso y dominio", "Sistema operativo", "Ubuntu 24.04", "Ejemplo: Ubuntu 24.04"),
    ("Acceso y dominio", "¿El dominio ya apunta al VPS?", "sí", "sí/no; debe ser sí antes de lanzar HTTPS"),
    ("Acceso y dominio", "Ruta de instalación", "/opt/primer-empleado-ia", "Mantén el valor por defecto salvo motivo claro"),
    ("IA y transcripción", "Proveedor IA inicial", "codex", "codex para beta controlada; openai para tráfico más estable"),
    ("IA y transcripción", "Ruta de Codex CLI en VPS", "/usr/local/bin/codex", "Ruta del binario codex en el VPS"),
    ("IA y transcripción", "Usuario systemd que tendrá sesión Codex", "primeria", "Usuario que ejecutará el servicio"),
    ("IA y transcripción", "¿Codex CLI ya está logueado con ese usuario?", "no", "sí/no; debe ser sí si usas codex"),
    ("IA y transcripción", "¿El micro entra en la primera beta?", "sí", "sí/no"),
    ("CRM y seguridad", "Usuario admin CRM", "admin", "Usuario para entrar al dashboard interno"),
    ("CRM y seguridad", "Contraseña real CRM", "", "Mínimo 16 caracteres; sin espacios, comillas, # ni barras invertidas"),
    ("CRM y seguridad", "¿Webhook externo desde el día 1?", "no", "sí/no"),
    ("CRM y seguridad", "Destino webhook", "Sin webhook externo inicial", "Make, n8n, Zapier, Airtable, HubSpot u otro"),
    ("CRM y seguridad", "URL webhook", "", "Déjalo vacío si no hay webhook desde el día 1"),
    ("CRM y seguridad", "Secreto webhook", "", "Déjalo vacío si no hay webhook; sin espacios, comillas, # ni barras invertidas"),
    ("CRM y seguridad", "¿Enviar conversación completa al webhook?", "no", "sí/no"),
    ("Privacidad", "Responsable legal", "", "Nombre o razón social responsable"),
    ("Privacidad", "NIF/CIF o razón social", "", "Dato legal que debe aparecer en privacidad"),
    ("Privacidad", "Email de contacto privacidad", "", "Email para derechos/privacidad"),
    ("Privacidad", "Proveedor VPS/hosting", "", "Proveedor donde alojas el VPS"),
    ("Privacidad", "Proveedor IA", "Codex CLI en servidor autenticado por el titular", "Proveedor usado para respuestas IA"),
    ("Privacidad", "Proveedor transcripción", "Whisper local en servidor si se activa micro", "Proveedor usado para transcribir audio"),
    ("Privacidad", "Proveedor email", "Sin proveedor email automatizado inicial", "Resend/Beehiiv/ConvertKit o sin email automático"),
    ("Privacidad", "Destino CRM/webhook", "SQLite local en VPS", "Destino externo si lo hay"),
    ("Privacidad", "Plazo de conservación", "6 meses desde la última interacción, salvo solicitud de supresión previa", "Plazo visible en privacidad"),
    ("Privacidad", "¿El diagnóstico suscribe automáticamente a newsletter?", "No; solo con consentimiento separado", "Recomendado: no"),
]


def load_answers(path: str) -> dict[str, str]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def answers_template() -> dict[str, str]:
    return {label: default for _section, label, default, _help_text in FIELDS}


def missing_answer_labels(answers: dict[str, str]) -> list[str]:
    return [label for label in validate_vps_inputs.REQUIRED_LABELS if not str(answers.get(label, "")).strip()]


def ask(label: str, default: str, help_text: str, *, secret: bool, answers: dict[str, str]) -> str:
    if label in answers:
        return str(answers[label]).strip()
    prompt = f"{label}"
    if default:
        prompt += f" [{default}]"
    if help_text:
        prompt += f" - {help_text}"
    prompt += ": "
    if secret:
        value = getpass.getpass(prompt).strip()
    else:
        value = input(prompt).strip()
    return value or default


def render(values: dict[str, str]) -> str:
    sections: dict[str, list[tuple[str, str]]] = {}
    for section, label, _default, _help in FIELDS:
        sections.setdefault(section, []).append((label, values.get(label, "")))

    lines = [
        "# Inputs para desplegar en VPS",
        "",
        "Archivo local generado para preparar el despliegue. No lo subas a Git.",
        "",
    ]
    for section, items in sections.items():
        lines.append(f"## {section}")
        lines.append("")
        for label, value in items:
            lines.append(f"- {label}: {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def fill_missing_answers(path: Path, provided: dict[str, str] | None = None, *, force: bool = False) -> dict:
    if path.exists():
        answers = json.loads(path.read_text(encoding="utf-8"))
    else:
        answers = answers_template()
    provided = provided or {}
    labels = {label: (default, help_text) for _section, label, default, help_text in FIELDS}
    missing = missing_answer_labels(answers)
    if not missing and not force:
        return {"ok": True, "path": str(path), "updated": [], "missing_required": []}
    updated = []
    for label in missing:
        default, help_text = labels.get(label, ("", ""))
        current = str(answers.get(label, "")).strip()
        if label in provided:
            value = str(provided[label]).strip()
        else:
            value = ask(
                label,
                current or default,
                help_text,
                secret=label in {"Contraseña real CRM", "Secreto webhook"},
                answers={},
            )
        if value:
            answers[label] = value
            updated.append(label)
    path.write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": not missing_answer_labels(answers),
        "path": str(path),
        "updated": updated,
        "missing_required": missing_answer_labels(answers),
        "next_actions": [
            f"python3 generate_vps_inputs.py --answers-json {path}",
            "python3 validate_vps_inputs.py --path VPS_INPUTS.local.md",
        ],
    }


def generate(output: Path, answers: dict[str, str], *, force: bool = False) -> dict:
    if output.exists() and not force:
        return {
            "ok": False,
            "error": f"Ya existe {output}. Usa --force si quieres sobrescribirlo.",
            "output": str(output),
        }
    values = {}
    for _section, label, default, help_text in FIELDS:
        values[label] = ask(
            label,
            default,
            help_text,
            secret=label in {"Contraseña real CRM", "Secreto webhook"},
            answers=answers,
        )
    output.write_text(render(values), encoding="utf-8")
    validation = validate_vps_inputs.validate(output)
    return {
        "ok": validation["ok"],
        "output": str(output),
        "validation": validation,
        "next_actions": [
            f"python3 validate_vps_inputs.py --path {output}",
            f"python3 prepare_vps_launch_files.py --inputs {output}",
            "sudo env DOMAIN=tu-dominio ./deploy/launch_from_inputs.sh",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera VPS_INPUTS.local.md de forma guiada y validable")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--answers-json", default="", help="Archivo JSON opcional para generar sin prompts, útil para tests")
    parser.add_argument("--print-answers-template", action="store_true", help="Imprime una plantilla JSON editable para usar con --answers-json")
    parser.add_argument("--fill-missing-answers", default="", help="Rellena interactivamente solo campos obligatorios vacíos del JSON indicado")
    parser.add_argument("--force", action="store_true", help="Sobrescribe el archivo de salida si ya existe")
    args = parser.parse_args()
    if args.print_answers_template:
        print(json.dumps(answers_template(), ensure_ascii=False, indent=2))
        return 0
    if args.fill_missing_answers:
        result = fill_missing_answers(Path(args.fill_missing_answers))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    result = generate(Path(args.output), load_answers(args.answers_json), force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
