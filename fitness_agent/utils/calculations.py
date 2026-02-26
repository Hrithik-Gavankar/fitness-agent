def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return {"bmi": bmi, "category": category}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str = "male") -> float:
    """Mifflin-St Jeor equation."""
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "male":
        bmr += 5
    else:
        bmr -= 161
    return round(bmr, 0)


ACTIVITY_MULTIPLIERS = {
    3: 1.375,
    4: 1.465,
    5: 1.55,
    6: 1.725,
}

GOAL_CALORIE_ADJUSTMENTS = {
    "fat_loss": -500,
    "weight_gain": 400,
    "muscle_building": 300,
    "health_maintenance": 0,
}

MACRO_SPLITS = {
    "fat_loss": {"protein": 0.40, "carbs": 0.30, "fat": 0.30},
    "weight_gain": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
    "muscle_building": {"protein": 0.35, "carbs": 0.40, "fat": 0.25},
    "health_maintenance": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
}


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    workout_days: int,
    goal: str,
    gender: str = "male",
) -> dict:
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    multiplier = ACTIVITY_MULTIPLIERS.get(workout_days, 1.55)
    maintenance = round(bmr * multiplier, 0)
    adjustment = GOAL_CALORIE_ADJUSTMENTS.get(goal, 0)
    target = round(maintenance + adjustment, 0)

    return {
        "bmr": bmr,
        "maintenance_calories": maintenance,
        "target_calories": target,
        "adjustment": adjustment,
    }


def calculate_macros(target_calories: float, goal: str) -> dict:
    split = MACRO_SPLITS.get(goal, MACRO_SPLITS["health_maintenance"])
    protein_cal = target_calories * split["protein"]
    carbs_cal = target_calories * split["carbs"]
    fat_cal = target_calories * split["fat"]

    return {
        "protein_g": round(protein_cal / 4, 0),
        "carbs_g": round(carbs_cal / 4, 0),
        "fat_g": round(fat_cal / 9, 0),
        "split_percentages": {
            "protein": int(split["protein"] * 100),
            "carbs": int(split["carbs"] * 100),
            "fat": int(split["fat"] * 100),
        },
    }
