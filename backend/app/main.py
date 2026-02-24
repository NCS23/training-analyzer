from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Router
from app.routers import training

app = FastAPI(
    title="Training Analyzer API",
    description="API for analyzing running and strength training data",
    version="0.1.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Später auf Frontend-URL beschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(training.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Training Analyzer API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
