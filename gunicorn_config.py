"""
gunicorn_config.py
Production WSGI server config. Used automatically by:
    gunicorn -c gunicorn_config.py app:app
Render/Railway use the Procfile's command directly, but this file is
handy for PythonAnywhere / VPS / Docker deployments.
"""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = min(4, multiprocessing.cpu_count() * 2 + 1)
threads = 4
worker_class = "sync"
timeout = 90
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
