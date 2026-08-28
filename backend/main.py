"""
FinSight Main FastAPI Application
"""

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from backend.db import Base, engine
from backend.routers.ai import router as ai_router
from backend.routers.dashboard import router as dashboard_router
from backend.routers.goals import router as goals_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinSight API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(dashboard_router)
app.include_router(goals_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FinSight Backend"}
