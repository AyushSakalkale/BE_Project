import os
import pandas as pd
from models.prophet_model import ProphetDetector

def train_prophet(data_dir="data", model_dir="models"):
    data_path = os.path.join(data_dir, 'prophet_data.csv')
    if not os.path.exists(data_path):
        print("Prophet data not found. Run sequencer.py first.")
        return
        
    df = pd.read_csv(data_path)
    df['ds'] = pd.to_datetime(df['ds'])
    
    detector = ProphetDetector()
    detector.train(df)
    
    detector.save_model(os.path.join(model_dir, "prophet_model.pkl"))
    print("Prophet model training complete.")

if __name__ == "__main__":
    if not os.path.exists("models"):
        os.makedirs("models")
    train_prophet()
