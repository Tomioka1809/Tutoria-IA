#!/bin/sh
set -e

echo "[entrypoint] Aplicando migraciones..."
alembic upgrade head

if [ "${AUTO_BOOTSTRAP:-1}" = "1" ]; then
  echo "[entrypoint] Verificando datos iniciales..."
  python -m app.bootstrap_data
else
  echo "[entrypoint] AUTO_BOOTSTRAP=0, se omite la siembra de datos."
fi

echo "[entrypoint] Arrancando: $*"
exec "$@"
