#!/bin/bash

set -o xtrace

# Cleanup container and image
docker container stop moneybags
docker container rm moneybags
docker image rm moneybags

# Build image and tag it
docker build -t moneybags .

# Create data and logs directories on host if they don't exist
mkdir -p ~/code/container_data/logs

# Create and run container
docker run -d \
  --name=moneybags \
  -e TZ=Europe/Stockholm \
  -e DB_HOST=192.168.1.100 \
  -e DB_PORT=3306 \
  -e DB_NAME=moneybags \
  -e DB_USER=moneybags_user \
  -e DB_PASSWORD=moneybags_pass \
  -e DB_POOL_SIZE=10 \
  -v ~/code/container_data:/app/data \
  --restart unless-stopped \
  -p 8000:8003 \
  moneybags
