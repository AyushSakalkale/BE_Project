# AI-Powered Log Anomaly Detection Backend

This is a production-level FastAPI backend for ingesting and analyzing logs using hybrid ML models (LSTM + Prophet).

## Features
- **JWT Auth**: Secure user registration and login.
- **Hybrid ML Scoring**: Real-time evaluation of logs (70% LSTM, 30% Prophet).
- **Log Simplification**: AI-driven human-readable log summaries via Hugging Face.
- **Multi-Channel Ingestion**: Supports file uploads, raw text pasting, and API-key-based ingestion.
- **Dashboard**: Real-time statistics, anomaly trends, and recent history.
- **Dockerized**: Pre-configured with PostgreSQL and Redis.

## Quick Start (with Docker)
1. **CD into backend**: `cd backend`
2. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```
3. **Access APIs**:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Root API: [http://localhost:8000/](http://localhost:8000/)

## Local Development (without Docker)
1. **Activate venv**: `..\venv\Scripts\activate`
2. **Install deps**: `pip install -r requirements.txt`
3. **Run App**:
   ```bash
   uvicorn main:app --reload
   ```

## ML Integration
This backend integrates with the models and inference logic in the `../ML` directory. It uses a singleton service to load models once and provide fast scoring.
