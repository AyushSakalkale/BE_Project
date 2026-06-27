# Frontend Dashboard User Guide and Demonstration Walkthrough

This document provides step-by-step instructions on how to launch the frontend web application, authenticate, navigate the interface, and walk an examiner through a live demonstration of the hybrid log anomaly detection system.

---

## 1. Quick Start Instructions

To run the entire system (database, message queue, backend ML API, and the React frontend):

1. **Launch the Services**:
   From the project root directory, execute:
   ```bash
   ./start_project.sh
   ```
   This script will automatically:
   * Launch the Docker containers for PostgreSQL, Redis, Flink, and the FastAPI backend.
   * Verify frontend node modules and run `npm run dev` in the background.

2. **Access the Web Interface**:
   Open your browser and navigate to:
   * **Frontend Dashboard**: `http://localhost:5173/`
   * **Backend API Documentation**: `http://localhost:8000/docs`

---

## 2. Interactive Walkthrough Flow for the Examiner

Follow this structured flow to demonstrate all system capabilities during the evaluation:

### Step 1: User Registration & Session Authorization
* **Action**: Navigate to `http://localhost:5173/` and click **Sign Up**. Register a new user (e.g., `examiner_demo`, `examiner@demo.com`, password `Password123!`). Then log in.
* **Explanation for Examiner**: Explain that the frontend dashboard enforces strict role-based session security via JSON Web Tokens (JWT) stored statefully using **Zustand**. All log ingestion endpoints require valid user authorization headers.

### Step 2: Metric Monitoring Dashboard
* **Action**: Guide the examiner through the landing page.
* **Explanation for Examiner**: Point out the live metrics widgets:
  * **Total Logs Ingested**: Ingested log counter.
  * **Anomalies Flagged**: Total anomalies flagged across all layers.
  * **Anomaly Trends**: Real-time time-series visualization charts plotted dynamically using **Recharts**.

### Step 3: Log Ingestion & Simulating Anomalies
* **Action**: Click on **Log Ingestion** in the sidebar. Show the three options:
  1. **Paste Logs**: Type or paste log entries directly.
  2. **File Upload**: Drag and drop a raw `.log` or `.txt` file.
  3. **API Integration**: Generate an ingestion API key and show the copyable Python code snippet.
* **Simulation Demo**:
  * Copy the following raw log line:
    `BLOCK* NameSystem.allocateBlock: /user/root/rand6/part-0000 blk_123. Exception: Connection Timed Out`
  * Paste it into the direct text box and click **Analyze**.
  * **Explanation**: Explain that this immediately triggers the **Heuristic Safety Net** because of the keyword `Exception`. The frontend dashboard count for anomalies will increment in real time.

### Step 4: Log Explorer & Anomaly Explanation Modal
* **Action**: Navigate to **Log Explorer** in the sidebar. 
* **Demo Details**:
  * Point out the high-density log data table. Normal logs are displayed in standard grey rows.
  * Show the anomalous logs highlighted in **red** with warning badges.
  * Click the **Explain** (Brain icon) button on the anomalous row.
  * **Explanation**: A modal dialog will appear. Explain to the examiner that this modal parses and correlates suspicion levels:
    * **Heuristics Override**: Displays `1.0` if keywords triggered.
    * **Isolation Forest Score**: Shows structural drift score.
    * **LSTM Sequence Indicator**: Displays whether block execution sequences were violated.
    * **Prophet Volume Indicator**: Displays binned traffic volume scores.
    * **AI Summary**: Shows a natural language description explaining why the system classified this log as an anomaly.

---

## 3. Troubleshooting

* **Frontend displays API connection errors**:
  Verify that the backend Docker container is active on `http://localhost:8000`. You can check this by running `docker ps` or viewing Swagger docs at `http://localhost:8000/docs`.
* **Vite Dev Server fails to start**:
  Check `vite.log` in the `frontend` folder for errors. If port `5173` is already in use, run `kill -9 $(lsof -t -i:5173)` to free it, then run `./start_project.sh` again.
