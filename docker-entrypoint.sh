#!/bin/sh
set -e
cd /app/submission_portal
if [ -z "$DJANGO_SECRET_KEY" ]; then
  export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
fi
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn submission_portal.wsgi:application --bind 0.0.0.0:8000 --workers 3
