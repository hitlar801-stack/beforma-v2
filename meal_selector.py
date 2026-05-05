"""Improved meal selector using beam search, dietary filters and macro scoring."""
from __future__ import annotations
import random
from collections import defaultdict
from typing import Optional

from meals_db import MEALS_DB, MealRecord

GOAL_MACRO_RATIOS: dict[str, dict[str, float]] = {
    "lose": {"protein": 0.40, "carbs": 0.35, "fat": 0.25},
    "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    "gain": {"protein": 0.30, "carbs": 0.50, "fat": 0.20},
}

MEAL_TYPE_PLANS: dict[int, list[str]] = {
    3: ["breakfast", "lunch", "dinner"],
}

MEAL_CALORIE_SHARE: dict[str, float] = {"breakfast": 0.25, "lunch": 0.40, "dinner": 0.35}


def normalize_preference(value: Optional[str]) -> str:
    if not value:
        return "normal"
    v = value.strip().lower().replace("_", " ").replace("-", " ")
    mapping = {
        "none": "normal", "all": "normal", "balanced": "normal", "normal": "normal",
        "vegetarian": "vegetarian", "vegan": "vegan", "pescatarian": "pescatarian",
        "keto": "low_carb", "low carb": "low_carb", "high protein": "high_protein",
        "dairy free": "dairy_free", "gluten free": "gluten_free",
    }
    return mapping.get(v, v.replace(" ", "_"))


def meal_allowed(meal: MealRecord, dietary_preference: Optional[str]) -> bool:
    pref = normalize_preference(dietary_preference)
    if pref == "normal":
        return True
    tags = set(meal.get("dietary_tags", []))
    if pref == "pescatarian":
        # Vegetarian meals are also okay for pescatarian users.
        return "pescatarian" in tags or "vegetarian" in tags or "vegan" in tags
    return pref in tags


def _eval_combination(comb: list[MealRecord], target_calories: float, target_p: float, target_c: float, target_f: float, strategy: str) -> float:
    if not comb:
        return 0.0
    share = sum(MEAL_CALORIE_SHARE.get(m["meal_type"], 0.33) for m in comb)
    tc, tp, tcb, tf = max(target_calories * share, 1), max(target_p * share, 1), max(target_c * share, 1), max(target_f * share, 1)
    cal = sum(m["calories"] for m in comb)
    p = sum(m["protein"] for m in comb)
    carbs = sum(m["carbs"] for m in comb)
    fat = sum(m["fat"] for m in comb)
    error = (
        abs(cal - tc) / tc
        + 2.2 * abs(p - tp) / tp
        + abs(carbs - tcb) / tcb
        + abs(fat - tf) / tf
    )
    sources = [m.get("protein_source", m["name"]) for m in comb]
    duplicate_sources = len(sources) - len(set(sources))
    error += duplicate_sources * 0.35
    if any(not m.get("image") for m in comb):
        error += 0.2
    fitness = -error
    if strategy == "flexible":
        fitness += random.uniform(-0.04, 0.04)
    return fitness


def select_meals(num_meals: int, daily_calories: float, goal: str, strategy: str = "strict", dietary_preference: Optional[str] = None, seed: Optional[int] = None) -> list[dict]:
    if seed is not None:
        random.seed(seed)
    meal_types = MEAL_TYPE_PLANS.get(num_meals, MEAL_TYPE_PLANS[3])
    ratios = GOAL_MACRO_RATIOS[goal]
    target_p = (daily_calories * ratios["protein"]) / 4
    target_c = (daily_calories * ratios["carbs"]) / 4
    target_f = (daily_calories * ratios["fat"]) / 9

    pool: dict[str, list[MealRecord]] = defaultdict(list)
    for meal in MEALS_DB:
        if meal_allowed(meal, dietary_preference):
            pool[meal["meal_type"]].append(meal)

    # Fallback if preference is too strict.
    if any(len(pool.get(slot, [])) < 5 for slot in meal_types):
        pool = defaultdict(list)
        for meal in MEALS_DB:
            pool[meal["meal_type"]].append(meal)

    beams: list[list[MealRecord]] = [[]]
    beam_width = 55 if strategy == "strict" else 75
    for slot in meal_types:
        candidates = pool.get(slot, [])
        if not candidates:
            continue
        new_beams: list[tuple[float, list[MealRecord]]] = []
        for beam in beams:
            used_names = {m["name"] for m in beam}
            for meal in candidates:
                if meal["name"] in used_names:
                    continue
                candidate = beam + [meal]
                score = _eval_combination(candidate, daily_calories, target_p, target_c, target_f, strategy)
                new_beams.append((score, candidate))
        new_beams.sort(key=lambda x: x[0], reverse=True)
        beams = [b for _, b in new_beams[:beam_width]]
    return [dict(m) for m in (beams[0] if beams else [])]
