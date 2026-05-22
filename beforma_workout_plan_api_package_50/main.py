import os
from typing import Any, Dict
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from workout_models import WorkoutPlanRequest
from workout_generator import generate_workout_plan
from workout_database import EXERCISE_LIBRARY

API_VERSION = "1.1.0-workout-plan-50-exercises"
API_KEY = os.getenv("BEFORMA_API_KEY", "")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app = FastAPI(title="BeForma Workout Plan API", description="Personalized workout plan generator with 50 English exercises and local images.", version=API_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")

@app.get("/")
def root() -> Dict[str, Any]:
    return {"name": "BeForma Workout Plan API", "version": API_VERSION, "docs": "/docs", "health": "/health", "main_endpoint": "/api/v1/workout/generate-plan"}

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "beforma-workout-plan-api", "version": API_VERSION, "exercise_library_count": len(EXERCISE_LIBRARY)}

@app.get("/api/v1/workout/exercises", dependencies=[Depends(require_api_key)])
def list_exercises() -> Dict[str, Any]:
    return {"count": len(EXERCISE_LIBRARY), "exercises": [{"id": k, **v, "image_url": v["image"]} for k, v in EXERCISE_LIBRARY.items()]}

@app.post("/api/v1/workout/generate-plan", dependencies=[Depends(require_api_key)])
def generate_plan(payload: WorkoutPlanRequest) -> Dict[str, Any]:
    return generate_workout_plan(age=payload.age, weight_kg=payload.weight_kg, activity_level=payload.activity_level, primary_goal=payload.primary_goal, injuries=payload.injuries, experience_level=payload.experience_level, equipment=payload.equipment, days_per_week=payload.days_per_week)
