# backend/main.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import router

app = FastAPI(
    title="AI Product Intelligence Loop",
    description="Multi-agent AI system for product decision making",
    version="1.0.0"
)

# Allow React dashboard to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "system": "AI Product Intelligence Loop",
        "version": "1.0.0",
        "stages": ["discover", "evaluate", "decide", "learn"],
        "status": "running"
    }