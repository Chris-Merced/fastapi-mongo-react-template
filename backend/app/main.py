"""
App entrypoint. Run locally with:

    uvicorn app.main:app --reload

`--reload` is uvicorn's equivalent of nodemon - restarts the process when
source files change.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.routers import achievements, auth, individuals, insights, teams


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    FastAPI's startup/shutdown hook, as an async context manager.

    Everything before `yield` runs once on startup (open the Mongo
    connection); everything after `yield` runs once on shutdown (close it).
    Comparable to server.on('listening', ...) / server.on('close', ...) in
    a Node http server, just expressed as one function instead of two
    event listeners.
    """
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(title="ACME Team Management API", lifespan=lifespan)

# Vite's dev server runs on a different origin (port) than the API, so the
# browser enforces CORS - without this, fetch()/axios calls from the React
# app would be blocked client-side even though the request itself is fine.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(individuals.router)
app.include_router(teams.router)
app.include_router(achievements.router)
app.include_router(insights.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
