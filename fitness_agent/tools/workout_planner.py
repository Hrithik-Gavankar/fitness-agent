from ..utils.data_loader import get_workout_for_profile


def get_workout_plan(
    goal: str,
    fitness_level: str,
    equipment_access: str,
    workout_days_per_week: int,
) -> dict:
    """Generates a personalized workout plan based on user's goal, fitness level, equipment access, and available days per week.

    Args:
        goal: The fitness goal - one of 'fat_loss', 'weight_gain', 'muscle_building', 'health_maintenance'.
        fitness_level: Current fitness level - one of 'beginner', 'intermediate', 'advanced'.
        equipment_access: Equipment available - one of 'none', 'basic', 'full_gym'.
        workout_days_per_week: Number of workout days per week (3-6).

    Returns:
        A dictionary containing the day-wise workout plan with exercises, sets, reps, and rest periods.
    """
    result = get_workout_for_profile(
        goal=goal,
        fitness_level=fitness_level,
        equipment=equipment_access,
        days_per_week=workout_days_per_week,
    )
    return result
