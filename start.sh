#!/bin/sh

python manage.py migrate

python manage.py collectstatic --noinput

python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="${APP_USERNAME}").exists():
    User.objects.create_superuser("${APP_USERNAME}", "", "${APP_PASSWORD}")
    print("Superuser created")
else:
    print("Superuser already exists")
EOF

gunicorn core.wsgi:application --bind 0.0.0.0:8000