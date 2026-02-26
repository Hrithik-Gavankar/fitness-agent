# Contributing to FitCoach AI

Thanks for your interest in contributing! This guide will help you get started.

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/fitness-agent.git
cd fitness-agent
```

### 2. Set up the dev environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 3. Configure the agent

```bash
cp fitness_agent/.env.example fitness_agent/.env
# Edit fitness_agent/.env — set GOOGLE_API_KEY or configure Ollama
```

### 4. Run locally

```bash
streamlit run app.py
```

## How to Contribute

### Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version, OS, and browser
- Relevant logs or screenshots

### Suggesting Features

Open an issue with:
- Problem you're trying to solve
- Your proposed solution
- Any alternatives you considered

### Submitting Code

1. **Create a branch** from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes.** Follow the code style below.

3. **Test locally** — make sure the app runs without errors:
   ```bash
   streamlit run app.py
   ```

4. **Commit** with a clear message:
   ```bash
   git commit -m "Add: brief description of what changed"
   ```
   Use prefixes: `Add:`, `Fix:`, `Update:`, `Remove:`, `Refactor:`

5. **Push and open a PR:**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request against `master`.

## Code Style

- **Python 3.10+** — use type hints where practical
- **Formatting** — keep it clean and consistent with the existing code
- **Imports** — standard library first, third-party second, local third (separated by blank lines)
- **No secrets** — never commit API keys, `.env` files, or `secrets.toml`
- **Comments** — only when the code isn't self-explanatory. No narration comments.

## Project Structure

| Directory | What goes here |
|-----------|---------------|
| `fitness_agent/agent.py` | Agent definition, instructions, model config |
| `fitness_agent/tools/` | Agent tool functions (one per file) |
| `fitness_agent/utils/` | Shared utilities (calculations, data loading) |
| `fitness_agent/models/` | Pydantic schemas |
| `fitness_agent/data/` | JSON knowledge base (workouts, diets, videos) |
| `app.py` | Streamlit frontend |
| `auth.py` | Authentication module |

## Adding Data

### Workout / Diet Plans

Add or edit JSON files in `fitness_agent/data/workouts/` or `fitness_agent/data/diet_plans/`. Follow the existing schema — see [FLOW.md](FLOW.md) for details.

### YouTube Videos

Add entries to `fitness_agent/data/youtube_videos/<goal>.json`:

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

Only use videos that are publicly available. Do not upload or redistribute copyrighted content.

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Update the README if you add a new feature or change setup steps
- If your change affects the agent's behavior, test with at least 2-3 different prompts
- Link related issues in the PR description (e.g., "Closes #5")

## Questions?

Open a [discussion](https://github.com/Hrithik-Gavankar/fitness-agent/discussions) or reach out via issues. We're happy to help!
