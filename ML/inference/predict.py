import os
import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
import pandas as pd

class RealTimeInference:
    def __init__(self, lstm_model_path, prophet_model_path, isolation_forest_model_path, event_mapping_path, templates_path):
        # Load LSTM
        self.lstm_model = tf.keras.models.load_model(lstm_model_path)
        with open(event_mapping_path, "rb") as f:
            self.event_to_id = pickle.load(f)
        self.id_to_event = {v: k for k, v in self.event_to_id.items()}
        
        # Load Prophet
        with open(prophet_model_path, "rb") as f:
            self.prophet_model = pickle.load(f)
            
        # Load Isolation Forest
        from models.isolation_forest import IsolationForestDetector
        self.iforest_detector = IsolationForestDetector()
        self.iforest_detector.load_model(isolation_forest_model_path)
            
        # Load Templates
        import pandas as pd
        self.templates_df = pd.read_csv(templates_path)
        
        self.regex_patterns = [
            (r'blk_-?\d+', 'blk_<*>'),
            (r'\d+\.\d+\.\d+\.\d+', 'IP'),
            (r'/\d+\.\d+\.\d+\.\d+:\d+', 'Source/Dest'),
            (r'\b\d+\b', '<*>')
        ]

    def _get_event_id(self, message):
        template = message
        for pattern, replacement in self.regex_patterns:
            template = re.sub(pattern, replacement, template)
        
        match = self.templates_df[self.templates_df['Template'] == template]
        if not match.empty:
            return match.iloc[0]['EventID']
        return "Unknown"

    def predict_lstm_anomaly(self, sequence, top_k=5):
        # sequence is a list of EventIDs
        int_seq = [self.event_to_id[e] for e in sequence if e in self.event_to_id]
        if not int_seq:
            return 0.0, False
            
        input_data = pad_sequences([int_seq[:-1]], maxlen=10, padding='pre')
        target = int_seq[-1]
        
        preds = self.lstm_model.predict(input_data, verbose=0)[0]
        top_indices = np.argsort(preds)[-top_k:]
        
        is_anomaly = target not in top_indices
        score = 1.0 - preds[target] if target < len(preds) else 1.0
        
        return score, is_anomaly

    def predict_prophet_anomaly(self, timestamp, count):
        df = pd.DataFrame({'ds': [pd.to_datetime(timestamp)], 'y': [count]})
        forecast = self.prophet_model.predict(df)
        res = df.merge(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')
        is_anomaly = (res['y'].iloc[0] > res['yhat_upper'].iloc[0]) or (res['y'].iloc[0] < res['yhat_lower'].iloc[0])
        return is_anomaly

    def predict_iforest_anomaly(self, message, level, timestamp):
        return self.iforest_detector.predict_anomaly_score(message, level, timestamp)

if __name__ == "__main__":
    # Example usage
    # infer = RealTimeInference("models/lstm_model.h5", "models/prophet_model.pkl", "models/event_mapping.pkl", "data/templates.csv")
    pass
