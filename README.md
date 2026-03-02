# FitCoach AI

An AI-powered fitness coach built with **Google ADK** that provides personalized workout plans, diet plans, and YouTube video recommendations through a conversational interface.

## Agent Pattern

This project follows the **Single Agent** pattern from [Google ADK's agent design patterns](https://youtu.be/GDm_uH6VxPY):

| Pattern | Description | Used Here? |
|---------|-------------|:----------:|
| **Single Agent** | One agent with multiple tools, handles all tasks via tool selection | Yes |
| Sequential Agent | Multiple agents chained in order, output of one feeds the next | No |
| Parallel Agent | Multiple agents run concurrently, results are aggregated | No |

Our `root_agent` is a single `Agent` with three tools (`get_workout_plan`, `get_diet_plan`, `get_youtube_recommendations`). The LLM decides which tool(s) to call based on the user's request and profile context. This pattern works well here because the tools are independent and the agent's instruction prompt handles all orchestration logic.

## Features

- **Personalized Onboarding** -- Collects user profile (age, weight, height, goals, preferences) through a sidebar form
- **Workout Plans** -- Day-wise training programs tailored to goal, fitness level, and equipment access
- **Diet Plans** -- Calorie-targeted meal plans with macro breakdowns, supporting Indian/Western cuisines and veg/non-veg/vegan preferences
- **YouTube Recommendations** -- Curated video suggestions (with embedded players) matched to your goal and level
- **Smart Dashboard** -- BMI, TDEE, macros, weight tracking, and activity streaks
- **Authentication** -- Optional Google and GitHub OAuth login via Supabase

## Project Structure

```
fitness-agent/
├── fitness_agent/              # ADK agent package
│   ├── agent.py                # Agent definition (root_agent)
│   ├── .env                    # API key + model config (not committed)
│   ├── tools/
│   │   ├── workout_planner.py
│   │   ├── diet_planner.py
│   │   └── youtube_recommender.py
│   ├── models/
│   │   └── schemas.py          # Pydantic data models
│   ├── utils/
│   │   ├── calculations.py     # BMI, TDEE, macro calculations
│   │   └── data_loader.py      # JSON data loading + filtering
│   ├── .env.example            # Template for agent config
│   └── data/
│       ├── workouts/           # Workout plans by goal (JSON)
│       ├── diet_plans/         # Diet plans by goal (JSON)
│       └── youtube_videos/     # Video recommendations by goal (JSON)
├── app.py                      # Streamlit UI
├── auth.py                     # Supabase OAuth module (Google + GitHub)
├── start.sh                    # Launch script
├── FLOW.md                     # Architecture documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── MAINTAINERS.md              # Project owners & contributors
└── requirements.txt
```

## Quick Start

### 1. Clone and setup

```bash
git clone <your-repo-url>
cd fitness-agent

python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Configure the agent

Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey):

```bash
cp fitness_agent/.env.example fitness_agent/.env
# Edit fitness_agent/.env and set GOOGLE_API_KEY
```

The free tier of Gemini 2.5 Flash provides ~10-15 requests/minute and 250-1,000 requests/day — plenty for personal use and development.

### 3. Run the app

```bash
streamlit run app.py
```

Opens at [http://localhost:8501](http://localhost:8501).

Or use the launch script for both ADK UI and Streamlit:

```bash
./start.sh
```

### 4. (Optional) Enable authentication

Auth is powered by [Supabase](https://supabase.com) and is entirely optional — leave the env vars blank to skip login.

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **Authentication → Providers** and enable Google and/or GitHub
3. Copy your Project URL and `anon` key from **Settings → API**
4. Add them to `fitness_agent/.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
AUTH_REDIRECT_URL=http://localhost:8501
```

You can enable one or both providers.

## Adding Your Data

### YouTube Videos

Add real videos to `fitness_agent/data/youtube_videos/*.json`:

```json
{
  "title": "Video Title",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "type": "workout",
  "level": "beginner",
  "duration_min": 15,
  "tags": ["hiit", "no-equipment"],
  "description": "Brief description"
}
```

### Workout / Diet Plans

Edit JSON files in `fitness_agent/data/workouts/` and `fitness_agent/data/diet_plans/`. See `FLOW.md` for schemas.

## Tech Stack

| Component        | Technology                    |
|------------------|-------------------------------|
| Agent Framework  | Google ADK                    |
| LLM              | Gemini 2.5 Flash (free tier) |
| Frontend         | Streamlit                     |
| Authentication   | Supabase Auth (OAuth PKCE)    |
| Language         | Python 3.10+                  |
| Data Validation  | Pydantic                      |
| Data Storage     | Local JSON files              |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## Maintainers

See [MAINTAINERS.md](MAINTAINERS.md) for the full list of project owners and contributors.

## Documentation

- [FLOW.md](FLOW.md) — System flow and agent design
- [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) — Database schema, ER diagram, and migration plan
- [docs/diagrams/architecture.excalidraw](docs/diagrams/architecture.excalidraw) — Block architecture diagram (open with [excalidraw.com](https://excalidraw.com))
