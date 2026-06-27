# HDFS Log Anomaly Detection System

This project implements a log anomaly detection system using two approaches:
1. **LSTM (Sequence Based)**: Detects anomalies by predicting the next log event in a block's lifecycle.
2. **Prophet (Time-Series Based)**: Detects spikes or unusual patterns in the volume of logs over time.

## Project Structure
- `/data`: Processed logs, templates, and sequences.
- `/preprocessing`: Log parsing and sequence generation logic.
- `/models`: Model architectures and saved weights.
- `/training`: Scripts to train the models.
- `/evaluation`: Metric calculations and visualizations.
- `/inference`: Unified API for real-time anomaly detection.

## Setup
1. Activate your virtual environment: `d:\pict_BE_Finalyear\venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`

## How to Run
### 1. Unified Pipeline (Recommended)
Run the entire process from parsing to training:
```bash
python run_pipeline.py
```

### 2. Individual Steps
- **Parse raw logs**: `python preprocessing/parser.py`
- **Generate sequences**: `python preprocessing/sequencer.py`
- **Train LSTM**: `python training/train_lstm.py`
- **Train Prophet**: `python training/train_prophet.py`

## Real-Time Usage
You can integrate the `RealTimeInference` class from `inference/predict.py` into your API:
```python
from inference.predict import RealTimeInference

infer = RealTimeInference(
    lstm_model_path="models/lstm_model.h5",
    prophet_model_path="models/prophet_model.pkl",
    event_mapping_path="models/event_mapping.pkl",
    templates_path="data/templates.csv"
)

# For a single log message
score, is_anomaly = infer.predict_lstm_anomaly(["E1", "E2", "E3", "E4"])
```

## Dataset
This system is configured for the HDFS log dataset. It automatically extracts `block_id` and templates the log messages into Event IDs.
