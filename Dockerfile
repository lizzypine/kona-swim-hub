FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  STATIC_ROOT=/app/www/static

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . ./

RUN mkdir -p "$STATIC_ROOT" /data \
  && SECRET_KEY=container-build-only \
  DATABASE_URL=sqlite:////tmp/kona-swim-hub-build.sqlite3 \
  DEBUG=False \
  python manage.py collectstatic --noinput \
  && chown -R app:app "$STATIC_ROOT" /data

USER app

EXPOSE 8000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 60 --access-logfile - --error-logfile - kona-swim-hub.wsgi:application"]