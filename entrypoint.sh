#!/bin/bash
set -e

echo "Esecuzione delle migrazioni Alembic..."
alembic upgrade head

echo "Avvio dell'applicazione proxy..."
exec "$@"
