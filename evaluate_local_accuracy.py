"""Evaluate BeForma nutrition recommendation quality with 20 test profiles.

Run inside the project folder after installing requirements:
    python evaluate_local_accuracy.py

This measures recommendation/optimizer accuracy, not medical accuracy.
"""
from __future__ import annotations

import csv
import time
from statistics import mean

from main import GeneratePlanRequest, generate_plan


TEST_CASES = [
    {"label": "Lose Beginner Home Male", "name": "User1", "email": "u1@test.com", "phone": "010", "age": 24, "gender": "male", "height": 178, "weight": 82, "fitnessGoal": "lose", "activityLevel": "Sedentary", "experienceLevel": "Beginner", "workoutLocation": "Home", "dietaryPreference": "normal"},
    {"label": "Lose Active Female", "name": "User2", "email": "u2@test.com", "phone": "010", "age": 29, "gender": "female", "height": 165, "weight": 76, "fitnessGoal": "fat_loss", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Lose Vegetarian", "name": "User3", "email": "u3@test.com", "phone": "010", "age": 22, "gender": "male", "height": 175, "weight": 88, "fitnessGoal": "cutting", "activityLevel": "Lightly Active", "experienceLevel": "Beginner", "workoutLocation": "Home", "dietaryPreference": "vegetarian"},
    {"label": "Lose Vegan", "name": "User4", "email": "u4@test.com", "phone": "010", "age": 31, "gender": "female", "height": 160, "weight": 70, "fitnessGoal": "lose", "activityLevel": "Sedentary", "experienceLevel": "Beginner", "workoutLocation": "Home", "dietaryPreference": "vegan"},
    {"label": "Lose Pescatarian", "name": "User5", "email": "u5@test.com", "phone": "010", "age": 35, "gender": "male", "height": 182, "weight": 96, "fitnessGoal": "weight_loss", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "pescatarian"},

    {"label": "Maintain Male", "name": "User6", "email": "u6@test.com", "phone": "010", "age": 26, "gender": "male", "height": 176, "weight": 73, "fitnessGoal": "maintain", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Maintain Female Home", "name": "User7", "email": "u7@test.com", "phone": "010", "age": 24, "gender": "female", "height": 163, "weight": 58, "fitnessGoal": "maintenance", "activityLevel": "Lightly Active", "experienceLevel": "Beginner", "workoutLocation": "Home", "dietaryPreference": "normal"},
    {"label": "Maintain Vegetarian", "name": "User8", "email": "u8@test.com", "phone": "010", "age": 32, "gender": "male", "height": 170, "weight": 70, "fitnessGoal": "maintain", "activityLevel": "Very Active", "experienceLevel": "Advanced", "workoutLocation": "Gym", "dietaryPreference": "vegetarian"},
    {"label": "Maintain Dairy Free", "name": "User9", "email": "u9@test.com", "phone": "010", "age": 28, "gender": "female", "height": 168, "weight": 64, "fitnessGoal": "stable", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "dairy_free"},
    {"label": "Maintain Gluten Free", "name": "User10", "email": "u10@test.com", "phone": "010", "age": 38, "gender": "male", "height": 180, "weight": 80, "fitnessGoal": "maintain", "activityLevel": "Lightly Active", "experienceLevel": "Beginner", "workoutLocation": "Home", "dietaryPreference": "gluten_free"},

    {"label": "Gain Beginner", "name": "User11", "email": "u11@test.com", "phone": "010", "age": 21, "gender": "male", "height": 180, "weight": 66, "fitnessGoal": "gain", "activityLevel": "Lightly Active", "experienceLevel": "Beginner", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Gain Intermediate Gym", "name": "User12", "email": "u12@test.com", "phone": "010", "age": 25, "gender": "male", "height": 178, "weight": 72, "fitnessGoal": "muscle_gain", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Bulk Very Active", "name": "User13", "email": "u13@test.com", "phone": "010", "age": 27, "gender": "male", "height": 185, "weight": 78, "fitnessGoal": "bulk", "activityLevel": "Very Active", "experienceLevel": "Advanced", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Bulk Athlete", "name": "User14", "email": "u14@test.com", "phone": "010", "age": 23, "gender": "male", "height": 188, "weight": 82, "fitnessGoal": "bulking", "activityLevel": "Super Active", "experienceLevel": "Advanced", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Gain Vegetarian", "name": "User15", "email": "u15@test.com", "phone": "010", "age": 24, "gender": "female", "height": 170, "weight": 55, "fitnessGoal": "gain", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "vegetarian"},
    {"label": "Gain Vegan", "name": "User16", "email": "u16@test.com", "phone": "010", "age": 30, "gender": "male", "height": 177, "weight": 68, "fitnessGoal": "gain", "activityLevel": "Very Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "vegan"},
    {"label": "Gain Pescatarian", "name": "User17", "email": "u17@test.com", "phone": "010", "age": 33, "gender": "female", "height": 166, "weight": 59, "fitnessGoal": "muscle_gain", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "pescatarian"},
    {"label": "Gain Home Beginner", "name": "User18", "email": "u18@test.com", "phone": "010", "age": 19, "gender": "male", "height": 172, "weight": 60, "fitnessGoal": "build_muscle", "activityLevel": "Sedentary", "experienceLevel": "Beginner", "workoutLocation": "Home", "dietaryPreference": "normal"},
    {"label": "Bulk Female Active", "name": "User19", "email": "u19@test.com", "phone": "010", "age": 26, "gender": "female", "height": 168, "weight": 62, "fitnessGoal": "bulk", "activityLevel": "Very Active", "experienceLevel": "Advanced", "workoutLocation": "Gym", "dietaryPreference": "normal"},
    {"label": "Gain Dairy Free", "name": "User20", "email": "u20@test.com", "phone": "010", "age": 29, "gender": "male", "height": 181, "weight": 74, "fitnessGoal": "gain", "activityLevel": "Moderately Active", "experienceLevel": "Intermediate", "workoutLocation": "Gym", "dietaryPreference": "dairy_free"},
]


def pct_accuracy(actual: float, target: float) -> float:
    return max(0.0, 100.0 - abs(actual - target) / max(target, 1) * 100.0)


def evaluate_case(case: dict) -> dict:
    label = case.pop("label")
    start = time.perf_counter()
    response = generate_plan(GeneratePlanRequest(**case))
    elapsed_ms = (time.perf_counter() - start) * 1000

    targets = response["macros"]
    meals = response["recommendations"]["diet_plan"]
    totals = {
        "calories": sum(m["calories"] for m in meals),
        "protein_grams": sum(m["protein"] for m in meals),
        "carbs_grams": sum(m["carbs"] for m in meals),
        "fat_grams": sum(m["fat"] for m in meals),
    }

    cal_acc = pct_accuracy(totals["calories"], response["daily_calorie_target"])
    p_acc = pct_accuracy(totals["protein_grams"], targets["protein_grams"])
    c_acc = pct_accuracy(totals["carbs_grams"], targets["carbs_grams"])
    f_acc = pct_accuracy(totals["fat_grams"], targets["fat_grams"])
    overall = (cal_acc + p_acc + c_acc + f_acc) / 4
    images = sum(1 for m in meals if m.get("image")) / max(len(meals), 1) * 100
    sources = [m.get("protein_source") for m in meals]
    unique_source_score = len(set(sources)) / max(len(sources), 1) * 100
    validation_passed = response["plan_quality"]["validation"]["passed"]
    usefulness = (overall * 0.55) + (images * 0.15) + (unique_source_score * 0.15) + ((100 if validation_passed else 65) * 0.15)

    return {
        "label": label,
        "goal": response["meta"]["normalized_goal"],
        "num_meals": response["meta"].get("num_meals"),
        "calorie_accuracy": round(cal_acc, 2),
        "protein_accuracy": round(p_acc, 2),
        "carbs_accuracy": round(c_acc, 2),
        "fat_accuracy": round(f_acc, 2),
        "overall_macro_accuracy": round(overall, 2),
        "image_coverage": round(images, 2),
        "protein_source_diversity": round(unique_source_score, 2),
        "validation_passed": validation_passed,
        "response_time_ms": round(elapsed_ms, 1),
        "usefulness_score": round(usefulness, 2),
        "meals": " | ".join(m["name"] for m in meals),
    }


def main() -> None:
    rows = [evaluate_case(dict(case)) for case in TEST_CASES]
    passed = sum(1 for r in rows if r["validation_passed"])
    print("\n========== BeForma Nutrition Model Evaluation V3 ==========")
    print(f"Test cases: {len(rows)}")
    print(f"Validation pass rate: {passed}/{len(rows)}")
    print(f"Average calorie accuracy: {mean(r['calorie_accuracy'] for r in rows):.2f}%")
    print(f"Average overall macro accuracy: {mean(r['overall_macro_accuracy'] for r in rows):.2f}%")
    print(f"Average image coverage: {mean(r['image_coverage'] for r in rows):.1f}%")
    print(f"Protein-source diversity: {mean(r['protein_source_diversity'] for r in rows):.2f}%")
    print(f"Average response time: {mean(r['response_time_ms'] for r in rows):.1f} ms")
    print(f"Client usefulness score: {mean(r['usefulness_score'] for r in rows):.2f}/100")

    verdict = "EXCELLENT" if mean(r['usefulness_score'] for r in rows) >= 90 else "GOOD" if mean(r['usefulness_score'] for r in rows) >= 80 else "NEEDS IMPROVEMENT"
    print(f"Verdict: {verdict}")

    out = "accuracy_report_v3.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved detailed report to: {out}")

    for r in rows:
        print(f"- {r['label']}: meals={r['num_meals']}, overall={r['overall_macro_accuracy']}%, calories={r['calorie_accuracy']}%, diversity={r['protein_source_diversity']}%, meals={r['meals']}")


if __name__ == "__main__":
    main()
