import pandas as pd
import numpy as np
import os
import pickle
from tqdm import tqdm

def create_sequences(df, out_dir="data", window_size=10):
    # Group by BlockID
    block_groups = df.groupby('BlockID')
    sequences = []
    
    for block_id, group in tqdm(block_groups, desc="Creating Sequences"):
        if block_id == "None": continue
        
        events = group['EventID'].values.tolist()
        # If sequence is longer than window_size, we can slide? 
        # Or just keep the full sequence? 
        # For anomaly detection, we often look for anomalies in the full block lifecycle.
        # But for training, let's create windows.
        if len(events) < 2: continue # Need at least 2 events to predict next
        
        # Simple windowing
        w = min(len(events), window_size)
        for i in range(len(events) - w + 1):
            sequences.append(events[i:i+w])
            
    with open(os.path.join(out_dir, 'sequences.pkl'), 'wb') as f:
        pickle.dump(sequences, f)
    
    return sequences

def create_ts_data(df, out_dir="data", freq="1min"):
    # Aggregate log counts per time interval
    df = df.set_index('Timestamp')
    ts_data = df.resample(freq).size().reset_index()
    ts_data.columns = ['ds', 'y']
    
    ts_data.to_csv(os.path.join(out_dir, 'prophet_data.csv'), index=False)
    return ts_data

if __name__ == "__main__":
    DATA_PATH = r"data/parsed_logs.csv"
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH, parse_dates=['Timestamp'])
        seqs = create_sequences(df)
        ts = create_ts_data(df)
        print(f"Created {len(seqs)} sequences and {len(ts)} time-series data points.")
    else:
        print(f"File {DATA_PATH} not found. Run parser.py first.")
