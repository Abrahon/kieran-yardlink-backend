#!/bin/sh
set -e

if [ "$DATABASE" = "postgres" ] || [ "${DB_HOST:-}" != "" ]; then
  echo "Waiting for postgres..."
  while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
    sleep 1
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
