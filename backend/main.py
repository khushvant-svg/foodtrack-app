import os
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas
from database import engine, get_db
from auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from ml_inference import classifier
from nutrition import get_nutrition

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FoodTrack API")

# Allow the Vite dev server locally, plus your deployed frontend URL in production.
# Set FRONTEND_URL on your hosting platform, e.g. https://foodtrack.vercel.app
_allowed_origins = ["http://localhost:5173"]
if os.environ.get("FRONTEND_URL"):
    _allowed_origins.append(os.environ["FRONTEND_URL"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Auth ----------

@app.post("/auth/signup", response_model=schemas.UserOut, status_code=201)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses "username" as the field name — we treat it as email.
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.patch("/auth/me/goal", response_model=schemas.UserOut)
def update_goal(
    payload: schemas.GoalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user.daily_calorie_goal = payload.daily_calorie_goal
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------- Prediction ----------

@app.post("/predict", response_model=schemas.PredictionResult)
async def predict_food(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(status_code=400, detail="Please upload a JPEG or PNG image")

    image_bytes = await file.read()
    result = classifier.predict(image_bytes)
    nutrition = get_nutrition(db, result["top_prediction"])

    return schemas.PredictionResult(
        top_prediction=result["top_prediction"],
        confidence=result["confidence"],
        alternatives=result["alternatives"],
        calories=nutrition["calories"],
        protein_g=nutrition["protein_g"],
        carbs_g=nutrition["carbs_g"],
        fat_g=nutrition["fat_g"],
    )


# ---------- Meal logging ----------

@app.post("/meals", response_model=schemas.MealLogOut, status_code=201)
def log_meal(
    payload: schemas.MealLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    meal = models.MealLog(
        user_id=current_user.id,
        food_label=payload.food_label,
        confirmed_label=payload.confirmed_label,
        calories=payload.calories,
        protein_g=payload.protein_g,
        carbs_g=payload.carbs_g,
        fat_g=payload.fat_g,
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


@app.get("/meals/today", response_model=list[schemas.MealLogOut])
def get_todays_meals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    return (
        db.query(models.MealLog)
        .filter(
            models.MealLog.user_id == current_user.id,
            func.date(models.MealLog.logged_at) == str(today),
        )
        .order_by(models.MealLog.logged_at.desc())
        .all()
    )


@app.get("/meals", response_model=list[schemas.MealLogOut])
def get_all_meals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.MealLog)
        .filter(models.MealLog.user_id == current_user.id)
        .order_by(models.MealLog.logged_at.desc())
        .limit(100)
        .all()
    )


@app.get("/")
def health_check():
    return {"status": "ok", "model_trained": classifier.is_trained}
