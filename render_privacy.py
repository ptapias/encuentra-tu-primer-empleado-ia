#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIRED_FIELDS = [
    "controller_name",
    "controller_legal_id",
    "contact_email",
    "hosting_provider",
    "ai_provider",
    "transcription_provider",
    "crm_provider",
    "webhook_destination",
    "email_provider",
    "retention_period",
    "newsletter_use",
    "last_updated",
]
FORBIDDEN_MARKERS = ["Completar", "Definir", "revisarse antes de publicación definitiva"]


def load_config(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED_FIELDS if not str(data.get(field, "")).strip()]
    if missing:
        raise SystemExit(f"Faltan campos obligatorios en {path}: {', '.join(missing)}")
    found = []
    for field in REQUIRED_FIELDS:
        value = str(data.get(field, ""))
        for marker in FORBIDDEN_MARKERS:
            if marker.lower() in value.lower():
                found.append(f"{field}: {marker}")
    if found:
        raise SystemExit("La configuración de privacidad conserva placeholders: " + ", ".join(found))
    return {field: str(data[field]).strip() for field in REQUIRED_FIELDS}


def render_markdown(cfg: dict) -> str:
    providers = [
        f"Hosting/VPS: {cfg['hosting_provider']}",
        f"IA: {cfg['ai_provider']}",
        f"Transcripción: {cfg['transcription_provider']}",
        f"CRM y almacenamiento: {cfg['crm_provider']}",
        f"Webhook/automatización externa: {cfg['webhook_destination']}",
        f"Email: {cfg['email_provider']}",
    ]
    provider_lines = "\n".join(f"- {item}" for item in providers)
    return f"""# Privacidad - Encuentra Tu Primer Empleado IA

Última actualización: {cfg['last_updated']}

Esta política explica cómo se usan los datos cuando una persona realiza el diagnóstico gratuito "Encuentra Tu Primer Empleado IA".

## Información básica

| Punto | Información |
|---|---|
| Responsable | {cfg['controller_name']} ({cfg['controller_legal_id']}) |
| Contacto | {cfg['contact_email']} |
| Finalidad | Generar un diagnóstico personalizado de procesos automatizables, guardar el resultado, crear un enlace privado de acceso al informe, mejorar el producto con feedback y cualificar el siguiente paso comercial cuando proceda. |
| Datos tratados | Email, respuestas de la conversación, información de negocio aportada por la persona, informe generado, enlace privado de acceso al diagnóstico, métricas de uso, interés en el siguiente paso y feedback. |
| Base | Consentimiento de la persona al dejar su email, aceptar la política y solicitar el informe. |
| Destinatarios | No vendemos datos. Usamos proveedores técnicos necesarios para prestar el servicio y operar la beta. |
| Conservación | {cfg['retention_period']} |
| Newsletter | {cfg['newsletter_use']} |

## Proveedores técnicos

{provider_lines}

## Qué datos se recogen

- Email, si la persona lo deja al final para generar y guardar el diagnóstico.
- Respuestas de la conversación y contexto de negocio que la persona decida compartir.
- Informe generado, enlace privado de acceso al diagnóstico, métricas de uso, interés en CTA y feedback.
- Datos técnicos básicos necesarios para operar la web y proteger el servicio.

## Para qué se usan

- Generar el diagnóstico personalizado.
- Mostrar oportunidades de automatización, riesgos, matriz de priorización y plan de acción.
- Guardar el resultado en el CRM interno y crear un enlace privado de acceso al informe para recuperar el diagnóstico.
- Revisar calidad, detectar fallos y entender qué casos de uso interesan más.
- Proponer un siguiente paso si encaja con el caso: recurso, newsletter, cohort, llamada o implementación.

## Qué no hacemos

- No vendemos tus datos.
- No publicamos conversaciones ni informes individuales; el enlace privado del informe no muestra email, conversación completa ni CRM interno.
- No usamos el diagnóstico para tomar decisiones legales, médicas, financieras o laborales automatizadas.
- No dejamos que una decisión comercial delicada dependa solo de la IA sin revisión humana.

## Derechos

Puedes pedir acceso, rectificación, supresión, oposición, limitación o portabilidad escribiendo a {cfg['contact_email']}.

## Solicitudes de eliminación

Si pides borrar tus datos, eliminaremos el lead y sus eventos asociados del CRM interno. Los backups se gestionarán conforme al plazo de conservación indicado arriba, salvo obligación legal aplicable.

## Texto corto para el punto de recogida

Usaremos tu email y esta conversación para generar y guardar el diagnóstico, crear un enlace privado de acceso al informe, mejorar la experiencia y proponerte un siguiente paso si encaja. No vendemos tus datos. Puedes pedir que eliminemos tu información escribiendo a {cfg['contact_email']}.
"""


