from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    daily_calorie_goal: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictionResult(BaseModel):
    """Returned right after a photo is analyzed, before the user confirms it."""
    top_prediction: str
    confidence: float
    alternatives: list[str]  # shown if confidence is low
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class MealLogCreate(BaseModel):
    food_label: str
    confirmed_label: Optional[str] = None
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class MealLogOut(BaseModel):
    id: int
    food_label: str
    confirmed_label: Optional[str]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    logged_at: datetime

    class Config:
        from_attributes = True


class GoalUpdate(BaseModel):
    daily_calorie_goal: int
