from typing import Dict, List, Optional
from workout_database import EXERCISE_LIBRARY

GOAL_CONFIG = {
    "lose_weight": {"duration_weeks": 8, "goal_focus": "Fat Loss", "default_days": 4, "cardio_minutes": "20-30 minutes", "sets": 3, "reps": "12-15", "rest": "45-60 sec"},
    "gain_weight": {"duration_weeks": 10, "goal_focus": "Muscle Gain", "default_days": 4, "cardio_minutes": "10-15 minutes", "sets": 4, "reps": "8-12", "rest": "60-90 sec"},
    "maintain_weight": {"duration_weeks": 8, "goal_focus": "Fitness Maintenance", "default_days": 3, "cardio_minutes": "15-20 minutes", "sets": 3, "reps": "10-12", "rest": "60 sec"},
}

def _normalize_injuries(injuries: Optional[List[str]]) -> List[str]:
    injuries = injuries or []
    if "none" in injuries:
        return []
    return sorted(set(injuries))

def _activity_modifier(activity_level: str) -> Dict[str, int]:
    if activity_level == "sedentary":
        return {"days_delta": -1, "volume_delta": -1}
    if activity_level == "very_active":
        return {"days_delta": 1, "volume_delta": 1}
    return {"days_delta": 0, "volume_delta": 0}

def _is_safe(key: str, injuries: List[str], equipment: str, experience: str) -> bool:
    ex = EXERCISE_LIBRARY[key]
    return equipment in ex["equipment"] and experience in ex["level"] and not set(ex["avoid_if_injuries"]).intersection(injuries)

def _pick(pool: List[str], injuries: List[str], equipment: str, experience: str, limit: int) -> List[str]:
    out = []
    for key in pool:
        if key in EXERCISE_LIBRARY and _is_safe(key, injuries, equipment, experience):
            out.append(key)
        if len(out) >= limit:
            break
    return out

def _exercise_item(key: str, sets: int, reps: str, rest: str) -> Dict:
    ex = EXERCISE_LIBRARY[key]
    return {"id": key, "name": ex["name"], "muscle_group": ex["muscle_group"], "image_url": ex["image"], "sets": sets, "reps": reps, "rest": rest, "tips": ex["tips"]}

def _build_day(title: str, keys: List[str], cfg: Dict, volume_delta: int) -> Dict:
    sets = max(2, cfg["sets"] + volume_delta)
    return {"day_title": title, "warm_up": "5-10 minutes of light cardio and dynamic mobility.", "exercises": [_exercise_item(k, sets, cfg["reps"], cfg["rest"]) for k in keys], "cool_down": "5-10 minutes of stretching and breathing."}

def generate_workout_plan(age: int, weight_kg: float, activity_level: str, primary_goal: str, injuries: Optional[List[str]] = None, experience_level: str = "beginner", equipment: str = "gym", days_per_week: Optional[int] = None) -> Dict:
    injuries = _normalize_injuries(injuries)
    cfg = GOAL_CONFIG[primary_goal]
    mod = _activity_modifier(activity_level)
    days = days_per_week or cfg["default_days"] + mod["days_delta"]
    days = max(2, min(5, days))
    volume_delta = mod["volume_delta"] - (1 if age >= 45 else 0)

    chest = ["chest_press_machine","dumbbell_bench_press","push_up","incline_push_up","decline_push_up","incline_dumbbell_press","cable_fly"]
    back = ["seated_cable_row","machine_row","lat_pulldown","single_arm_dumbbell_row","face_pull","assisted_pull_up"]
    legs = ["leg_press","bodyweight_squat","goblet_squat","reverse_lunge","walking_lunge","step_up","hamstring_curl","leg_extension","romanian_deadlift","glute_bridge","hip_thrust","calf_raise"]
    shoulders = ["shoulder_press","lateral_raise","front_raise","rear_delt_fly","arnold_press","shrug"]
    arms = ["dumbbell_curl","hammer_curl","cable_curl","tricep_pushdown","overhead_tricep_extension","bench_dip"]
    core = ["dead_bug","bird_dog","plank","side_plank","mountain_climber","bicycle_crunch","russian_twist","hanging_knee_raise"]
    cardio = ["treadmill_walk","stationary_bike","elliptical","jumping_jacks","high_knees"]

    if equipment == "home":
        chest = ["incline_push_up","push_up","decline_push_up"]
        back = ["bird_dog"]
        legs = ["bodyweight_squat","reverse_lunge","walking_lunge","step_up","glute_bridge","calf_raise"]
        shoulders = []
        arms = ["bench_dip"]
        cardio = ["jumping_jacks","high_knees"]

    if days == 2:
        templates = [("Day 1 - Full Body A", chest[:3]+back[:3]+legs[:4]+core[:3]), ("Day 2 - Full Body B", legs[3:]+shoulders[:3]+arms[:3]+core[:3]+cardio[:2])]
    elif days == 3:
        templates = [("Day 1 - Full Body Strength", chest[:3]+back[:3]+legs[:4]+core[:2]), ("Day 2 - Lower Body & Core", legs+core[:4]), ("Day 3 - Upper Body & Cardio", chest+back+shoulders+arms[:2]+cardio[:2])]
    elif days == 4:
        templates = [("Day 1 - Upper Body", chest+back+shoulders[:3]+arms[:2]), ("Day 2 - Lower Body", legs), ("Day 3 - Core & Cardio", core+cardio), ("Day 4 - Full Body", chest[:3]+back[:3]+legs[:4]+core[:3])]
    else:
        templates = [("Day 1 - Push", chest+shoulders[:3]+arms[3:]), ("Day 2 - Legs", legs), ("Day 3 - Pull", back+arms[:3]+core[:2]), ("Day 4 - Core & Cardio", core+cardio), ("Day 5 - Full Body", chest[:3]+back[:3]+legs[:3]+shoulders[:2]+core[:2])]

    safe_defaults = _pick(["dead_bug","bird_dog","glute_bridge","treadmill_walk","stationary_bike"], injuries, equipment, experience_level, 5)
    weekly = []
    for idx, (title, pool) in enumerate(templates, start=1):
        keys = _pick(pool, injuries, equipment, experience_level, 6)
        if len(keys) < 3:
            keys = list(dict.fromkeys(keys + safe_defaults))[:5]
        weekly.append({"day_number": idx, **_build_day(title, keys, cfg, volume_delta)})

    return {
        "status": "success",
        "profile_summary": {"age": age, "weight_kg": weight_kg, "activity_level": activity_level, "primary_goal": primary_goal, "previous_injuries": injuries or ["none"], "experience_level": experience_level, "equipment": equipment},
        "plan_summary": {"duration_weeks": cfg["duration_weeks"], "days_per_week": days, "goal_focus": cfg["goal_focus"], "cardio_recommendation": cfg["cardio_minutes"], "safety_note": "This plan avoids exercises that may conflict with selected injuries. For serious injuries, consult a qualified professional."},
        "weekly_schedule": weekly
    }