def render_html(cfg: dict) -> str:
    e = html.escape
    providers = [
        ("Hosting/VPS", cfg["hosting_provider"]),
        ("IA", cfg["ai_provider"]),
        ("Transcripción", cfg["transcription_provider"]),
        ("CRM y almacenamiento", cfg["crm_provider"]),
        ("Webhook/automatización externa", cfg["webhook_destination"]),
        ("Email", cfg["email_provider"]),
    ]
    provider_items = "\n".join(f"          <li><strong>{e(label)}:</strong> {e(value)}</li>" for label, value in providers)
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Privacidad - Encuentra Tu Primer Empleado IA</title>
  <style>
    :root {{
      --bg: #f4f7f5;
      --ink: #171717;
      --muted: #62645f;
      --line: #d7dfd8;
      --panel: #ffffff;
      --accent: #1f7a5b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }}
    main {{
      width: min(940px, calc(100% - 32px));
      margin: 0 auto;
      padding: 42px 0 56px;
      display: grid;
      gap: 16px;
    }}
    h1 {{
      font-size: clamp(36px, 6vw, 72px);
      line-height: .96;
      letter-spacing: 0;
      margin: 0;
      max-width: 820px;
    }}
    h2 {{
      font-size: 22px;
      letter-spacing: 0;
      margin: 0;
    }}
    p {{ margin: 0; color: #383a36; }}
    a {{ color: var(--accent); font-weight: 900; text-decoration: none; }}
    .eyebrow {{
      color: var(--accent);
      font-size: 13px;
      font-weight: 900;
      text-transform: uppercase;
    }}
    .lead {{
      font-size: 19px;
      max-width: 760px;
    }}
    .card {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 18px;
      display: grid;
      gap: 10px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 6px;
    }}
    .note {{
      border-left: 4px solid var(--accent);
      padding-left: 12px;
      color: var(--muted);
    }}
    @media (max-width: 760px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="eyebrow">Privacidad</div>
    <h1>Cómo usamos tus datos durante el diagnóstico</h1>
    <p class="lead">Recogemos la información necesaria para entender tu negocio, generar un diagnóstico útil, guardar el resultado y mejorar el producto con feedback real.</p>

    <section class="grid">
      <div class="card">
        <h2>Responsable</h2>
        <p>{e(cfg['controller_name'])}</p>
        <p>{e(cfg['controller_legal_id'])}</p>
        <p>Contacto: <a href="mailto:{e(cfg['contact_email'])}">{e(cfg['contact_email'])}</a></p>
      </div>
      <div class="card">
        <h2>Conservación</h2>
        <p>{e(cfg['retention_period'])}</p>
        <p>{e(cfg['newsletter_use'])}</p>
      </div>
      <div class="card">
        <h2>Qué datos se recogen</h2>
        <ul>
          <li>Email, si lo dejas al final para generar y guardar el diagnóstico.</li>
          <li>Respuestas de la conversación y contexto de negocio que decidas compartir.</li>
          <li>Informe generado, enlace privado de acceso al diagnóstico, métricas de uso, interés en CTA y feedback.</li>
        </ul>
      </div>
      <div class="card">
        <h2>Para qué se usan</h2>
        <ul>
          <li>Generar tu diagnóstico personalizado.</li>
          <li>Revisar calidad y mejorar la experiencia.</li>
          <li>Proponerte un siguiente paso solo si encaja con tu caso.</li>
        </ul>
      </div>
      <div class="card">
        <h2>Qué no hacemos</h2>
        <ul>
          <li>No vendemos tus datos.</li>
          <li>No publicamos tu conversación ni mostramos el CRM interno en el enlace privado del informe.</li>
          <li>No dejamos que una decisión comercial delicada dependa solo de la IA.</li>
        </ul>
      </div>
      <div class="card">
        <h2>Tus derechos</h2>
        <p>Puedes pedir acceso, rectificación, supresión, oposición, limitación o portabilidad escribiendo a <a href="mailto:{e(cfg['contact_email'])}">{e(cfg['contact_email'])}</a>.</p>
      </div>
    </section>

    <section class="card">
      <h2>Proveedores técnicos</h2>
      <ul>
{provider_items}
      </ul>
    </section>

    <p class="note">Si pides borrar tus datos, eliminaremos el lead y sus eventos asociados del CRM interno. Los backups se gestionarán conforme al plazo de conservación indicado, salvo obligación legal aplicable.</p>
    <p>Última actualización: {e(cfg['last_updated'])}</p>
    <p><a href="/Agente_Real_CRM.html">Volver al diagnóstico</a></p>
  </main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Genera PRIVACY_BETA.md y PRIVACY_BETA.html desde una configuración real.")
    parser.add_argument("--config", default="privacy_config.json", help="JSON con datos reales de privacidad")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    cfg = load_config(config_path)
    md = render_markdown(cfg)
    html_text = render_html(cfg)
    (ROOT / "PRIVACY_BETA.md").write_text(md, encoding="utf-8")
    (ROOT / "PRIVACY_BETA.html").write_text(html_text, encoding="utf-8")
    print(json.dumps({"ok": True, "markdown": "PRIVACY_BETA.md", "html": "PRIVACY_BETA.html"}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
