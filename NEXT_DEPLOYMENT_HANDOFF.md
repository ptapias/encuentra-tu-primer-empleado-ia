# Siguiente paso: pasar de local a beta en VPS

Estado actual: la app local esta en verde para demo controlada. El agente real con Codex ha pasado discovery completa en clinica dental, inmobiliaria y consultor B2B, sin fallback, con informe e insights especificos. El bloqueo ya no es producto local: faltan datos reales para desplegar.

## 1. Rellena estos 8 datos

Abre `VPS_ANSWERS.local.json` y completa solo lo que falta. Importante: no renombres las claves; deben quedar exactamente como aparecen en el JSON.

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
```

Resultado esperado:

- `VPS_INPUTS.local.md` completo.
- `.env.generated` con configuracion de produccion.
- `privacy_config.json` con privacidad real.
- `PRIVACY_BETA.md` y `PRIVACY_BETA.html` renderizados sin placeholders.

Todos esos archivos locales sensibles estan ignorados por Git cuando corresponde.

## 3. Sube al VPS

En el VPS:

```bash
sudo mkdir -p /opt/primer-empleado-ia
sudo chown -R "$USER":"$USER" /opt/primer-empleado-ia
git clone https://github.com/ptapias/encuentra-tu-primer-empleado-ia.git /opt/primer-empleado-ia
cd /opt/primer-empleado-ia
```

Copia al VPS los archivos generados que hagan falta para instalar, especialmente `VPS_INPUTS.local.md` o `.env.generated`/`privacy_config.json` si decides llevarlos ya preparados.

Despues ejecuta:

```bash
sudo env DOMAIN=diagnostico.tu-dominio.com ./deploy/launch_from_inputs.sh
```

Cambia `diagnostico.tu-dominio.com` por el dominio real.

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
