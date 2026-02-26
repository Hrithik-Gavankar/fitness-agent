import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filepath: Path) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


def load_workout_data(goal: str) -> dict:
    filepath = DATA_DIR / "workouts" / f"{goal}.json"
    if not filepath.exists():
        return {"error": f"No workout data found for goal: {goal}"}
    return _load_json(filepath)


def load_diet_data(goal: str) -> dict:
    filepath = DATA_DIR / "diet_plans" / f"{goal}.json"
    if not filepath.exists():
        return {"error": f"No diet data found for goal: {goal}"}
    return _load_json(filepath)


def load_youtube_data(goal: str) -> dict:
    filepath = DATA_DIR / "youtube_videos" / f"{goal}.json"
    if not filepath.exists():
        return {"error": f"No youtube data found for goal: {goal}"}
    return _load_json(filepath)


def get_workout_for_profile(
    goal: str, fitness_level: str, equipment: str, days_per_week: int
) -> dict:
    data = load_workout_data(goal)
    if "error" in data:
        return data

    level_data = data.get("levels", {}).get(fitness_level)
    if not level_data:
        return {"error": f"No data for fitness level: {fitness_level}"}

    equipment_data = level_data.get("equipment", {}).get(equipment)
    if not equipment_data:
        available = list(level_data.get("equipment", {}).keys())
        equipment_data = level_data.get("equipment", {}).get(
            available[0] if available else ""
        )
        if not equipment_data:
            return {"error": f"No equipment data found"}

    days = equipment_data.get("days", [])
    if len(days) > days_per_week:
        days = days[:days_per_week]

    return {
        "goal": goal,
        "fitness_level": fitness_level,
        "equipment": equipment,
        "days_per_week": len(days),
        "workout_plan": days,
    }


def get_diet_for_profile(
    goal: str, diet_preference: str, cuisine: str
) -> dict:
    data = load_diet_data(goal)
    if "error" in data:
        return data

    diet_data = data.get("diet_types", {}).get(diet_preference)
    if not diet_data:
        return {"error": f"No data for diet preference: {diet_preference}"}

    cuisine_data = diet_data.get("cuisines", {}).get(cuisine)
    if not cuisine_data:
        if cuisine == "flexible":
            for c in ["indian", "western"]:
                cuisine_data = diet_data.get("cuisines", {}).get(c)
                if cuisine_data:
                    break
        if not cuisine_data:
            return {"error": f"No data for cuisine: {cuisine}"}

    return {
        "goal": goal,
        "diet_preference": diet_preference,
        "cuisine": cuisine,
        "meals": cuisine_data.get("meals", {}),
    }


def get_videos_for_profile(
    goal: str, fitness_level: str, content_type: str = "both"
) -> dict:
    data = load_youtube_data(goal)
    if "error" in data:
        return data

    videos = data.get("videos", [])

    filtered = [
        v for v in videos
        if v.get("level", "") in [fitness_level, "all"]
        and (content_type == "both" or v.get("type", "") == content_type)
    ]

    if not filtered:
        filtered = videos[:5]

    return {
        "goal": goal,
        "fitness_level": fitness_level,
        "content_type": content_type,
        "videos": filtered,
    }
