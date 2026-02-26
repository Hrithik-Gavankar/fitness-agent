#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check for .env
if [ ! -f fitness_agent/.env ] || grep -q "your_google_api_key_here" fitness_agent/.env 2>/dev/null; then
    echo "⚠️  GOOGLE_API_KEY not set. Add it to fitness_agent/.env"
    echo "   echo 'GOOGLE_API_KEY=your_key' > fitness_agent/.env"
    exit 1
fi

# Activate venv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting FitCoach AI..."
echo "  ADK Agent UI  → http://localhost:8000"
echo "  Streamlit UI  → http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both."
echo ""

# Start ADK web in background
adk web --port 8000 &
ADK_PID=$!

# Start Streamlit in background
streamlit run app.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $ADK_PID 2>/dev/null
    kill $STREAMLIT_PID 2>/dev/null
    wait $ADK_PID 2>/dev/null
    wait $STREAMLIT_PID 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# Wait for either to exit
wait
