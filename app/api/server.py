from fastapi import FastAPI
from app.config import settings

app = FastAPI(title="Discord Group AI Admin API")

@app.get("/health")
async def health_check():
    """Simple health check endpoint for Docker/Kubernetes."""
    return {"status": "ok", "app": settings.app_name}

@app.get("/api/v1/stats")
async def get_stats():
    """Retrieve basic stats (could query DB in the future)."""
    return {
        "messages_ingested": 0,
        "responses_generated": 0
    }
