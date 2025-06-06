#!/bin/bash
# cleanup-docker.sh
echo "Cleaning up Docker resources..."
docker image prune -a -f
docker container prune -f
docker volume prune -f
docker builder prune -a -f
echo "Cleanup complete!"
