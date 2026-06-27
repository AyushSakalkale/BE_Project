import sys
import os
import re
from app.core.config import settings

# Hybrid import strategy to use the ML models
ML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), settings.ML_DIR))
sys.path.append(ML_PATH)

try:
    from inference.predict import RealTimeInference
except ImportError:
    # This might happen in development if paths are tricky, but adding to sys.path should work
    print(f"Warning: Could not import RealTimeInference from {ML_PATH}")
    RealTimeInference = None

class MLService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance._init_detector()
        return cls._instance

    def _init_detector(self):
        self.block_sequences = {}
        if RealTimeInference is None:
            self.detector = None
            return
            
        try:
            self.detector = RealTimeInference(
                lstm_model_path=os.path.join(ML_PATH, "models/lstm_model.h5"),
                prophet_model_path=os.path.join(ML_PATH, "models/prophet_model.pkl"),
                isolation_forest_model_path=os.path.join(ML_PATH, "models/isolation_forest.pkl"),
                event_mapping_path=os.path.join(ML_PATH, "models/event_mapping.pkl"),
                templates_path=os.path.join(ML_PATH, "data/templates.csv")
            )
        except Exception as e:
            print(f"Warning: Could not initialize RealTimeInference: {e}")
            print("ML Log Anomaly Detection will run in fallback/heuristics mode.")
            self.detector = None
        
        # Regex patterns for parsing (duplicated from parser.py for reliability)
        self.regex_patterns = [
            (r'blk_-?\d+', 'blk_<*>'),
            (r'\d+\.\d+\.\d+\.\d+', 'IP'),
            (r'/\d+\.\d+\.\d+\.\d+:\d+', 'Source/Dest'),
            (r'\b\d+\b', '<*>')
        ]

    def parse_message(self, message):
        template = message
        for pattern, replacement in self.regex_patterns:
            template = re.sub(pattern, replacement, template)
        return template

    def parse_log_line(self, line: str):
        # Try parsing in standard HDFS format
        tokens = line.strip().split()
        if len(tokens) >= 5 and re.match(r'^\d{6}$', tokens[0]) and re.match(r'^\d{6}$', tokens[1]):
            date = tokens[0]
            time_str = tokens[1]
            ts = f"20{date[:2]}-{date[2:4]}-{date[4:6]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            level = "INFO"
            for t in tokens[2:5]:
                if t.upper() in ["INFO", "WARN", "WARNING", "ERROR", "FATAL", "DEBUG"]:
                    level = t
                    break
            
            try:
                level_idx = tokens.index(level)
                if level_idx + 1 < len(tokens) and tokens[level_idx + 1].endswith(':'):
                    msg = " ".join(tokens[level_idx+2:])
                else:
                    msg = " ".join(tokens[level_idx+1:])
            except ValueError:
                msg = " ".join(tokens[2:])
            return ts, level, msg
        else:
            # Fallback if it's not a standard HDFS-like line
            level = "INFO"
            msg_upper = line.upper()
            if any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT"]):
                level = "ERROR"
            elif any(w in msg_upper for w in ["WARN", "WARNING", "SLOW"]):
                level = "WARN"
            
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            return ts, level, line

    def _heuristic_check(self, message: str) -> float:
        """Fallback for logs the ML model doesn't recognize."""
        msg_upper = message.upper()
        if any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"]):
            return 0.9
        if any(w in msg_upper for w in ["WARN", "WARNING", "SLOW"]):
            return 0.45
        return 0.0

    async def predict_combined(self, message: str, timestamp=None, sequence=None, level=None):
        # 1. Heuristic-Based Score (Critical fallback)
        heuristic_score = self._heuristic_check(message)
        
        if not self.detector:
            is_anomaly = heuristic_score > 0.5
            return heuristic_score, is_anomaly, "Unknown"
        
        # Extract features for models
        parsed_ts, parsed_level, parsed_msg = self.parse_log_line(message)
        
        ts_val = timestamp if timestamp else parsed_ts
        lvl_val = level if level else parsed_level
        msg_val = parsed_msg
        
        # Try finding event_id on msg_val first, then fallback to message
        event_id = self.detector._get_event_id(msg_val)
        if event_id == "Unknown":
            event_id = self.detector._get_event_id(message)
            
        # 1. LSTM Score
        lstm_score = 0.0
        lstm_anomaly = False
        if event_id != "Unknown":
            # Track sequence state per BlockID, mirroring production stateful tracking
            block_match = re.search(r'(blk_-?\d+)', message)
            block_id = block_match.group(1) if block_match else None
            
            if sequence:
                current_seq = sequence
            elif block_id:
                if not hasattr(self, 'block_sequences'):
                    self.block_sequences = {}
                if len(self.block_sequences) > 5000:
                    # simple cleanup of oldest keys to prevent memory leak
                    keys_to_remove = list(self.block_sequences.keys())[:1000]
                    for k in keys_to_remove:
                        self.block_sequences.pop(k, None)
                        
                if block_id not in self.block_sequences:
                    self.block_sequences[block_id] = []
                self.block_sequences[block_id].append(event_id)
                current_seq = self.block_sequences[block_id]
            else:
                current_seq = [event_id]
                
            if len(current_seq) >= 2:
                lstm_score, lstm_anomaly = self.detector.predict_lstm_anomaly(current_seq)
            
        # 2. Prophet Score (Time-Series)
        prophet_anomaly = False
        if timestamp:
            prophet_anomaly = self.detector.predict_prophet_anomaly(timestamp, 1)
        prophet_score = 1.0 if prophet_anomaly else 0.0
            
        # 3. Isolation Forest Score
        iforest_score, iforest_anomaly = self.detector.predict_iforest_anomaly(msg_val, lvl_val, ts_val)
        
        # 4. Final Combination
        # Consensus: 0.3 * IF(x) + 0.4 * LSTM(x) + 0.3 * Prophet(x)
        ml_score = 0.3 * iforest_score + 0.4 * lstm_score + 0.3 * prophet_score
        
        final_score = max(ml_score, heuristic_score)
        
        is_anomaly = final_score > 0.5 or lstm_anomaly or iforest_anomaly
        
        final_score = float(final_score)
        is_anomaly = bool(is_anomaly)
        
        # Debug logging to terminal
        print(f"[ML Consensus] msg: {msg_val[:60]}... | Level: {lvl_val} | TS: {ts_val}")
        print(f"  -> LSTM: {lstm_score:.4f} (anomaly: {lstm_anomaly})")
        print(f"  -> Prophet: {prophet_score:.4f} (anomaly: {prophet_anomaly})")
        print(f"  -> Isolation Forest: {iforest_score:.4f} (anomaly: {iforest_anomaly})")
        print(f"  -> Consensus Score: {ml_score:.4f} | Heuristic: {heuristic_score:.4f} | Final: {final_score:.4f} (is_anomaly: {is_anomaly})")
        
        return final_score, is_anomaly, event_id

ml_service = MLService()
