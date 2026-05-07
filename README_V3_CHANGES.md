# BeForma Nutrition V3 — Gain/Bulk Accuracy Fix

## Main objective
This update improves the nutrition recommendation engine after the initial Railway deployment.

## What changed

### 1. More high-calorie meals for gain/bulk
Updated `meals_db.py`:
- Added high-calorie bulking breakfasts.
- Added high-calorie bulking lunches.
- Added high-calorie bulking dinners.
- Added high-protein, high-calorie snacks.
- Added extra dairy-free and vegan snack alternatives.
- Every added meal includes an image URL.

### 2. Gain/bulk now uses 4 or 5 meals instead of 3
Updated `main.py`:
- `POST /generate-plan` now automatically chooses meal count.
- Lose/maintain users get 3 meals.
- Gain/bulk beginner or low-activity users get 4 meals.
- Gain/bulk active/intermediate/advanced users get 5 meals.

### 3. Reduced repeated protein sources
Updated `meal_selector.py`:
- Stronger penalty for repeated protein source.
- Bonus for new protein source.
- Better meal family diversity.
- Larger beam search for gain/bulk cases.

### 4. Added snacks support
Updated `meal_selector.py`, `main.py`, and `meals_db.py`:
- Added `snack` meal type.
- Added 4-meal and 5-meal meal type plans.
- Added calorie share distribution for snacks.

### 5. Stronger evaluation
Added `evaluate_local_accuracy.py`:
- Increased test cases from 5 to 20.
- Covers lose, maintain, gain, bulk, vegan, vegetarian, pescatarian, dairy-free, and gluten-free cases.
- Reports calorie accuracy, macro accuracy, image coverage, protein-source diversity, validation pass rate, response time, and usefulness score.

## Latest local evaluation result

- Test cases: 20
- Validation pass rate: 20/20
- Average calorie accuracy: 98.26%
- Average overall macro accuracy: 93.91%
- Average image coverage: 100.0%
- Protein-source diversity: 99.00%
- Average response time: 310.2 ms
- Client usefulness score: 96.50/100
- Verdict: EXCELLENT

## Files changed

- `main.py`
- `meal_selector.py`
- `meals_db.py`
- `evaluate_local_accuracy.py`
- `README_V3_CHANGES.md`

## Deploy

Replace the files above in the GitHub repo, commit, push, then redeploy on Railway.

```bash
git add main.py meal_selector.py meals_db.py evaluate_local_accuracy.py README_V3_CHANGES.md
git commit -m "Improve gain bulk meal accuracy and evaluation"
git push
```

Railway should auto-deploy the latest commit.
