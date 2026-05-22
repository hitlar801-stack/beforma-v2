FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY beforma_workout_plan_api_package_50/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY beforma_workout_plan_api_package_50/ .

CMD sh -c "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"