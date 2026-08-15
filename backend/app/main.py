from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import close_db, init_db
from backend.app.routes.analysis import router as analysis_router
from backend.app.routes.github import router as github_router
from backend.app.routes.health import router as health_router
from backend.app.routes.repositories import router as repositories_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="CodeGenome API",
    description="Deep-tech software intelligence platform for predicting code change impact",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(repositories_router)
app.include_router(analysis_router)
app.include_router(github_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CodeGenome API", "docs": "/docs"}


def run() -> None:
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
