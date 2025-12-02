# Docker Deployment Guide

This guide explains how to run Moneybags using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 1.29 or later)

## Quick Start

### Using Docker Compose (Recommended)

1. Build and start the application:
```bash
docker-compose up -d
```

2. Access the application at: http://localhost:8000

3. Stop the application:
```bash
docker-compose down
```

### Using Docker directly

1. Build the image:
```bash
docker build -t moneybags .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name moneybags-app moneybags
```

3. Stop the container:
```bash
docker stop moneybags-app
docker rm moneybags-app
```

## Configuration

### Environment Variables

The following environment variables can be configured:

- `DATABASE_PATH`: Path to the SQLite database file (default: `/app/data/moneybags.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

You can set these in the `docker-compose.yml` file or pass them with the `-e` flag:

```bash
docker run -d -p 8000:8000 \
  -e DATABASE_PATH=/app/data/moneybags.db \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/data:/app/data \
  moneybags
```

## Data Persistence

The database is stored in a volume mounted at `/app/data` in the container. By default, Docker Compose maps this to `./data` on your host machine.

To backup your data:
```bash
cp -r ./data ./data-backup-$(date +%Y%m%d)
```

## Health Checks

The container includes a health check that verifies the application is responding:
- Endpoint: `/health`
- Interval: 30 seconds
- Timeout: 3 seconds
- Retries: 3

Check the health status:
```bash
docker ps
```

The `STATUS` column will show "healthy" when the application is running correctly.

## Troubleshooting

### View logs
```bash
docker-compose logs -f
```

or

```bash
docker logs moneybags-app
```

### Access container shell
```bash
docker-compose exec moneybags /bin/bash
```

or

```bash
docker exec -it moneybags-app /bin/bash
```

### Reset database
```bash
docker-compose down
rm -rf ./data
docker-compose up -d
```

## Development

For development with live code reloading, you can mount the source code:

```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/app:/app/app \
  -v $(pwd)/data:/app/data \
  moneybags
```

Note: You'll need to rebuild the image after dependency changes.

## Production Considerations

For production deployment:

1. Use a reverse proxy (nginx, Caddy) for SSL/TLS termination
2. Set up proper backup procedures for the database
3. Consider using a PostgreSQL database instead of SQLite for better concurrency
4. Set `LOG_LEVEL=WARNING` or `ERROR` in production
5. Use Docker secrets for sensitive configuration
6. Implement monitoring and alerting
7. Use container orchestration (Kubernetes, Docker Swarm) for high availability

## Building for Different Platforms

To build for a specific platform (e.g., ARM64):

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t moneybags .
```
