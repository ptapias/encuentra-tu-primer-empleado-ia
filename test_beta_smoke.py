#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


NO_REDIRECT_OPENER = urllib.request.build_opener(NoRedirect)
SMOKE_IP = f"198.51.{os.getpid() % 250}.{int(time.time() * 1000) % 250 + 1}"


def request(base, path, *, auth=None, method="GET", payload=None, timeout=30):
    headers = {"X-Forwarded-For": SMOKE_IP}
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


def request_no_redirect(base, path, *, method="GET", timeout=30):
    req = urllib.request.Request(base.rstrip("/") + path, headers={"X-Forwarded-For": SMOKE_IP}, method=method)
    try:
        with NO_REDIRECT_OPENER.open(req, timeout=timeout) as response:
            return response.status, dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers)


def request_raw(base, path, *, auth=None, timeout=30):
    headers = {"X-Forwarded-For": SMOKE_IP}
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    req = urllib.request.Request(base.rstrip("/") + path, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")


def request_bad_json_status(base, path, *, timeout=30):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=b"{mal json",
        headers={"X-Forwarded-For": SMOKE_IP, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description="Smoke test de beta para Encuentra Tu Primer Empleado IA")
    parser.add_argument("--base", default="http://localhost:8787", help="URL base, por ejemplo https://diagnostico.tu-dominio.com")
    parser.add_argument("--admin-user", default="")
    parser.add_argument("--admin-password", default="")
    parser.add_argument("--expected-version", default="", help="Versión esperada en /healthz para detectar servicios sin reiniciar")
    args = parser.parse_args()
    auth = (args.admin_user, args.admin_password) if args.admin_user and args.admin_password else None

    checks = []

    status, root_headers = request_no_redirect(args.base, "/", method="HEAD")
    expect(status == 302 and root_headers.get("Location") == "/Agente_Real_CRM.html", "HEAD / debería redirigir al diagnóstico")
    status, root_utm_headers = request_no_redirect(args.base, "/?utm_source=youtube&utm_campaign=whatsapp_ia&video=agente-whatsapp", method="GET")
    expect(
        status == 302 and root_utm_headers.get("Location") == "/Agente_Real_CRM.html?utm_source=youtube&utm_campaign=whatsapp_ia&video=agente-whatsapp",
        "GET / debería conservar UTMs al redirigir al diagnóstico",
    )
    favicon_status, _favicon_headers = request_no_redirect(args.base, "/favicon.ico", method="GET")
    expect(favicon_status == 204, "favicon.ico no debería generar ruido 404 en navegador")
    checks.append({"check": "root_redirect", "status": status, "keeps_utm": True, "favicon": favicon_status})

    status, health = request(args.base, "/healthz")
    expect(status == 200 and health.get("ok"), "healthz no responde correctamente")
    expect(bool(health.get("version")), "healthz debería exponer la versión/commit desplegado")
    if args.expected_version:
        expect(
            str(health.get("version")) == args.expected_version,
            f"/healthz.version={health.get('version')} no coincide con la versión esperada {args.expected_version}; reinicia el servicio o revisa el deploy",
        )
    beta_noindex = bool(health.get("beta_noindex", True))
    checks.append({"check": "health", "provider": health.get("provider"), "transcription": health.get("transcription"), "beta_noindex": beta_noindex, "version": health.get("version")})

    status, robots_headers, robots = request_raw(args.base, "/robots.txt")
    expect(status == 200 and "User-agent: *" in robots, "robots.txt no responde correctamente")
    if beta_noindex:
        expect("Disallow: /" in robots, "robots.txt debería bloquear indexación en beta")
        expect("noindex" in robots_headers.get("X-Robots-Tag", ""), "falta X-Robots-Tag en robots.txt")
    checks.append({"check": "robots", "noindex": beta_noindex})

    status, capabilities = request(args.base, "/api/capabilities")
    expect(status == 200 and "transcription" in capabilities, "capabilities no devuelve estado de transcripción")
    checks.append({"check": "capabilities", "transcription": capabilities["transcription"].get("available")})

    try:
        request(args.base, "/transcribe", method="POST", payload=None)
        empty_transcribe_status = 200
    except urllib.error.HTTPError as exc:
        empty_transcribe_status = exc.code
    expect(empty_transcribe_status == 400, "transcribe debería rechazar audio vacío con 400")
    checks.append({"check": "transcribe_empty_audio", "status": empty_transcribe_status})

    status, public_headers, public_html = request_raw(args.base, "/Agente_Real_CRM.html")
    expect(status == 200, "la página pública no carga")
    if beta_noindex:
        expect("noindex" in public_headers.get("X-Robots-Tag", ""), "falta X-Robots-Tag en página pública")
    expect("¿Dónde se te escapa tiempo, dinero o clientes?" in public_html, "falta el gancho principal en la página pública")
    expect("Discovery gratuito · 7-10 min" in public_html, "falta el posicionamiento de discovery consultiva")
    expect("Discovery gratuito" in public_html and "mini sesión consultiva" in public_html, "el lateral no refuerza el posicionamiento consultivo")
    # Tras el redesign editorial dark, validamos los nuevos elementos del HTML público.
    expect("escucha, repregunta y separa" in public_html, "el hero del agente no comunica la promesa consultiva")
    expect("Empezar conversación" in public_html, "el CTA principal no aparece o cambió de copy")
    expect("Cuéntame una escena" in public_html, "falta el primer beat del progreso narrativo en el hero")
    expect("Yo extraigo el patrón" in public_html, "falta el segundo beat del progreso narrativo")
    expect("Te entrego un plan" in public_html, "falta el tercer beat del progreso narrativo")
    expect("Qué recibirás" in public_html, "el lateral no anticipa los entregables")
    expect("Fugas detectadas" in public_html, "el lateral no menciona fugas detectadas")
    expect("Primer empleado IA recomendado" in public_html, "el lateral no anuncia el empleado IA recomendado")
    expect("Plan de 7 días" in public_html, "el lateral no anuncia el plan de 7 días")
    # Estructura editorial / branding
    expect("IA AL DÍA" in public_html, "falta la marca IA al Día en header / footer")
    expect("phaseLine" in public_html and "phaseCounter" in public_html, "falta la línea de 4 fases (top frame + footer counter)")
    # Composer y chat
    expect('id="composer"' in public_html and 'id="sendBtn"' in public_html, "el composer del chat no expone los IDs esperados")
    # Privacidad / consent
    expect("BETA_NOINDEX" not in public_html, "fugas de variables internas en el HTML público")
    expect("sales_intelligence" not in public_html, "la página pública expone términos internos de ventas")
    expect("/PRIVACY_BETA.html" in public_html, "la página pública no enlaza a la privacidad HTML")
    expect("Descargar JSON" not in public_html and "informe potente" not in public_html.lower(), "la página pública contiene textos internos")
    checks.append({"check": "public_page", "ok": True})

    status, dashboard_headers, dashboard_html = request_raw(args.base, "/CRM_Dashboard.html", auth=auth)
    expect(status == 200 and "offerFilter" in dashboard_html and "sourceFilter" in dashboard_html, "el CRM no incluye filtros operativos")
    expect("Consentimiento" in dashboard_html, "el CRM no muestra consentimiento del lead")
    expect("Interés CTA" in dashboard_html, "el CRM no muestra intención de CTA")
    expect("Discovery útil" in dashboard_html and "Listos informe" in dashboard_html, "el CRM no muestra métricas del embudo de discovery")
    expect("Email final" in dashboard_html and "de emails" in dashboard_html, "el CRM no muestra conversión del email-gate final")
    expect("Resumen de acción" in dashboard_html and "Fuga principal" in dashboard_html, "el CRM no muestra resumen accionable del diagnóstico")
    expect("Discovery viva" in dashboard_html and "Procesos candidatos" in dashboard_html, "el CRM no muestra discovery viva ni procesos candidatos")
    expect("Informe privado" in dashboard_html and "Abrir informe privado" in dashboard_html, "el CRM no muestra acceso al enlace privado del informe")
    checks.append({"check": "dashboard_filters", "ok": True})

    status, privacy_headers, privacy_html = request_raw(args.base, "/PRIVACY_BETA.html")
    expect(status == 200 and "Cómo usamos tus datos" in privacy_html, "la página de privacidad no carga")
    expect("Completar razón social" not in privacy_html and "Contacto | Completar" not in privacy_html, "la privacidad pública contiene placeholders internos")
    if beta_noindex:
        expect("noindex" in privacy_headers.get("X-Robots-Tag", ""), "falta X-Robots-Tag en privacidad")
    checks.append({"check": "privacy_page", "ok": True})

    blocked_static = [
        "/.env",
        "/crm.sqlite3",
        "/crm_leads.jsonl",
        "/app_server.py",
        "/backup_crm.py",
        "/backups/",
        "/README.md",
        "/DEPLOYMENT_VPS.md",
        "/FIRST_TESTERS_PACKET.md",
        "/BETA_TEST_PLAN.md",
        "/COMPLETION_AUDIT.md",
        "/PRIVACY_BETA.md",
        "/Prototipo_Conversacional.html",
        "/Sistema_Completo.md",
    ]
    blocked_statuses = {}
    for path in blocked_static:
        try:
            request(args.base, path)
            blocked_statuses[path] = 200
        except urllib.error.HTTPError as exc:
            blocked_statuses[path] = exc.code
    expect(all(status == 404 for status in blocked_statuses.values()), f"archivos sensibles expuestos: {blocked_statuses}")
    checks.append({"check": "sensitive_static_files", "statuses": blocked_statuses})

    attribution = {
        "source": "youtube",
        "medium": "video",
        "campaign": "whatsapp_ia",
        "video": "agente-whatsapp",
        "landing_path": "/Agente_Real_CRM.html",
    }
    status, session = request(args.base, "/api/session", payload={"attribution": attribution})
    expect(status == 200 and session.get("lead_id"), "no se puede crear sesión pública")
    expect(session.get("facts", {}).get("attribution", {}).get("source") == "youtube", "no se guarda la atribución inicial")
    checks.append({"check": "session", "lead_id": session.get("lead_id")})

    bad_json_status = request_bad_json_status(args.base, "/api/session")
    expect(bad_json_status == 400, f"JSON inválido debería devolver 400, no {bad_json_status}")
    checks.append({"check": "bad_json_handling", "status": bad_json_status})

    missing_lead_statuses = {}
    for endpoint, payload in {
        "/api/chat": {"lead_id": "missing-lead", "message": "hola"},
        "/api/email": {"lead_id": "missing-lead", "email": "smoke@example.com", "consent": True},
        "/api/report": {"lead_id": "missing-lead"},
        "/api/cta": {"lead_id": "missing-lead", "segment": "cohort"},
        "/api/feedback": {"lead_id": "missing-lead", "feedback": {"rating": 5}},
    }.items():
        try:
            request(args.base, endpoint, payload=payload, timeout=5)
            missing_lead_statuses[endpoint] = 200
        except urllib.error.HTTPError as exc:
            missing_lead_statuses[endpoint] = exc.code
    expect(all(status == 404 for status in missing_lead_statuses.values()), f"lead inexistente debería devolver 404: {missing_lead_statuses}")
    checks.append({"check": "missing_lead_handling", "statuses": missing_lead_statuses})

    try:
        request(args.base, "/api/email", payload={"lead_id": session["lead_id"], "email": "smoke@example.com"})
        email_without_consent = 200
    except urllib.error.HTTPError as exc:
        email_without_consent = exc.code
    expect(email_without_consent == 400, "el email-gate debería exigir consentimiento explícito")
    try:
        request(args.base, "/api/report", payload={"lead_id": session["lead_id"]}, timeout=5)
        report_without_consent = 200
    except urllib.error.HTTPError as exc:
        report_without_consent = exc.code
    expect(report_without_consent == 400, "el informe no debería generarse sin email y consentimiento")
    try:
        request(args.base, "/api/cta", payload={"lead_id": session["lead_id"], "segment": "cohort"})
        cta_without_consent = 200
    except urllib.error.HTTPError as exc:
        cta_without_consent = exc.code
    expect(cta_without_consent == 400, "el CTA no debería guardarse sin email y consentimiento")
    try:
        request(args.base, "/api/feedback", payload={"lead_id": session["lead_id"], "feedback": {"rating": 5}})
        feedback_without_consent = 200
    except urllib.error.HTTPError as exc:
        feedback_without_consent = exc.code
    expect(feedback_without_consent == 400, "el feedback no debería guardarse sin email y consentimiento")
    status, email_saved = request(
        args.base,
        "/api/email",
        payload={"lead_id": session["lead_id"], "email": "smoke@example.com", "consent": True, "privacy_version": "smoke"},
    )
    expect(status == 200 and email_saved.get("email") == "smoke@example.com", "no se guarda email con consentimiento")
    checks.append({"check": "email_consent", "ok": True})

    try:
        request(args.base, "/api/report", payload={"lead_id": session["lead_id"]}, timeout=5)
        report_without_discovery = 200
    except urllib.error.HTTPError as exc:
        report_without_discovery = exc.code
    expect(report_without_discovery == 409, "el informe no debería generarse sin discovery suficiente aunque ya haya email")
    checks.append({"check": "report_quality_gate", "status": report_without_discovery})

    status, cta_saved = request(args.base, "/api/cta", payload={"lead_id": session["lead_id"], "segment": "cohort", "source": "smoke"})
    expect(status == 200 and cta_saved.get("cta_interest", {}).get("segment") == "cohort", "no se guarda intención de CTA")
    checks.append({"check": "cta_interest", "ok": True})

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

    feedback_payload = {
        "lead_id": session["lead_id"],
        "feedback": {
            "rating": 4,
            "liked": "Prioridad clara",
            "missing": "Costes estimados",
            "improve": "Más ejemplos por sector",
            "text": "Prioridad clara\n\nCostes estimados\n\nMás ejemplos por sector",
        },
    }
    status, feedback_saved = request(args.base, "/api/feedback", payload=feedback_payload)
    expect(status == 200 and feedback_saved.get("ok"), "no se puede guardar feedback estructurado")
    lead_auth = auth if auth else None
    status, lead_detail = request(args.base, f"/api/lead?id={session['lead_id']}", auth=lead_auth)
    saved_feedback = lead_detail.get("lead", {}).get("feedback", {})
    expect(saved_feedback.get("rating") == 4 and saved_feedback.get("missing") == "Costes estimados", "el feedback estructurado no queda guardado en CRM")
    expect(lead_detail.get("lead", {}).get("facts", {}).get("attribution", {}).get("campaign") == "whatsapp_ia", "la atribución no queda disponible en CRM")
    expect(lead_detail.get("lead", {}).get("facts", {}).get("consent", {}).get("accepted") is True, "el consentimiento no queda guardado en CRM")
    expect(lead_detail.get("lead", {}).get("facts", {}).get("cta_interest", {}).get("segment") == "cohort", "la intención de CTA no queda guardada en CRM")
    checks.append({"check": "structured_feedback", "ok": True})

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
    expect(any(item.get("name") == "youtube" for item in metrics["metrics"].get("top_sources", [])), "las métricas no agregan origen de lead")
    expect(metrics["metrics"].get("consent_captured", 0) >= 1, "las métricas no cuentan consentimiento")
    expect(metrics["metrics"].get("cta_interest", 0) >= 1, "las métricas no cuentan interés de CTA")
    expect("operational_status" in metrics["metrics"] and "ai_errors" in metrics["metrics"], "las métricas no exponen salud operativa de IA")
    expect("webhook_errors" in metrics["metrics"], "las métricas no exponen errores de webhook")
    expect("recent_operational_events" in metrics["metrics"], "las métricas no exponen incidencias operativas recientes")
    expect("avg_chat_latency_seconds" in metrics["metrics"] and "avg_report_latency_seconds" in metrics["metrics"], "las métricas no exponen latencia de IA")
    expect("useful_discovery_rate" in metrics["metrics"] and "ready_for_report_rate" in metrics["metrics"], "las métricas no exponen embudo de discovery")
    expect("email_from_ready_rate" in metrics["metrics"] and "report_from_email_rate" in metrics["metrics"], "las métricas no exponen conversión del email-gate final")
    expect(metrics["metrics"].get("avg_feedback_rating", 0) >= 4, "las métricas no calculan utilidad media del feedback")
    expect(any(item.get("name") == "Costes estimados" for item in metrics["metrics"].get("top_feedback_missing", [])), "las métricas no agregan faltantes de feedback")
    expect(any(item.get("name") == "cohort" for item in metrics["metrics"].get("top_cta_interest", [])), "las métricas no agregan CTA por segmento")
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
    export_header = export_csv.splitlines()[0]
    expect("source,medium,campaign,video,ref" in export_header, "el export CSV no incluye atribución")
    expect("consent_accepted,consent_accepted_at,privacy_version" in export_header, "el export CSV no incluye consentimiento")
    expect("discovery_focus,discovery_confidence,discovery_ready,candidate_processes,open_gaps,live_insights" in export_header, "el export CSV no incluye discovery viva")
    expect("cta_interest,cta_clicked_at" in export_header, "el export CSV no incluye intención de CTA")
    expect("public_report_url" in export_header, "el export CSV no incluye enlace privado del informe")
    expect("first_opportunity,first_step" in export_header, "el export CSV no incluye resumen de acción")
    expect("objections,content_ideas" in export_header, "el export CSV no incluye inteligencia comercial")
    expect("evidence_summary" in export_header, "el export CSV no incluye señales de evidencia")
    checks.append({"check": "export_csv", "auth_required": bool(auth), "status_without_auth": export_without_auth})

    print(json.dumps({"ok": True, "base": args.base, "checks": checks}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
