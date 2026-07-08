from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth, legal, services

app = FastAPI(
    title="YerevanServices API",
    description="Backend for a hyperlocal service marketplace (tutoring, repairs, car audio, etc). "
    "Self-hosted: FastAPI + PostgreSQL, no third-party BaaS dependency.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(legal.router)


@app.on_event("startup")
def create_tables():
    # Simple table creation instead of a migration tool (Alembic) —
    # deliberate choice for a small/early-stage project: one less moving
    # part to configure and debug. If the schema needs to evolve later
    # (adding a column to existing production data), that's the moment
    # to introduce Alembic; until then this is safe because it only
    # creates tables that don't exist yet, never alters existing ones.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
