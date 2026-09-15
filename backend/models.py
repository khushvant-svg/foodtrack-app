from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    daily_calorie_goal = Column(Integer, default=2000)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meal_logs = relationship("MealLog", back_populates="user")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    food_label = Column(String, nullable=False)       # model's top prediction
    confirmed_label = Column(String, nullable=True)    # set if user corrects it
    image_path = Column(String, nullable=True)

    calories = Column(Float, default=0)
    protein_g = Column(Float, default=0)
    carbs_g = Column(Float, default=0)
    fat_g = Column(Float, default=0)

    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="meal_logs")


class NutritionCache(Base):
    """Avoids re-hitting a nutrition API/lookup for the same food repeatedly."""
    __tablename__ = "nutrition_cache"

    food_label = Column(String, primary_key=True)
    calories_per_serving = Column(Float)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
