#!/usr/bin/env python3
"""
Gunicorn configuration for Discord bot production deployment.
Optimized for Replit Reserved VM deployments with proper resource management.
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes - Single worker for Discord bot compatibility
workers = 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120
keepalive = 2
threads = 4

# Restart workers after this many seconds
max_worker_memory = 200  # MB
worker_memory_limit = max_worker_memory * 1024 * 1024  # Convert to bytes

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "discord-bot-rivalz"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None

# Application
wsgi_module = "wsgi:application"

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Discord bot WSGI server is ready. Serving on %s", bind)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Discord bot worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Discord bot worker %s is being forked", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Discord bot worker %s spawned", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Discord bot worker %s initialized", worker.pid)