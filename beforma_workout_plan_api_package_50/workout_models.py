from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

ActivityLevel = Literal["sedentary", "lightly_active", "moderately_active", "very_active"]
PrimaryGoal = Literal["lose_weight", "gain_weight", "maintain_weight"]
Injury = Literal["none", "lower_back", "knee", "shoulder", "neck", "ankle", "wrist", "elbow"]
ExperienceLevel = Literal["beginner", "intermediate", "advanced"]
Equipment = Literal["home", "gym"]

class WorkoutPlanRequest(BaseModel):
    age: int = Field(..., ge=12, le=80)
    weight_kg: float = Field(..., ge=30, le=250)
    activity_level: ActivityLevel
    primary_goal: PrimaryGoal
    injuries: List[Injury] = Field(default_factory=lambda: ["none"])
    experience_level: ExperienceLevel = "beginner"
    equipment: Equipment = "gym"
    days_per_week: Optional[int] = Field(default=None, ge=2, le=5)

    @field_validator("injuries")
    @classmethod
    def normalize_injuries(cls, values):
        if not values:
            return ["none"]
        if "none" in values and len(values) > 1:
            return [v for v in values if v != "none"]
        return values
