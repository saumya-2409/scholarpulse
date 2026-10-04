from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.research import router as research_router
from api.paper import router as paper_router
from api.auth import router as auth_router

from database import init_database

app = FastAPI(
    title="ScholarPulse API",
    description="Backend API for the ScholarPulse research assistant.",
    version="1.0.0",
)

init_database()

# Allow the React/Vite frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(research_router)
app.include_router(paper_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "ScholarPulse API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }