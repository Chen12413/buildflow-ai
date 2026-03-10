from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.routers import clarifications, exports, planning, prd, projects, runs

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(clarifications.router, prefix=settings.api_v1_prefix)
app.include_router(prd.router, prefix=settings.api_v1_prefix)
app.include_router(planning.router, prefix=settings.api_v1_prefix)
app.include_router(runs.router, prefix=settings.api_v1_prefix)
app.include_router(exports.router, prefix=settings.api_v1_prefix)
