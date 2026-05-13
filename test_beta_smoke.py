#!/usr/bin/env python3
import argparse
import base64
import json
import sys
import urllib.error
import urllib.request


def request(base, path, *, auth=None, method="GET", payload=None, timeout=30):
    headers = {}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
        method = "POST"
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    req = urllib.request.Request(base.rstrip("/") + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read().decode("utf-8", errors="replace")
        if "application/json" in content_type:
            return response.status, json.loads(raw)
        return response.status, raw


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description="Smoke test de beta para Encuentra Tu Primer Empleado IA")
    parser.add_argument("--base", default="http://localhost:8787", help="URL base, por ejemplo https://diagnostico.tu-dominio.com")
    parser.add_argument("--admin-user", default="")
    parser.add_argument("--admin-password", default="")
    args = parser.parse_args()
    auth = (args.admin_user, args.admin_password) if args.admin_user and args.admin_password else None

    checks = []

    status, health = request(args.base, "/healthz")
    expect(status == 200 and health.get("ok"), "healthz no responde correctamente")
    checks.append({"check": "health", "provider": health.get("provider"), "transcription": health.get("transcription")})

    status, capabilities = request(args.base, "/api/capabilities")
    expect(status == 200 and "transcription" in capabilities, "capabilities no devuelve estado de transcripción")
    checks.append({"check": "capabilities", "transcription": capabilities["transcription"].get("available")})

    status, public_html = request(args.base, "/Agente_Real_CRM.html")
    expect(status == 200, "la página pública no carga")
    expect("¿Dónde se te escapa tiempo, dinero o clientes?" in public_html, "falta el gancho principal en la página pública")
    expect("Descargar JSON" not in public_html and "informe potente" not in public_html.lower(), "la página pública contiene textos internos")
    checks.append({"check": "public_page", "ok": True})

    status, session = request(args.base, "/api/session", payload={})
    expect(status == 200 and session.get("lead_id"), "no se puede crear sesión pública")
    checks.append({"check": "session", "lead_id": session.get("lead_id")})

    try:
        status, metrics = request(args.base, "/api/metrics")
        metrics_without_auth = status
    except urllib.error.HTTPError as exc:
        metrics_without_auth = exc.code
        metrics = {}
    if auth:
        expect(metrics_without_auth == 401, "las métricas deberían estar protegidas sin autenticación")
        status, metrics = request(args.base, "/api/metrics", auth=auth)
        expect(status == 200 and "metrics" in metrics, "las métricas no responden con autenticación")
    else:
        expect(metrics_without_auth == 200 and "metrics" in metrics, "las métricas no responden en entorno sin auth")
    checks.append({"check": "metrics", "auth_required": bool(auth), "status_without_auth": metrics_without_auth})

    try:
        status, export_csv = request(args.base, "/api/export.csv")
        export_without_auth = status
    except urllib.error.HTTPError as exc:
        export_without_auth = exc.code
        export_csv = ""
    if auth:
        expect(export_without_auth == 401, "el export CSV debería estar protegido sin autenticación")
        status, export_csv = request(args.base, "/api/export.csv", auth=auth)
        expect(status == 200 and "email" in export_csv.splitlines()[0], "el export CSV no responde con autenticación")
    else:
        expect(export_without_auth == 200 and "email" in export_csv.splitlines()[0], "el export CSV no responde en entorno sin auth")
    checks.append({"check": "export_csv", "auth_required": bool(auth), "status_without_auth": export_without_auth})

    print(json.dumps({"ok": True, "base": args.base, "checks": checks}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
