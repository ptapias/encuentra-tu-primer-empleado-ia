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


def request_raw(base, path, *, auth=None, timeout=30):
    headers = {}
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    req = urllib.request.Request(base.rstrip("/") + path, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")


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
    beta_noindex = bool(health.get("beta_noindex", True))
    checks.append({"check": "health", "provider": health.get("provider"), "transcription": health.get("transcription"), "beta_noindex": beta_noindex})

    status, robots_headers, robots = request_raw(args.base, "/robots.txt")
    expect(status == 200 and "User-agent: *" in robots, "robots.txt no responde correctamente")
    if beta_noindex:
        expect("Disallow: /" in robots, "robots.txt debería bloquear indexación en beta")
        expect("noindex" in robots_headers.get("X-Robots-Tag", ""), "falta X-Robots-Tag en robots.txt")
    checks.append({"check": "robots", "noindex": beta_noindex})

    status, capabilities = request(args.base, "/api/capabilities")
    expect(status == 200 and "transcription" in capabilities, "capabilities no devuelve estado de transcripción")
    checks.append({"check": "capabilities", "transcription": capabilities["transcription"].get("available")})

    status, public_headers, public_html = request_raw(args.base, "/Agente_Real_CRM.html")
    expect(status == 200, "la página pública no carga")
    if beta_noindex:
        expect("noindex" in public_headers.get("X-Robots-Tag", ""), "falta X-Robots-Tag en página pública")
    expect("¿Dónde se te escapa tiempo, dinero o clientes?" in public_html, "falta el gancho principal en la página pública")
    expect("Por qué esta va primero" in public_html, "el informe no incluye explicación de prioridad")
    expect("Cómo funcionaría en la práctica" in public_html, "el informe no incluye flujo práctico")
    expect("Descargar JSON" not in public_html and "informe potente" not in public_html.lower(), "la página pública contiene textos internos")
    checks.append({"check": "public_page", "ok": True})

    blocked_static = ["/.env", "/crm.sqlite3", "/crm_leads.jsonl", "/app_server.py", "/backup_crm.py", "/backups/"]
    blocked_statuses = {}
    for path in blocked_static:
        try:
            request(args.base, path)
            blocked_statuses[path] = 200
        except urllib.error.HTTPError as exc:
            blocked_statuses[path] = exc.code
    expect(all(status == 404 for status in blocked_statuses.values()), f"archivos sensibles expuestos: {blocked_statuses}")
    checks.append({"check": "sensitive_static_files", "statuses": blocked_statuses})

    status, session = request(args.base, "/api/session", payload={})
    expect(status == 200 and session.get("lead_id"), "no se puede crear sesión pública")
    checks.append({"check": "session", "lead_id": session.get("lead_id")})

    status, delete_session = request(args.base, "/api/session", payload={})
    expect(status == 200 and delete_session.get("lead_id"), "no se puede crear sesión de borrado")

    update_payload = {
        "lead_id": session["lead_id"],
        "status": "send_resource",
        "offer": "resource",
        "notes": "smoke test",
    }
    try:
        status, lead_update = request(args.base, "/api/lead/update", payload=update_payload)
        update_without_auth = status
    except urllib.error.HTTPError as exc:
        update_without_auth = exc.code
        lead_update = {}
    if auth:
        expect(update_without_auth == 401, "la edición de lead debería estar protegida sin autenticación")
        status, lead_update = request(args.base, "/api/lead/update", auth=auth, payload=update_payload)
        expect(status == 200 and lead_update.get("lead", {}).get("status") == "send_resource", "la edición de lead no responde con autenticación")
    else:
        expect(update_without_auth == 200 and lead_update.get("lead", {}).get("status") == "send_resource", "la edición de lead no responde en entorno sin auth")
    checks.append({"check": "lead_update", "auth_required": bool(auth), "status_without_auth": update_without_auth})

    try:
        status, legacy_crm = request(args.base, "/crm", payload={"event": "smoke_legacy_crm", "lead_id": session["lead_id"]})
        legacy_crm_without_auth = status
    except urllib.error.HTTPError as exc:
        legacy_crm_without_auth = exc.code
        legacy_crm = {}
    if auth:
        expect(legacy_crm_without_auth == 401, "el endpoint legacy /crm debería estar protegido sin autenticación")
        status, legacy_crm = request(args.base, "/crm", auth=auth, payload={"event": "smoke_legacy_crm", "lead_id": session["lead_id"]})
        expect(status == 200 and legacy_crm.get("ok"), "el endpoint legacy /crm no responde con autenticación")
    else:
        expect(legacy_crm_without_auth == 200 and legacy_crm.get("ok"), "el endpoint legacy /crm no responde en entorno sin auth")
    checks.append({"check": "legacy_crm", "auth_required": bool(auth), "status_without_auth": legacy_crm_without_auth})

    delete_payload = {"lead_id": delete_session["lead_id"], "confirm": "delete"}
    try:
        status, deleted = request(args.base, "/api/lead/delete", payload=delete_payload)
        delete_without_auth = status
    except urllib.error.HTTPError as exc:
        delete_without_auth = exc.code
        deleted = {}
    if auth:
        expect(delete_without_auth == 401, "el borrado de lead debería estar protegido sin autenticación")
        status, deleted = request(args.base, "/api/lead/delete", auth=auth, payload=delete_payload)
        expect(status == 200 and deleted.get("deleted") == delete_session["lead_id"], "el borrado de lead no responde con autenticación")
        try:
            request(args.base, f"/api/lead?id={delete_session['lead_id']}", auth=auth)
            raise AssertionError("el lead borrado sigue disponible")
        except urllib.error.HTTPError as exc:
            expect(exc.code == 404, "el lead borrado debería devolver 404")
    else:
        expect(delete_without_auth == 200 and deleted.get("deleted") == delete_session["lead_id"], "el borrado de lead no responde en entorno sin auth")
        try:
            request(args.base, f"/api/lead?id={delete_session['lead_id']}")
            raise AssertionError("el lead borrado sigue disponible")
        except urllib.error.HTTPError as exc:
            expect(exc.code == 404, "el lead borrado debería devolver 404")
    checks.append({"check": "lead_delete", "auth_required": bool(auth), "status_without_auth": delete_without_auth})

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
