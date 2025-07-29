#!/bin/bash
set -e

# Propagate SIGTERM/SIGINT to all background jobs
trap 'kill $(jobs -p) 2>/dev/null' SIGTERM SIGINT

python services/workflow_service/services/worker.py &

gunicorn services.workflow_service.services.scraping.spider_server:app \
    -c services/workflow_service/services/scraping/spider_gunicorn.conf.py &

wait -n
exit $?
