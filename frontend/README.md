# AnomalyAI Frontend

A production-level SaaS dashboard for real-time log monitoring and AI-powered anomaly detection.

## Tech Stack

- **React (Vite)**: Core framework
- **Tailwind CSS**: Modern, premium dark theme styling
- **Axios**: API integration with JWT interceptors
- **React Query**: Data fetching, caching, and auto-polling
- **Recharts**: Time-series anomaly trends visualization
- **Zustand**: Global authentication and session state
- **Lucide React**: Vector icons
- **Framer Motion**: Smooth UI transitions

## Features

1. **Authentication**: Complete Signup/Login flow with JWT persistence.
2. **Real-time Dashboard**:
    - Summary cards for Logs and Anomalies.
    - Interactive Anomaly Trends graph.
    - Live feed of recent events with auto-refresh (10s).
3. **Log Ingestion**:
    - **Upload**: Drag-and-drop log files (.log, .txt).
    - **Paste**: Direct raw log analysis.
    - **API Integration**: Generate API keys and view code snippets (Python/Node.js).
    - **External**: Cloud connector placeholders (Kafka/RabbitMQ).
4. **Log Explorer**:
    - High-density data table with fuzzy search and service filtering.
    - Anomaly highlighting and "Brain Circuit" explain button.
5. **AI Insights**:
    - On-demand natural language explanation of complex log events.

## Getting Started

### Prerequisites

- Node.js (v18+)
- Backend running at `http://localhost:8000`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

### Configuration

Modify `.env` to change the backend API URL:
```env
VITE_API_BASE_URL=http://localhost:8000
```
