from enum import Enum
from pydantic import BaseModel, Field


class Goal(str, Enum):
    FAT_LOSS = "fat_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_BUILDING = "muscle_building"
    HEALTH_MAINTENANCE = "health_maintenance"


class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DietPreference(str, Enum):
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non_vegetarian"
    VEGAN = "vegan"
    EGGETARIAN = "eggetarian"


class CuisinePreference(str, Enum):
    INDIAN = "indian"
    WESTERN = "western"
    FLEXIBLE = "flexible"


class EquipmentAccess(str, Enum):
    NONE = "none"
    BASIC = "basic"
    FULL_GYM = "full_gym"


class UserProfile(BaseModel):
    name: str
    age: int = Field(ge=14, le=80)
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    goal: Goal
    fitness_level: FitnessLevel
    diet_preference: DietPreference
    cuisine_preference: CuisinePreference
    workout_days_per_week: int = Field(ge=3, le=6)
    equipment_access: EquipmentAccess


class Exercise(BaseModel):
    name: str
    sets: int
    reps: str
    rest_sec: int
    muscle_group: str
    equipment: str


class WorkoutDay(BaseModel):
    day: int
    name: str
    focus: str
    exercises: list[Exercise]


class DietMeal(BaseModel):
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    ingredients: list[str]
    prep_time_min: int


class YouTubeVideo(BaseModel):
    title: str
    url: str
    type: str
    level: str
    duration_min: int
    tags: list[str]
    description: str
