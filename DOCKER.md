# Docker Deployment Guide

This guide explains how to run Moneybags using Docker.

## Prerequisites

- Docker (version 20.10 or later)

## Quick Start

### Building the Image

Build the Docker image:
```bash
docker build -t moneybags .
```

### Running the Container

Run the container with volume mounting for data persistence:
```bash
docker run -d -p 8004:8004 \
  -v /home/xivind/container_data/moneybags:/app/data \
  --name moneybags-app \
  moneybags
```

Note: The example above uses `/home/xivind/container_data/moneybags` as the shared data directory. Adjust this path to match your container data directory pattern used by sister projects.

Access the application at: http://localhost:8004

### Stopping the Container

```bash
docker stop moneybags-app
docker rm moneybags-app
```

## Configuration

### Port

Moneybags runs on port 8004 by default. To use a different port, modify the `-p` flag:
```bash
docker run -d -p 9000:8004 -v /path/to/data:/app/data --name moneybags-app moneybags
```

### Environment Variables

The following environment variables can be configured at runtime:

- `DATABASE_PATH`: Path to the SQLite database file (default: `/app/data/moneybags.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

You can set these with the `-e` flag:
```bash
docker run -d -p 8004:8004 \
  -e DATABASE_PATH=/app/data/moneybags.db \
  -e LOG_LEVEL=DEBUG \
  -v /home/xivind/container_data/moneybags:/app/data \
  --name moneybags-app \
  moneybags
```

## Data Persistence

The database and logs are stored in a volume mounted at `/app/data` in the container. You should mount a directory from your host machine to persist data across container restarts.

### Shared Container Data Pattern

Following the pattern used by sister projects, mount a shared container data directory:
```bash
mkdir -p /home/xivind/container_data/moneybags
docker run -d -p 8004:8004 \
  -v /home/xivind/container_data/moneybags:/app/data \
  --name moneybags-app \
  moneybags
```

### Backup Your Data

To backup your data:
```bash
cp -r /home/xivind/container_data/moneybags /home/xivind/container_data/moneybags-backup-$(date +%Y%m%d)
```

## Health Checks

The container includes a health check that verifies the application is responding:
- Endpoint: `/health`
- Interval: 600 seconds (10 minutes)
- Timeout: 3 seconds
- Retries: 3

Check the health status:
```bash
docker ps
```

The `STATUS` column will show "healthy" when the application is running correctly.

## Troubleshooting

### View Logs

```bash
docker logs moneybags-app
```

Follow logs in real-time:
```bash
docker logs -f moneybags-app
```

### Access Container Shell

```bash
docker exec -it moneybags-app /bin/bash
```

### Reset Database

```bash
docker stop moneybags-app
docker rm moneybags-app
rm -rf /home/xivind/container_data/moneybags/*
docker run -d -p 8004:8004 \
  -v /home/xivind/container_data/moneybags:/app/data \
  --name moneybags-app \
  moneybags
```

## Development

For development with live code reloading, you can mount the source code:

```bash
docker run -d -p 8004:8004 \
  -v $(pwd)/app:/app/app \
  -v /home/xivind/container_data/moneybags:/app/data \
  --name moneybags-app-dev \
  moneybags
```

Note: You'll need to rebuild the image after dependency changes.

## Production Considerations

For production deployment:

1. Use a reverse proxy (nginx, Caddy) for SSL/TLS termination
2. Set up proper backup procedures for the database
3. Consider using PostgreSQL instead of SQLite for better concurrency
4. Set `LOG_LEVEL=WARNING` or `ERROR` in production
5. Use Docker secrets for sensitive configuration
6. Implement monitoring and alerting
7. Use container orchestration (Kubernetes, Docker Swarm) for high availability

## Building for Different Platforms

To build for a specific platform (e.g., ARM64):

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t moneybags .
```
