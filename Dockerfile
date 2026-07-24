# Python 3.12 is used rather than 3.14 because Django 5.0 does not yet
# officially support 3.14 (the admin site breaks on template rendering).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Accept requests from any host so the app works in a container or on
# Docker Playground. Override for production deployments.
ENV DJANGO_ALLOWED_HOSTS="*"

WORKDIR /app

# Build tools are needed for Pillow's image handling dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Apply migrations at startup so the container works with a fresh database.
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]