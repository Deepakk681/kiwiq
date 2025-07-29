# PYTHONPATH=$(pwd):$(pwd)/services poetry run gunicorn services.workflow_service.services.scraping.spider_server:app -c services/workflow_service/services/scraping/spider_gunicorn.conf.py
# gunicorn services.workflow_service.services.scraping.spider_server:app -c services/workflow_service/services/scraping/spider_gunicorn.conf.py

from global_config.settings import global_settings

# gunicorn.conf.py - Minimal production config
bind = "0.0.0.0:6969"
workers = 4
# worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 600
graceful_timeout = 600
keepalive = 5

# Prevent memory leaks with worker recycling
max_requests = 1
max_requests_jitter = 0

# Logging
# accesslog = "-"
# errorlog = "-"
# loglevel = global_settings.LOG_LEVEL.lower()
# print("LOG_LEVEL", loglevel)

# Use RAM for worker heartbeat (faster hang detection)
# worker_tmp_dir = "/dev/shm"

# Preload app for faster restarts
preload_app = True
# worker_connections
# backlog
# capture_output = True
