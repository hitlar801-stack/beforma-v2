"""BeForma Nutrition API - final Railway-ready version.

Main endpoint for backend:
    POST /generate-plan
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from database import GeneratedPlan, db_session, init_db
from meal_generator import generate_full_meal_plan
from meals_db import MEALS_DB, count_by_type
from nutrition import activity_factor, calculate_bmi, generate_nutrition_plan, normalize_goal
from recommender import get_feedback_stats, get_meal_tags, rank_meals_for_goal, record_feedback, suggest_substitutions
from validator import validate_plan

API_VERSION = "2.0.0-final"
API_KEY = os.getenv("BEFORMA_NUTRITION_API_KEY", "")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
INIT_DB_ON_STARTUP = os.getenv("INIT_DB_ON_STARTUP", "true").lower() == "true"

Goal = Literal["lose", "maintain", "gain"]
Gender = Literal["male", "female", "other", "m", "f"]
Strategy = Literal["strict", "flexible"]
MealType = Literal["breakfast", "lunch", "dinner"]

app = FastAPI(
    title="BeForma Nutrition API",
    description="Graduation-project API for BMI, calories, macros, 300+ meal recommendations with images, and optional DB saving.",
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    if INIT_DB_ON_STARTUP:
        try:
            init_db()
        except Exception:
            # Never block API startup because DB was not configured yet.
            pass


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")


class GeneratePlanRequest(BaseModel):
    name: str = Field(..., examples=["Ibrahim"])
    email: str = Field(..., examples=["ibrahim@example.com"])
    phone: str = Field(..., examples=["01000000000"])
    age: int = Field(..., ge=10, le=100, examples=[24])
    gender: str = Field(..., examples=["male"])
    height: float = Field(..., ge=100, le=250, description="Height in cm", examples=[178])
    weight: float = Field(..., ge=30, le=300, description="Weight in kg", examples=[82])
    fitnessGoal: str = Field(..., examples=["lose"])
    activityLevel: str = Field("Sedentary", examples=["Sedentary"])
    experienceLevel: str = Field("Beginner", examples=["Beginner"])
    workoutLocation: str = Field("Home", examples=["Home"])
    dietaryPreference: str = Field("normal", examples=["normal"])

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, value: str) -> str:
        v = value.strip().lower()
        if v == "m":
            return "male"
        if v == "f":
            return "female"
        if v not in {"male", "female", "other"}:
            return "other"
        return v


class UserNutritionInput(BaseModel):
    age: int = Field(..., ge=10, le=100, examples=[24])
    gender: Gender = Field(..., examples=["male"])
    height: float = Field(..., ge=100, le=250, examples=[178])
    weight: float = Field(..., ge=30, le=300, examples=[82])
    activity_level: float = Field(..., ge=1.0, le=2.2, examples=[1.55])
    goal: Goal = Field(..., examples=["lose"])


class MealPlanRequest(UserNutritionInput):
    num_meals: int = Field(3, ge=3, le=3, examples=[3])
    strategy: Strategy = Field("strict", examples=["strict"])
    dietary_preference: str = Field("normal", examples=["normal"])


class FeedbackRequest(BaseModel):
    meal_name: str
    accepted: bool
    user_id: Optional[str] = None


class ValidatePlanRequest(BaseModel):
    meals: list[dict]
    plan_totals: dict
    target_calories: float = Field(..., gt=0)
    goal: Goal
    calorie_tolerance: float = Field(0.06, ge=0.01, le=0.20)


class SubstitutionRequest(BaseModel):
    meal_name: str


def build_workout_plan(fitness_goal: str, experience_level: str, workout_location: str) -> dict:
    goal = normalize_goal(fitness_goal)
    level = (experience_level or "Beginner").strip().lower()
    location = (workout_location or "Home").strip().lower()
    if "home" in location:
        exercises = ["Squat", "Push-up", "Glute bridge", "Plank", "Lunges"]
        equipment = "bodyweight"
    else:
        exercises = ["Leg press", "Chest press", "Lat pulldown", "Shoulder press", "Cable row"]
        equipment = "gym machines/free weights"
    days = 3 if level == "beginner" else 4
    if goal == "gain":
        focus = "progressive overload and hypertrophy"
        cardio = "10-15 min light cardio after lifting"
    elif goal == "lose":
        focus = "strength training with calorie-burning circuits"
        cardio = "20-30 min moderate cardio 3x/week"
    else:
        focus = "balanced strength and fitness maintenance"
        cardio = "15-20 min cardio 2x/week"
    return {
        "fitnessGoal": fitness_goal,
        "normalizedGoal": goal,
        "experienceLevel": experience_level,
        "workoutLocation": workout_location,
        "days_per_week": days,
        "equipment": equipment,
        "focus": focus,
        "cardio": cardio,
        "sample_exercises": exercises,
        "message": "Workout plan placeholder is generated from profile data and can be replaced by the workout module.",
    }


def save_generated_plan(request_id: str, payload: GeneratePlanRequest, response: dict) -> None:
    try:
        with db_session() as db:
            db.add(GeneratedPlan(
                request_id=request_id,
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                age=payload.age,
                gender=payload.gender,
                height=payload.height,
                weight=payload.weight,
                fitness_goal=payload.fitnessGoal,
                activity_level=payload.activityLevel,
                experience_level=payload.experienceLevel,
                workout_location=payload.workoutLocation,
                dietary_preference=payload.dietaryPreference,
                bmi=response.get("bmi"),
                bmi_category=response.get("bmi_category"),
                daily_calorie_target=response.get("daily_calorie_target"),
                macros_json=response.get("macros"),
                diet_plan_json=response.get("recommendations", {}).get("diet_plan"),
                workout_plan_json=response.get("recommendations", {}).get("workout_plan"),
                raw_request_json=payload.model_dump(),
                raw_response_json=response,
            ))
    except Exception:
        pass


@app.get("/")
def root() -> dict:
    return {
        "service": "BeForma Nutrition API",
        "version": API_VERSION,
        "docs": "/docs",
        "main_endpoint": "POST /generate-plan",
        "meals_count": len(MEALS_DB),
        "meals_by_type": count_by_type(),
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "beforma-nutrition-api",
        "version": API_VERSION,
        "meals_count": len(MEALS_DB),
        "meals_by_type": count_by_type(),
        "main_endpoint": "/generate-plan",
    }


@app.post("/generate-plan")
def generate_plan(payload: GeneratePlanRequest) -> dict:
    """Main endpoint for Flutter/backend integration.

    Receives the exact camelCase request from the client and returns BMI, calories, macros,
    3 meals with images, and a workout placeholder.
    """
    request_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    goal = normalize_goal(payload.fitnessGoal)
    factor = activity_factor(payload.activityLevel)
    bmi, bmi_category = calculate_bmi(payload.height, payload.weight)

    nutrition_plan = generate_nutrition_plan(
        age=payload.age,
        gender=payload.gender,
        height=payload.height,
        weight=payload.weight,
        activity_level=factor,
        goal=goal,
    )
    full_plan = generate_full_meal_plan(
        nutrition_plan=nutrition_plan,
        num_meals=3,
        strategy="strict",
        dietary_preference=payload.dietaryPreference,
    )
    workout_plan = build_workout_plan(payload.fitnessGoal, payload.experienceLevel, payload.workoutLocation)
    response = {
        "request_id": request_id,
        "status": "success",
        "user": {
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "age": payload.age,
            "gender": payload.gender,
            "height": payload.height,
            "weight": payload.weight,
        },
        "bmi": bmi,
        "bmi_category": bmi_category,
        "daily_calorie_target": full_plan["daily_targets"]["daily_calories"],
        "macros": {
            "protein_grams": full_plan["daily_targets"]["protein_grams"],
            "carbs_grams": full_plan["daily_targets"]["carbs_grams"],
            "fat_grams": full_plan["daily_targets"]["fat_grams"],
        },
        "recommendations": {
            "diet_plan": full_plan["meals"],
            "workout_plan": workout_plan,
        },
        "plan_quality": {
            "quality_score": full_plan["quality_score"],
            "optimized": full_plan["optimized"],
            "accuracy": full_plan["accuracy"],
            "validation": full_plan["validation"],
        },
        "meta": {
            "activity_factor": factor,
            "normalized_goal": goal,
            "dietary_preference": payload.dietaryPreference,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
            "catalog_meals_count": len(MEALS_DB),
        },
    }
    save_generated_plan(request_id, payload, response)
    return response


@app.post("/api/v1/nutrition/targets", dependencies=[Depends(require_api_key)])
def calculate_targets(payload: UserNutritionInput) -> dict:
    plan = generate_nutrition_plan(payload.age, payload.gender, payload.height, payload.weight, payload.activity_level, payload.goal)
    return {"request_id": str(uuid.uuid4()), "status": "success", "targets": plan.as_dict(), "input": payload.model_dump()}


@app.post("/api/v1/nutrition/meal-plan", dependencies=[Depends(require_api_key)])
def generate_meal_plan(payload: MealPlanRequest) -> dict:
    plan = generate_nutrition_plan(payload.age, payload.gender, payload.height, payload.weight, payload.activity_level, payload.goal)
    full_plan = generate_full_meal_plan(plan, num_meals=payload.num_meals, strategy=payload.strategy, dietary_preference=payload.dietary_preference)
    return {"request_id": str(uuid.uuid4()), "status": "success", "data": full_plan}


@app.get("/api/v1/nutrition/meals", dependencies=[Depends(require_api_key)])
def meals_catalog(meal_type: Optional[MealType] = None, tag: Optional[str] = Query(default=None), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)) -> dict:
    meals = [m for m in MEALS_DB if meal_type is None or m["meal_type"] == meal_type]
    enriched = []
    for meal in meals:
        item = dict(meal)
        item["tags"] = get_meal_tags(meal["name"])
        if tag is None or tag.lower() in [t.lower() for t in item["tags"]]:
            enriched.append(item)
    return {"status": "success", "count": len(enriched), "limit": limit, "offset": offset, "meals": enriched[offset: offset + limit]}


@app.get("/api/v1/nutrition/recommendations", dependencies=[Depends(require_api_key)])
def recommendations(goal: Goal, meal_type: Optional[MealType] = None, dietary_preference: str = "normal", n: int = Query(5, ge=1, le=20)) -> dict:
    meals = rank_meals_for_goal(goal, meal_type=meal_type, top_n=n, dietary_preference=dietary_preference)
    enriched = []
    for meal in meals:
        item = dict(meal)
        item["tags"] = get_meal_tags(meal["name"])
        item["substitutions"] = suggest_substitutions(meal["name"])
        enriched.append(item)
    return {"status": "success", "goal": goal, "meal_type": meal_type, "dietary_preference": dietary_preference, "meals": enriched}


@app.post("/api/v1/nutrition/substitutions", dependencies=[Depends(require_api_key)])
def substitutions(payload: SubstitutionRequest) -> dict:
    if not any(m["name"] == payload.meal_name for m in MEALS_DB):
        raise HTTPException(status_code=404, detail="Meal not found in catalog.")
    return {"status": "success", "meal_name": payload.meal_name, "tags": get_meal_tags(payload.meal_name), "substitutions": suggest_substitutions(payload.meal_name)}


@app.post("/api/v1/nutrition/validate-plan", dependencies=[Depends(require_api_key)])
def validate_existing_plan(payload: ValidatePlanRequest) -> dict:
    result = validate_plan(payload.meals, payload.plan_totals, payload.target_calories, payload.goal, payload.calorie_tolerance)
    return {"status": "success", "validation": {"passed": result.passed, "score": result.score, "issues": [i.__dict__ for i in result.issues]}}


@app.post("/api/v1/nutrition/feedback", dependencies=[Depends(require_api_key)])
def feedback(payload: FeedbackRequest) -> dict:
    if not any(m["name"] == payload.meal_name for m in MEALS_DB):
        raise HTTPException(status_code=404, detail="Meal not found in catalog.")
    record_feedback(payload.meal_name, payload.accepted)
    return {"status": "success", "message": "Feedback recorded", "meal_name": payload.meal_name, "accepted": payload.accepted}


@app.get("/api/v1/nutrition/feedback/stats", dependencies=[Depends(require_api_key)])
def feedback_stats() -> dict:
    return {"status": "success", "data": get_feedback_stats()}
