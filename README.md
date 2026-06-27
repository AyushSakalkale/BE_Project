# BE_Project: Hybrid Log Anomaly Detection System

A production-level hybrid log anomaly detection system combining Heuristics, Isolation Forest, LSTM sequence analysis, and Prophet volume tracking.

## Project Structure

* `/backend`: FastAPI microservice backend using PostgreSQL and Redis.
* `/frontend`: React dashboard (Vite + Tailwind CSS + Recharts).
* `/ML`: Machine Learning training and evaluation scripts (LSTM, Isolation Forest, Prophet).
* `/md`: Thesis documentation and evaluation reports.
* `/files`: Demonstration logs for direct testing.

## Documentation Links

* [Thesis Evaluation Chapter](file:///Users/ayushsakalkale/Desktop/final_be/md/evaluation_chapter.md)
* [Final Metrics Report](file:///Users/ayushsakalkale/Desktop/final_be/md/FINAL_EVALUATION_REPORT.md)
* [Frontend User Guide](file:///Users/ayushsakalkale/Desktop/final_be/md/frontend_instructions.md)

## Prerequisites

Ensure you have the following installed on your system:
* **Docker Desktop** (must be open and running)
* **Python 3.8+** (for running ML evaluation scripts)
* **Node.js (v18+)** (for frontend dashboard)

## Quick Start

1. **Setup Python Virtual Environment** (Recommended for macOS/Linux to avoid permission conflicts):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r ML/requirements.txt
   ```

2. **Configure AI Explanations (Optional)**:
   The backend uses Hugging Face models to explain anomalies. If you wish to use live Hugging Face APIs, rename the `.env.example` in `backend/` to `.env` (or set the environment variable) and add your token:
   ```env
   HUGGINGFACE_API_KEY=your_token_here
   ```
   *(If left empty, the application will automatically fall back to clean local descriptions).*

3. **Launch Services**:
   ```bash
   ./start_project.sh
   ```

4. **Access Web Interfaces**:
   * **Frontend Web UI**: `http://localhost:5173/`
   * **Backend Swagger API Docs**: `http://localhost:8000/docs`

5. **Run the Evaluation Test Suite**:
   ```bash
   ./run_all_tests.sh
   ```

6. **Shutdown and Clean up Services**:
   ```bash
   ./stop_project.sh
   ```

## Troubleshooting & Port Conflicts

* **Port 5432 Conflict (PostgreSQL)**:
  If you have a local PostgreSQL service running on your host machine, the Docker container might fail to start. Stop your local PostgreSQL service before running the startup script:
  * *macOS (Homebrew)*: `brew services stop postgresql`
  * *Linux (systemd)*: `sudo systemctl stop postgresql`
* **Port 5173 Conflict (Vite Frontend)**:
  If port `5173` is already occupied, run `kill -9 $(lsof -t -i:5173)` to free it before running `./start_project.sh`.

