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
mkdir -p ~/code/container_data/moneybags

# Create and run container
docker run -d \
  --name=moneybags \
  -e TZ=Europe/Stockholm \
  -v ~/code/container_data/moneybags/db_config.json:/app/db_config.json \
  -v ~/code/container_data:/app/data \
  --restart unless-stopped \
  -p 8003:8000 \
  moneybags
