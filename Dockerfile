FROM python:3.13-slim

# Setam directorul de lucru
WORKDIR /app

# Instalam dependentele de sistem
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiem si instalam dependentele Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem tot proiectul
COPY . .

# Cream directorul pentru baza de date
RUN mkdir -p /app/data

# Expunem portul
EXPOSE 8000

# Comanda de start
CMD ["sh", "-c", "python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='$APP_USERNAME').exists() or User.objects.create_superuser('$APP_USERNAME', '', '$APP_PASSWORD')\" | python manage.py shell && \
    gunicorn core.wsgi:application --bind 0.0.0.0:8000"]