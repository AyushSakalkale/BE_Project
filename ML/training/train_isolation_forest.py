import os
import pandas as pd
from models.isolation_forest import IsolationForestDetector

def train_iforest(data_dir="data", model_dir="models"):
    data_path = os.path.join(data_dir, 'parsed_logs.csv')
    if not os.path.exists(data_path):
        print(f"Parsed logs not found at {data_path}. Run parser.py first.")
        return
        
    df = pd.read_csv(data_path)
    detector = IsolationForestDetector()
    print("Training Isolation Forest model...")
    detector.train(df)
    
    detector.save_model(os.path.join(model_dir, "isolation_forest.pkl"))
    print("Isolation Forest model training complete.")

if __name__ == "__main__":
    if not os.path.exists("models"):
        os.makedirs("models")
    train_iforest()
