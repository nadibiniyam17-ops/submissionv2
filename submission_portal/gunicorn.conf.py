"""Gunicorn settings for several people using the site at once.

systemd WorkingDirectory is submission_portal/, so this file is picked up
automatically. Override with GUNICORN_WORKERS, GUNICORN_THREADS, GUNICORN_BIND.
"""
import multiprocessing
import os


def _positive_int(name, default):
    raw = os.environ.get(name, '').strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000').strip() or '127.0.0.1:8000'
worker_class = 'gthread'
workers = _positive_int(
    'GUNICORN_WORKERS',
    max(2, min(4, (multiprocessing.cpu_count() or 1) + 1)),
)
threads = _positive_int('GUNICORN_THREADS', 4)
timeout = _positive_int('GUNICORN_TIMEOUT', 90)
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
