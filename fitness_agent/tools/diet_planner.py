from ..utils.data_loader import get_diet_for_profile
from ..utils.calculations import calculate_bmi, calculate_tdee, calculate_macros


def get_diet_plan(
    goal: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    diet_preference: str,
    cuisine_preference: str,
    workout_days_per_week: int,
    gender: str = "male",
) -> dict:
    """Generates a personalized diet plan with calorie targets, macro breakdown, and meal suggestions.

    Args:
        goal: The fitness goal - one of 'fat_loss', 'weight_gain', 'muscle_building', 'health_maintenance'.
        weight_kg: User's weight in kilograms.
        height_cm: User's height in centimeters.
        age: User's age in years.
        diet_preference: Diet type - one of 'vegetarian', 'non_vegetarian', 'vegan', 'eggetarian'.
        cuisine_preference: Cuisine type - one of 'indian', 'western', 'flexible'.
        workout_days_per_week: Number of workout days per week (3-6).
        gender: User's gender for BMR calculation - 'male' or 'female'. Defaults to 'male'.

    Returns:
        A dictionary containing BMI, calorie targets, macro breakdown, and meal suggestions.
    """
    bmi_info = calculate_bmi(weight_kg, height_cm)
    tdee_info = calculate_tdee(weight_kg, height_cm, age, workout_days_per_week, goal, gender)
    macro_info = calculate_macros(tdee_info["target_calories"], goal)
    meals = get_diet_for_profile(goal, diet_preference, cuisine_preference)

    return {
        "bmi": bmi_info,
        "calories": tdee_info,
        "macros": macro_info,
        "meal_plan": meals,
    }
