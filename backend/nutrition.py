"""
Maps a food label -> estimated calories/macros for one standard serving.

For the MVP this uses a local reference table covering common Food-101
classes, checked against a DB cache first. To go further, swap
`_lookup_local` for a real call to Edamam's Nutrition API or USDA
FoodData Central and keep everything else (the cache-first logic) the same.
"""
from sqlalchemy.orm import Session
import models

# A representative subset of Food-101 classes with approximate per-serving values.
# Extend this as needed — it's deliberately small for the MVP.
_REFERENCE_TABLE = {
    "pizza":            {"calories": 285, "protein_g": 12, "carbs_g": 36, "fat_g": 10},
    "hamburger":         {"calories": 354, "protein_g": 17, "carbs_g": 29, "fat_g": 20},
    "sushi":             {"calories": 200, "protein_g": 9,  "carbs_g": 30, "fat_g": 4},
    "salad":             {"calories": 152, "protein_g": 5,  "carbs_g": 12, "fat_g": 10},
    "french_fries":      {"calories": 365, "protein_g": 4,  "carbs_g": 48, "fat_g": 17},
    "ice_cream":         {"calories": 273, "protein_g": 5,  "carbs_g": 31, "fat_g": 15},
    "steak":             {"calories": 271, "protein_g": 26, "carbs_g": 0,  "fat_g": 18},
    "fried_rice":        {"calories": 333, "protein_g": 8,  "carbs_g": 45, "fat_g": 13},
    "pancakes":          {"calories": 227, "protein_g": 6,  "carbs_g": 28, "fat_g": 10},
    "donuts":            {"calories": 253, "protein_g": 3,  "carbs_g": 31, "fat_g": 14},
    "chicken_curry":     {"calories": 240, "protein_g": 20, "carbs_g": 10, "fat_g": 14},
    "omelette":          {"calories": 154, "protein_g": 11, "carbs_g": 1,  "fat_g": 12},
    "spaghetti_bolognese": {"calories": 344, "protein_g": 16, "carbs_g": 42, "fat_g": 12},
    "waffles":           {"calories": 291, "protein_g": 7,  "carbs_g": 33, "fat_g": 14},
    "sandwich":          {"calories": 250, "protein_g": 12, "carbs_g": 30, "fat_g": 9},
}

_DEFAULT = {"calories": 250, "protein_g": 10, "carbs_g": 25, "fat_g": 10}


def _lookup_local(food_label: str) -> dict:
    return _REFERENCE_TABLE.get(food_label, _DEFAULT)


def get_nutrition(db: Session, food_label: str) -> dict:
    """Cache-first lookup: check the DB cache, else fall back to the local table."""
    cached = (
        db.query(models.NutritionCache)
        .filter(models.NutritionCache.food_label == food_label)
        .first()
    )
    if cached:
        return {
            "calories": cached.calories_per_serving,
            "protein_g": cached.protein_g,
            "carbs_g": cached.carbs_g,
            "fat_g": cached.fat_g,
        }

    values = _lookup_local(food_label)

    # Populate the cache so future lookups (and a real API swap-in) are cheap.
    entry = models.NutritionCache(
        food_label=food_label,
        calories_per_serving=values["calories"],
        protein_g=values["protein_g"],
        carbs_g=values["carbs_g"],
        fat_g=values["fat_g"],
    )
    db.merge(entry)
    db.commit()

    return values
