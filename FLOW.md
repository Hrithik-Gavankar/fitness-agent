# Fitness Agent - Architecture & Flow Document

## Overview

An AI-powered fitness agent built with **Google ADK (Agent Development Kit)** that provides personalized workout plans, diet plans, and YouTube video recommendations through a conversational interface.

---

## 1. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Google ADK Agent                        │
│                    (Gemini 2.0 Flash)                         │
│                                                              │
│  System Prompt: Fitness coach persona with onboarding logic  │
├──────────────────────────────────────────────────────────────┤
│                         TOOLS                                │
│                                                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Workout      │  │  Diet Planner   │  │  YouTube       │  │
│  │  Planner      │  │                 │  │  Recommender   │  │
│  └──────┬───────┘  └──────┬──────────┘  └──────┬─────────┘  │
│         │                  │                     │            │
├─────────┴──────────────────┴─────────────────────┴───────────┤
│                      DATA LAYER                              │
│                                                              │
│  data/workouts/     data/diet_plans/     data/youtube_videos/│
│  ├── fat_loss.json  ├── fat_loss.json    ├── fat_loss.json   │
│  ├── muscle_...     ├── muscle_...       ├── muscle_...      │
│  ├── weight_...     ├── weight_...       ├── weight_...      │
│  └── health_...     └── health_...       └── health_...      │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. User Onboarding Flow

The agent collects user information conversationally during the first interaction.

### Data Collected

| Field             | Type     | Options / Range                                        |
|-------------------|----------|--------------------------------------------------------|
| Name              | string   | Free text                                              |
| Age               | int      | 14-80                                                  |
| Weight            | float    | In kg                                                  |
| Height            | float    | In cm                                                  |
| Goal              | enum     | `fat_loss`, `weight_gain`, `muscle_building`, `health_maintenance` |
| Fitness Level     | enum     | `beginner`, `intermediate`, `advanced`                 |
| Diet Preference   | enum     | `vegetarian`, `non_vegetarian`, `vegan`, `eggetarian`  |
| Cuisine Preference| enum     | `indian`, `western`, `flexible`                        |
| Workout Days/Week | int      | 3-6                                                    |
| Equipment Access  | enum     | `none` (home), `basic` (dumbbells/bands), `full` (gym) |

### Onboarding Conversation Example

```
Agent: Hey! I'm your fitness coach. Let's set up your profile.
       What's your name?
User:  Hrithik

Agent: Nice to meet you, Hrithik! How old are you?
User:  25

Agent: What's your current weight (in kg)?
User:  75

Agent: And height (in cm)?
User:  178

Agent: What's your primary fitness goal?
       1. Fat Loss
       2. Weight Gain
       3. Muscle Building
       4. Health Maintenance
User:  Muscle Building

Agent: What's your current fitness level?
       1. Beginner (new to working out)
       2. Intermediate (6+ months consistent)
       3. Advanced (2+ years serious training)
User:  Intermediate

Agent: Any diet preferences?
       1. Vegetarian
       2. Non-Vegetarian
       3. Vegan
       4. Eggetarian
User:  Non-Vegetarian

Agent: Cuisine preference?
       1. Indian
       2. Western
       3. Flexible (mix of both)
User:  Indian

Agent: How many days per week can you work out?
User:  5

Agent: Do you have access to equipment?
       1. None (home workouts only)
       2. Basic (dumbbells, resistance bands)
       3. Full gym access
User:  Full gym access

Agent: You're all set! Here's your profile:
       Name: Hrithik | Age: 25 | Weight: 75kg | Height: 178cm
       Goal: Muscle Building | Level: Intermediate
       Diet: Non-Veg Indian | Workout: 5 days/week | Equipment: Full Gym

       Would you like a workout plan, diet plan, or both?
```

---

## 3. Fitness Level Derivation

The agent uses a combination of user-reported level and BMI to contextualize recommendations:

```
BMI = weight / (height_in_m ^ 2)

Underweight:  BMI < 18.5
Normal:       18.5 <= BMI < 25
Overweight:   25 <= BMI < 30
Obese:        BMI >= 30
```

### TDEE Calculation (for diet plans)

```
BMR (Mifflin-St Jeor):
  Male:   10 * weight(kg) + 6.25 * height(cm) - 5 * age - 161 + 5 + 161 = 10w + 6.25h - 5a + 5
  Female: 10 * weight(kg) + 6.25 * height(cm) - 5 * age - 161

Activity Multiplier:
  3 days/week: 1.375 (lightly active)
  4 days/week: 1.465 (moderately active)
  5 days/week: 1.55  (active)
  6 days/week: 1.725 (very active)

TDEE = BMR * Activity Multiplier

Goal Adjustments:
  Fat Loss:            TDEE - 500 kcal
  Weight Gain:         TDEE + 400 kcal
  Muscle Building:     TDEE + 300 kcal
  Health Maintenance:  TDEE (no change)
```

---

## 4. Tool Design

### 4.1 `get_workout_plan`

**Input:** goal, fitness_level, days_per_week, equipment_access
**Logic:**
1. Load `data/workouts/{goal}.json`
2. Filter by fitness_level and equipment
3. Trim/expand to match days_per_week
4. Return structured weekly plan

**Output:** Day-wise workout plan with exercises, sets, reps, rest periods.

### 4.2 `get_diet_plan`

**Input:** goal, weight, height, age, diet_preference, cuisine_preference
**Logic:**
1. Calculate TDEE and adjust for goal
2. Compute macro split (protein/carbs/fat)
3. Load `data/diet_plans/{goal}.json`
4. Filter by diet_preference and cuisine
5. Return meal plan fitting calorie target

**Macro Splits by Goal:**
| Goal                | Protein   | Carbs     | Fat       |
|---------------------|-----------|-----------|-----------|
| Fat Loss            | 40%       | 30%       | 30%       |
| Weight Gain         | 25%       | 50%       | 25%       |
| Muscle Building     | 35%       | 40%       | 25%       |
| Health Maintenance  | 30%       | 40%       | 30%       |

**Output:** Daily meal plan with breakfast, lunch, dinner, snacks + macro breakdown.

### 4.3 `get_youtube_recommendations`

**Input:** goal, fitness_level, content_type (workout/diet/both)
**Logic:**
1. Load `data/youtube_videos/{goal}.json`
2. Filter by level and content_type
3. Return top 3-5 relevant videos

**Output:** Video title, URL, duration, and brief description.

---

## 5. Data Schema

### 5.1 Workout Data (`data/workouts/{goal}.json`)

```json
{
  "goal": "muscle_building",
  "levels": {
    "beginner": {
      "equipment": {
        "full_gym": {
          "days": [
            {
              "day": 1,
              "name": "Push Day",
              "focus": "Chest, Shoulders, Triceps",
              "exercises": [
                {
                  "name": "Bench Press",
                  "sets": 4,
                  "reps": "8-10",
                  "rest_sec": 90,
                  "muscle_group": "chest",
                  "equipment": "barbell"
                }
              ]
            }
          ]
        },
        "basic": { ... },
        "none": { ... }
      }
    },
    "intermediate": { ... },
    "advanced": { ... }
  }
}
```

### 5.2 Diet Data (`data/diet_plans/{goal}.json`)

```json
{
  "goal": "muscle_building",
  "diet_types": {
    "non_vegetarian": {
      "cuisines": {
        "indian": {
          "meals": {
            "breakfast": [
              {
                "name": "Egg Bhurji with Multigrain Roti",
                "calories": 450,
                "protein_g": 28,
                "carbs_g": 40,
                "fat_g": 18,
                "ingredients": ["eggs", "onion", "tomato", "multigrain roti"],
                "prep_time_min": 15
              }
            ],
            "lunch": [...],
            "dinner": [...],
            "snacks": [...]
          }
        },
        "western": { ... }
      }
    },
    "vegetarian": { ... },
    "vegan": { ... }
  }
}
```

### 5.3 YouTube Video Data (`data/youtube_videos/{goal}.json`)

```json
{
  "goal": "muscle_building",
  "videos": [
    {
      "title": "Complete Push Pull Legs Routine",
      "url": "https://www.youtube.com/watch?v=XXXXX",
      "type": "workout",
      "level": "intermediate",
      "duration_min": 15,
      "tags": ["ppl", "gym", "hypertrophy"],
      "description": "Full PPL split explanation with form demos"
    }
  ]
}
```

---

## 6. Project Structure

```
fitness-agent/                        # Repository root (run `adk web` from here)
├── fitness_agent/                    # ADK agent package
│   ├── __init__.py
│   ├── agent.py                      # Main ADK agent (defines root_agent)
│   ├── .env                          # API key (not committed)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── workout_planner.py        # get_workout_plan tool
│   │   ├── diet_planner.py           # get_diet_plan tool
│   │   └── youtube_recommender.py    # get_youtube_recommendations tool
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                # Pydantic models for all data types
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_loader.py            # JSON data loading & filtering
│   │   └── calculations.py           # BMI, TDEE, macro calculations
│   └── data/
│       ├── workouts/
│       │   ├── fat_loss.json
│       │   ├── muscle_building.json
│       │   ├── weight_gain.json
│       │   └── health_maintenance.json
│       ├── diet_plans/
│       │   ├── fat_loss.json
│       │   ├── muscle_building.json
│       │   ├── weight_gain.json
│       │   └── health_maintenance.json
│       └── youtube_videos/
│           ├── fat_loss.json
│           ├── muscle_building.json
│           ├── weight_gain.json
│           └── health_maintenance.json
├── .env.example                      # Template for API keys
├── .gitignore
├── requirements.txt
├── FLOW.md                           # This document
├── LICENSE
└── README.md
```

---

## 7. Tech Stack

| Component        | Technology                        |
|------------------|-----------------------------------|
| Agent Framework  | Google ADK (`google-adk`)         |
| LLM              | Gemini 2.0 Flash                  |
| Language         | Python 3.11+                      |
| Data Validation  | Pydantic                          |
| Data Storage     | Local JSON files                  |
| Config           | python-dotenv                     |

---

## 8. Future Enhancements (v2+)

- **Progress Tracking:** Store workout logs, track PRs, visualize progress
- **Adaptive Plans:** Modify plans based on user feedback and performance
- **Multi-week Periodization:** Progressive overload programming
- **Exercise Substitutions:** Swap exercises based on injury/preference
- **Supplement Recommendations:** Creatine, protein, vitamins based on goal
- **Integration:** Google Fit / Apple Health data import
- **RAG Pipeline:** Vector-embed large exercise databases for smarter retrieval
- **Web UI:** Streamlit or Gradio frontend for richer interaction

---

## 9. How to Add Your Data

### Adding YouTube Videos
1. Open `data/youtube_videos/{goal}.json`
2. Add entries following the schema in Section 5.3
3. Tag each video with `type` (workout/diet), `level`, and relevant `tags`

### Adding Workout Plans
1. Open `data/workouts/{goal}.json`
2. Add exercises under the correct `level → equipment → days` path
3. Include sets, reps, rest time, and muscle group

### Adding Diet Plans
1. Open `data/diet_plans/{goal}.json`
2. Add meals under `diet_type → cuisine → meal_category`
3. Include calories, macros, ingredients, and prep time

---
