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

## Quick Start

1. **Launch Services**:
   ```bash
   ./start_project.sh
   ```
2. **Access Dashboards**:
   * Frontend: `http://localhost:5173/`
   * Swagger Docs: `http://localhost:8000/docs`
3. **Run Test Suite**:
   ```bash
   ./run_all_tests.sh
   ```
4. **Shutdown Services**:
   ```bash
   ./stop_project.sh
   ```
