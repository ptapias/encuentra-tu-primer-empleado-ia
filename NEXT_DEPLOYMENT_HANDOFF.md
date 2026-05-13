# Siguiente paso: pasar de local a beta en VPS

Estado actual: la app local esta en verde para demo controlada. El agente real con Codex ha pasado discovery completa en clinica dental, inmobiliaria y consultor B2B, sin fallback, con informe e insights especificos. El bloqueo ya no es producto local: faltan datos reales para desplegar.

## 0. Mira el semáforo antes de tocar nada

```bash
python3 beta_readiness_status.py --plain
```

Ahora mismo deberías ver algo parecido a:

```text
Estado: blocked_on_launch_inputs.
Datos VPS completados: 16/24.
```

Ese comando es la fuente corta de verdad para saber qué falta. Si después de rellenar datos sigue bloqueado, lee primero la sección "Valores ya rellenados que también bloquean": suele ser Codex no logueado como usuario systemd, DNS todavía no apuntando al VPS, contraseña CRM débil o privacidad incompleta.

## 1. Rellena estos 8 datos

Abre `VPS_ANSWERS.local.json` y completa solo lo que falta. Importante: no renombres las claves; deben quedar exactamente como aparecen en el JSON.

Si no tienes todavía ese archivo local:

```bash
cp VPS_ANSWERS.example.json VPS_ANSWERS.local.json
```

Si prefieres que el asistente pregunte solo los campos pendientes o valores bloqueantes:

```bash
python3 generate_vps_inputs.py --fill-missing-answers VPS_ANSWERS.local.json
```

Ese asistente tambien revisa valores ya escritos que bloquean el despliegue, por ejemplo Codex marcado como no logueado, contraseña demasiado corta, email invalido o dominio/DNS no listo.

- `Dominio/subdominio público`: por ejemplo `diagnostico.tuprimerempleadoia.com`.
- `IP del VPS`: IP pública del servidor.
- `Usuario SSH`: usuario con permisos para entrar al VPS.
- `Contraseña real CRM`: mínimo 16 caracteres, sin espacios, comillas, `#` ni barras invertidas.
- `Responsable legal`: nombre o sociedad responsable.
- `NIF/CIF o razón social`: dato legal que aparecerá en privacidad.
- `Email de contacto privacidad`: email para derechos/supresión.
- `Proveedor VPS/hosting`: proveedor donde esta alojado el servidor.

Mantener el resto como esta sirve para una primera beta controlada, salvo que quieras activar webhook externo desde el dia 1.

## 2. Genera los archivos locales de lanzamiento

Cuando esos datos esten rellenos:

```bash
python3 generate_vps_inputs.py --answers-json VPS_ANSWERS.local.json
python3 validate_vps_inputs.py --path VPS_INPUTS.local.md
python3 prepare_vps_launch_files.py --inputs VPS_INPUTS.local.md
python3 render_privacy.py --config privacy_config.json
python3 print_vps_deploy_commands.py --inputs VPS_INPUTS.local.md
```

Resultado esperado:

- `VPS_INPUTS.local.md` completo.
- `.env.generated` con configuracion de produccion.
- `privacy_config.json` con privacidad real.
- `PRIVACY_BETA.md` y `PRIVACY_BETA.html` renderizados sin placeholders.

Todos esos archivos locales sensibles estan ignorados por Git cuando corresponde.

## 3. Sube al VPS

Usa los comandos que imprime este script desde tu máquina local:

```bash
python3 print_vps_deploy_commands.py --inputs VPS_INPUTS.local.md
```

Ese es el camino recomendado: copia `VPS_INPUTS.local.md` al VPS y `deploy/launch_from_inputs.sh` volverá a validar la ficha y generará allí `.env.generated` y `privacy_config.json`.

Solo copies `.env.generated` o `privacy_config.json` si decides saltarte el flujo guiado y hacer una instalación manual con `deploy/install_vps.sh`.

## 4. Condicion especial si usamos Codex

Si `AI_PROVIDER=codex`, el usuario systemd que corre la app, por defecto `primeria`, debe tener Codex CLI logueado. No basta con que lo este `root`.

Validacion esperada:

```bash
sudo python3 preflight_vps.py --env .env --service-user primeria --check-codex-live
```

Si esto falla, no abras la beta.

## 5. Gate antes de enviar el enlace

Primero prueba el VPS:

```bash
DOMAIN=diagnostico.tu-dominio.com ./deploy/verify_vps.sh
```

Luego, cuando hagas prueba manual completa en escritorio y movil:

```bash
cp MANUAL_PRODUCTION_TEST.md MANUAL_PRODUCTION_TEST.local.md
nano MANUAL_PRODUCTION_TEST.local.md
python3 validate_manual_production_test.py --path MANUAL_PRODUCTION_TEST.local.md
```

Gate final de beta publica controlada:

```bash
DOMAIN=diagnostico.tu-dominio.com \
PUBLIC_BETA=true \
BROWSER_CHECKS=true \
TRANSCRIPTION_CHECK=true \
MANUAL_PRODUCTION_TESTED=true \
MANUAL_TEST_PATH=MANUAL_PRODUCTION_TEST.local.md \
CRM_REVIEWED=true \
MIC_TESTED=true \
./deploy/verify_vps.sh
```

Si el micro no entra en la primera beta, cambia `MIC_TESTED=true` por `MIC_OPTIONAL=true` y ajusta el copy para no empujar el micro como via principal.

## 6. Primer envio

No lo lances aun a toda la newsletter. Primer grupo recomendado: 5-10 testers.

Perfiles:

- 2 profesionales saturados con email o mensajes.
- 2 negocios locales con citas o leads.
- 2 servicios B2B.
- 1 ecommerce o formacion online.
- 1 agencia o consultor.

Criterio minimo para abrir mas trafico: 5 testers completan el flujo, al menos 3 dicen que el informe es concreto, nadie ve CRM/datos sin auth y el go/no-go publico pasa.
