# Paquete de lanzamiento VPS

Este documento convierte el despliegue en una operación corta y verificable. La guía técnica completa está en `DEPLOYMENT_VPS.md`; aquí solo está lo necesario para pasar de local a beta real sin abrir algo a medias.

## 1. Datos que necesito

- Dominio o subdominio final: por ejemplo `diagnostico.tuprimerempleadoia.com`.
- IP del VPS y forma de acceso SSH.
- Sistema operativo del VPS.
- Usuario con permisos sudo.
- Confirmación de que el dominio ya apunta al VPS o que podemos cambiar DNS.
- Contraseña real para el CRM interno.
- URL de webhook si queremos sincronizar con Make, n8n, Zapier, Airtable, HubSpot u otro CRM externo desde el día 1.
- Email de contacto de privacidad.
- Responsable legal o datos fiscales que deben aparecer en privacidad.
- Proveedores reales que se usarán: VPS, Codex/OpenAI, transcripción, email si aplica.
- Plazo de conservación de leads y conversaciones.
- Decisión sobre newsletter: si el diagnóstico solo guarda lead o también suscribe a una lista.

Con esos datos, en el VPS:

```bash
cp privacy_config.example.json privacy_config.json
nano privacy_config.json
python3 render_privacy.py --config privacy_config.json
```

El generador actualiza `PRIVACY_BETA.md` y `PRIVACY_BETA.html`. Si queda algún `Completar`, se detiene.

## 2. Decisión de proveedor IA para la beta

Recomendación inicial: `AI_PROVIDER=codex` solo para beta privada o semi-privada con poco tráfico.

Condiciones mínimas:

- Codex CLI instalado en el VPS.
- Sesión de Codex iniciada en el VPS con el usuario de servicio (`primeria` por defecto), no solo con `root`.
- `ALLOW_AI_FALLBACK=false`.
- `MAX_AI_CONCURRENCY=1`.
- El usuario acepta que, si Codex tarda o falla, la app mostrará error honesto en vez de inventar un diagnóstico.

Plan B si Codex no es estable en VPS:

- Cambiar a `AI_PROVIDER=openai`.
- Añadir `OPENAI_API_KEY`.
- Mantener los mismos tests de smoke/release.

## 3. Comandos de instalación

En el VPS:

```bash
sudo mkdir -p /opt/primer-empleado-ia
sudo chown -R "$USER":"$USER" /opt/primer-empleado-ia
git clone https://github.com/ptapias/encuentra-tu-primer-empleado-ia.git /opt/primer-empleado-ia
cd /opt/primer-empleado-ia
sudo ./deploy/install_vps.sh
```

El primer pase crea `.env` y se detiene. Editar:

```bash
sudo nano /opt/primer-empleado-ia/.env
```

Valores mínimos:

```bash
HOST=127.0.0.1
PORT=8787
AI_PROVIDER=codex
CODEX_BIN=/usr/local/bin/codex
ALLOW_AI_FALLBACK=false
ADMIN_USER=admin
ADMIN_PASSWORD=una-password-larga-real
CRM_WEBHOOK_URL=
CRM_WEBHOOK_SECRET=
CRM_WEBHOOK_TIMEOUT=5
MAX_AI_CONCURRENCY=1
AI_QUEUE_WAIT_SECONDS=8
BETA_NOINDEX=true
```

Segundo pase:

```bash
cd /opt/primer-empleado-ia
sudo DOMAIN=diagnostico.tu-dominio.com ./deploy/install_vps.sh
```

## 4. Validación obligatoria

Antes de pasar un enlace a nadie:

```bash
cd /opt/primer-empleado-ia
sudo python3 preflight_vps.py --env .env --service-user primeria --check-codex-live
python3 test_beta_smoke.py --base http://127.0.0.1:8787 --admin-user admin --admin-password 'PASSWORD_REAL'
python3 test_beta_smoke.py --base https://diagnostico.tu-dominio.com --admin-user admin --admin-password 'PASSWORD_REAL'
```

El gate final para beta pública controlada:

```bash
python3 release_check.py \
  --env .env \
  --base https://diagnostico.tu-dominio.com \
  --admin-user admin \
  --admin-password 'PASSWORD_REAL' \
  --public-beta
```

Si falla, no se abre.

Atajo recomendado después de instalar:

```bash
DOMAIN=diagnostico.tu-dominio.com ./deploy/verify_vps.sh
```

Cuando la privacidad final esté completada y quieras abrir más allá de beta controlada:

```bash
DOMAIN=diagnostico.tu-dominio.com PUBLIC_BETA=true ./deploy/verify_vps.sh
```

Después de las pruebas manuales, usa el go/no-go operativo:

```bash
python3 launch_go_no_go.py \
  --env .env \
  --base https://diagnostico.tu-dominio.com \
  --admin-user admin \
  --admin-password 'PASSWORD_REAL' \
  --public-beta \
  --check-codex-live \
  --service-user primeria \
  --with-browser \
  --with-transcription \
  --manual-production-tested \
  --crm-reviewed \
  --mic-tested
```

Si el micro queda fuera de la primera beta, usa `--mic-optional` en lugar de `--mic-tested` y lanza el diagnóstico como flujo principalmente por texto.

## 5. Prueba manual de producto

Hacer dos diagnósticos reales en producción:

- Uno desde escritorio.
- Uno desde móvil.

En cada prueba:

- Empezar sin email.
- Usar texto.
- Probar micrófono en HTTPS.
- Responder hasta que el agente cierre la discovery.
- Dejar email y aceptar consentimiento.
- Generar informe.
- Confirmar que aparecen señales detectadas, matriz, plan y CTA.
- Guardar PDF.
- Marcar interés en CTA.
- Dejar feedback.
- Abrir CRM y comprobar conversación, outcome, consentimiento, CTA, feedback y atribución.
- Exportar CSV y comprobar `email`, `consent_accepted`, `cta_interest`, `feedback_rating`, `evidence_summary`.

Usa `MANUAL_PRODUCTION_TEST.md` como plantilla de aceptación. Rellena una copia por prueba o pega ahí las evidencias antes de abrir a testers.

## 6. Primer grupo de testers

Enviar a 5-10 personas, no más, durante la primera semana.

Perfiles:

- 2 profesionales saturados con email o mensajes.
- 2 negocios locales con citas o leads.
- 2 servicios B2B.
- 1 ecommerce o formación online.
- 1 agencia/consultor.

Preguntas de seguimiento:

- ¿En qué momento sentiste que el agente te entendía?
- ¿Qué pregunta te sobró?
- ¿Qué pregunta faltó?
- ¿La recomendación te pareció concreta o genérica?
- ¿Te dio ganas de crear ese empleado IA?
- ¿Qué habrías esperado ver en el informe?

## 7. Criterios para abrir más tráfico

Abrir a newsletter/YouTube si:

- El gate `--public-beta` pasa.
- El CRM está protegido.
- El micro funciona en HTTPS.
- 5 testers completan el diagnóstico.
- Al menos 3 de 5 dicen que el informe es concreto.
- Menos de 1 de 5 se atasca antes del informe.
- No hay ningún lead o conversación visible sin autenticación.

Mantener cerrado si:

- Codex falla o pierde sesión en VPS.
- El informe tarda demasiado o llega vacío.
- El CRM no exige contraseña.
- La privacidad sigue con placeholders.
- El micrófono no funciona y el copy sigue empujando a usarlo como vía principal.
