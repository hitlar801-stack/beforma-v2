# BeForma Nutrition API — Final Railway Project

## Main endpoint for backend / Flutter

```http
POST /generate-plan
```

This endpoint is public and does not require an API key.

### Request body

```json
{
  "age": 24,
  "gender": "male",
  "height": 178,
  "weight": 82,
  "fitnessGoal": "lose",
  "activityLevel": "Sedentary",
  "experienceLevel": "Beginner",
  "workoutLocation": "Home",
  "dietaryPreference": "normal"
}
```

### Response includes

- BMI
- BMI category
- daily calorie target
- protein/carbs/fat macros
- 3 meals: breakfast, lunch, dinner
- image URL for every meal
- meal ingredients with gram quantities
- quality / macro accuracy score
- workout plan placeholder based on goal, level and location

## Meal database

`meals_db.py` contains 360 meals:

- 120 breakfast meals
- 120 lunch meals
- 120 dinner meals

Every meal has:

- calories
- protein
- carbs
- fat
- protein_source
- dietary_tags
- items with grams
- image URL

## Accuracy improvements

The new selector uses:

- goal-aware macro ratios
- beam search over 360 meals
- dietary preference filtering
- protein-source diversity penalty
- portion optimization
- validation scoring

The returned `plan_quality.accuracy.macro_error_pct` is macro matching accuracy, not medical accuracy.

## Railway deployment

1. Put all files in the root of your GitHub repo.
2. Railway → New Project → Deploy from GitHub Repo.
3. Add PostgreSQL if you want DB saving.
4. In API Service → Variables, add:

```env
ALLOWED_ORIGINS=*
INIT_DB_ON_STARTUP=true
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

5. Generate public domain from Service → Settings → Networking.

## Test URLs

```text
https://YOUR-DOMAIN.up.railway.app/health
https://YOUR-DOMAIN.up.railway.app/docs
```

## Endpoint to hand off

```text
POST https://YOUR-DOMAIN.up.railway.app/generate-plan
```
