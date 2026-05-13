#!/usr/bin/env python3
import argparse
import shlex
from pathlib import Path

import validate_vps_inputs


def command_quote(value: str) -> str:
    return shlex.quote(str(value))


def deploy_commands(inputs_path: Path) -> dict:
    validation = validate_vps_inputs.validate(inputs_path)
    if not validation["ok"]:
        return {
            "ok": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "inputs": str(inputs_path),
        }
    fields = validate_vps_inputs.extract_fields(inputs_path.read_text(encoding="utf-8"))
    user = fields["Usuario SSH"]
    host = fields["IP del VPS"]
    port = fields.get("Puerto SSH", "22") or "22"
    domain = fields["Dominio/subdominio público"]
    app_dir = fields.get("Ruta de instalación", "/opt/primer-empleado-ia") or "/opt/primer-empleado-ia"
    remote = f"{user}@{host}"
    repo = "https://github.com/ptapias/encuentra-tu-primer-empleado-ia.git"
    commands = [
        f"ssh -p {command_quote(port)} {command_quote(remote)} {command_quote(f'sudo mkdir -p {app_dir} && sudo chown -R $USER:$USER {app_dir}')}",
        f"ssh -p {command_quote(port)} {command_quote(remote)} {command_quote(f'test -d {app_dir}/.git || git clone {repo} {app_dir}')}",
        f"scp -P {command_quote(port)} {command_quote(str(inputs_path))} {command_quote(f'{remote}:{app_dir}/VPS_INPUTS.local.md')}",
        f"ssh -p {command_quote(port)} {command_quote(remote)} {command_quote(f'cd {app_dir} && git pull --ff-only && sudo env DOMAIN={domain} ./deploy/launch_from_inputs.sh')}",
        f"ssh -p {command_quote(port)} {command_quote(remote)} {command_quote(f'cd {app_dir} && DOMAIN={domain} ./deploy/verify_vps.sh')}",
    ]
    return {
        "ok": True,
        "inputs": str(inputs_path),
        "domain": domain,
        "remote": remote,
        "app_dir": app_dir,
        "commands": commands,
        "warnings": validation["warnings"],
    }


def plain(result: dict) -> str:
    if not result["ok"]:
        lines = ["No puedo generar comandos: la ficha VPS no valida.", ""]
        for error in result.get("errors", []):
            lines.append(f"- {error}")
        return "\n".join(lines).rstrip() + "\n"
    lines = [
        "Comandos sugeridos para copiar la ficha al VPS y lanzar el instalador guiado:",
        "",
    ]
    for index, command in enumerate(result["commands"], start=1):
        lines.append(f"{index}. {command}")
    if result.get("warnings"):
        lines.append("")
        lines.append("Avisos:")
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Imprime comandos SSH/SCP para desplegar desde VPS_INPUTS.local.md")
    parser.add_argument("--inputs", default=str(validate_vps_inputs.DEFAULT_PATH))
    args = parser.parse_args()
    result = deploy_commands(Path(args.inputs))
    print(plain(result), end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
