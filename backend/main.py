from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, logs, dashboard, integration
from app.core.config import settings
from app.models.database import engine, Base

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(integration.router, prefix="/integration", tags=["Integration"])

from app.workers.db_batch_worker import db_batch_worker

@app.on_event("startup")
async def startup():
    # Start the DB bulk insertion background worker
    db_batch_worker.start()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    # Gracefully flush and stop the bulk insertion worker
    await db_batch_worker.stop()

@app.get("/")
def root():
    return {"message": "Log Anomaly Detection API is running"}
