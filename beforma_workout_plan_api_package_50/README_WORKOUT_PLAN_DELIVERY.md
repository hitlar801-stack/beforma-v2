# BeForma Workout Plan API - 50 Exercises

This is an independent workout-plan generator. It does not include nutrition logic and does not include camera exercise recognition.

## Main endpoint

POST /api/v1/workout/generate-plan

## Inputs

- age
- weight_kg
- activity_level: sedentary, lightly_active, moderately_active, very_active
- primary_goal: lose_weight, gain_weight, maintain_weight
- injuries: none, lower_back, knee, shoulder, neck, ankle, wrist, elbow
- experience_level: beginner, intermediate, advanced
- equipment: home, gym
- days_per_week: 2 to 5

## Output

Each exercise returns:
- id
- English name
- muscle_group
- image_url
- sets
- reps
- rest
- tips

## Local run

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Open:
http://127.0.0.1:8000/docs

## Railway

Deploy this folder as an independent service. Do not mix it with nutrition API or exercise-recognition API.
