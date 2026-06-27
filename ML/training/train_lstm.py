import os
import pickle
import numpy as np
import pandas as pd
from tensorflow.keras.preprocessing.sequence import pad_sequences
from models.lstm import AnomalyLSTM

def train_lstm(data_dir="data", model_dir="models"):
    # Load sequences
    with open(os.path.join(data_dir, 'sequences.pkl'), 'rb') as f:
        sequences = pickle.load(f)
        
    # Load templates to get vocab size
    templates_df = pd.read_csv(os.path.join(data_dir, 'templates.csv'))
    event_to_id = {row['EventID']: i+1 for i, row in templates_df.iterrows()}
    vocab_size = len(event_to_id) + 1 # +1 for padding
    
    # Convert sequences to integers
    int_sequences = []
    for seq in sequences:
        int_seq = [event_to_id[e] for e in seq if e in event_to_id]
        if len(int_seq) > 1:
            int_sequences.append(int_seq)
            
    # Create X and y using prefix-to-next subsequences
    X = []
    y = []
    for seq in int_sequences:
        for i in range(1, len(seq)):
            X.append(seq[:i])
            y.append(seq[i])
        
    X = pad_sequences(X, maxlen=10, padding='pre')
    y = np.array(y)
    
    # Train
    model = AnomalyLSTM(vocab_size=vocab_size)
    history = model.train(X, y, epochs=5, batch_size=64)
    
    # Save model and mapping
    model.save_model(os.path.join(model_dir, "lstm_model.h5"))
    with open(os.path.join(model_dir, "event_mapping.pkl"), "wb") as f:
        pickle.dump(event_to_id, f)
        
    return history

if __name__ == "__main__":
    if not os.path.exists("models"):
        os.makedirs("models")
    train_lstm()
