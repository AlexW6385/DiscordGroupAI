# Deployment Guide

This guide provides instructions for starting the bot locally and deploying it to the cloud.

## 1. Local Startup (Standard)

You can now start the bot using `main.py` with various arguments:

### List available roles
```bash
python main.py --list-roles
```

### Start with specific roles
```bash
python main.py --roles expert,warm
```

### Start with all roles (as defined in .env)
```bash
python main.py
```

### Custom Port for API
```bash
python main.py --port 9000
```

---

## 2. Docker Deployment

### Local Docker Desktop
1. Ensure your `.env` is configured correctly.
2. Run the following command:
   ```bash
   docker-compose up --build
   ```

### Overriding Roles in Docker
You can override the startup roles in `docker-compose.yml` by modifying the `command` field:
```yaml
services:
  bot:
    command: python main.py --roles expert
```

---

## 3. Cloud Deployment Tips

### Environment Variables
Most cloud providers (Heroku, Railway, Render, AWS) allow you to set environment variables in their dashboard. Ensure you have the following set:
- `DISCORD_BOT_TOKEN` (or role-specific tokens in their YAMLs)
- `OPENAI_API_KEY`
- `DATABASE_URL` (pointing to your managed Postgres)
- `REDIS_URL` (pointing to your managed Redis)

### Managed Services
For better reliability, use managed services for persistence:
- **Database**: Supabase, ElephantSQL, or AWS RDS.
- **Redis**: Upstash or Redis Labs.

### Docker Image
You can push the generated Docker image to a container registry (Docker Hub, AWS ECR, GCP GCR) and deploy it to a container service like **AWS ECS**, **Google Cloud Run**, or **DigitalOcean App Platform**.
