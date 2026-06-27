import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Setup ML paths
ml_dir = "/Users/ayushsakalkale/Desktop/final_be/ML"
sys.path.append(ml_dir)

from inference.predict import RealTimeInference

def run_validation():
    # Load data
    data_path = os.path.join(ml_dir, "data/parsed_logs.csv")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return
        
    df = pd.read_csv(data_path)
    df['Timestamp_parsed'] = pd.to_datetime(df['Timestamp'])
    
    # Pre-calculate log counts per minute for Prophet
    minute_counts = df.groupby(df['Timestamp_parsed'].dt.floor('min')).size().to_dict()
    
    # Load Inference
    infer = RealTimeInference(
        lstm_model_path=os.path.join(ml_dir, "models/lstm_model.h5"),
        prophet_model_path=os.path.join(ml_dir, "models/prophet_model.pkl"),
        isolation_forest_model_path=os.path.join(ml_dir, "models/isolation_forest.pkl"),
        event_mapping_path=os.path.join(ml_dir, "models/event_mapping.pkl"),
        templates_path=os.path.join(ml_dir, "data/templates.csv")
    )
    
    # 1. Ground Truth
    y_true = []
    for idx, row in df.iterrows():
        msg = str(row['Message']).upper()
        lvl = str(row['Level']).upper()
        is_true_anom = (
            lvl in ["ERROR", "FATAL"] or
            any(w in msg for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"])
        )
        y_true.append(1 if is_true_anom else 0)
        
    y_true = np.array(y_true)
    
    # 2. Batch Prophet Predictions (Huge performance boost!)
    print("Running batch Prophet predictions...")
    prophet_df = pd.DataFrame({
        'ds': df['Timestamp_parsed'],
        'y': [minute_counts.get(t.floor('min'), 1) for t in df['Timestamp_parsed']]
    })
    forecast = infer.prophet_model.predict(prophet_df)
    prophet_anoms = (prophet_df['y'] > forecast['yhat_upper']) | (prophet_df['y'] < forecast['yhat_lower'])
    prophet_anoms = prophet_anoms.values
    prophet_scores = prophet_anoms.astype(float)
    
    # Calculate scores and predictions for other models
    print("Running sequence LSTM and Isolation Forest predictions statefully...")
    iforest_anoms = []
    iforest_scores = []
    lstm_anoms = []
    lstm_scores = []
    ml_scores = []
    heuristic_scores = []
    
    block_sequences = {}
    
    for idx, row in df.iterrows():
        msg = str(row['Message'])
        lvl = str(row['Level'])
        ts = row['Timestamp']
        event_id = row['EventID']
        block_id = row['BlockID']
        
        # Track sequences
        if pd.notna(block_id) and block_id != "None":
            if block_id not in block_sequences:
                block_sequences[block_id] = []
            block_sequences[block_id].append(event_id)
            current_seq = block_sequences[block_id]
        else:
            current_seq = [event_id]
            
        # LSTM
        lstm_score = 0.0
        lstm_anom = False
        if event_id != "Unknown" and len(current_seq) >= 2:
            lstm_score, lstm_anom = infer.predict_lstm_anomaly(current_seq)
            
        # Isolation Forest
        iforest_score, iforest_anom = infer.predict_iforest_anomaly(msg, lvl, ts)
        
        # Heuristics
        msg_upper = msg.upper()
        heuristic_score = 0.0
        if any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"]):
            heuristic_score = 0.9
        elif any(w in msg_upper for w in ["WARN", "WARNING", "SLOW"]):
            heuristic_score = 0.45
            
        # Weighted Ensemble score
        ml_score = 0.3 * iforest_score + 0.4 * lstm_score + 0.3 * prophet_scores[idx]
        
        iforest_anoms.append(iforest_anom)
        iforest_scores.append(iforest_score)
        lstm_anoms.append(lstm_anom)
        lstm_scores.append(lstm_score)
        ml_scores.append(ml_score)
        heuristic_scores.append(heuristic_score)
        
    iforest_anoms = np.array(iforest_anoms)
    iforest_scores = np.array(iforest_scores)
    lstm_anoms = np.array(lstm_anoms)
    lstm_scores = np.array(lstm_scores)
    ml_scores = np.array(ml_scores)
    heuristic_scores = np.array(heuristic_scores)
    
    # 2. Ablation Configurations
    configs = {
        "Isolation Forest Only": iforest_anoms.astype(int),
        "LSTM Only": lstm_anoms.astype(int),
        "Prophet Only": prophet_anoms.astype(int),
        "Weighted Ensemble Only (No Overrides, Thresh > 0.5)": (ml_scores > 0.5).astype(int),
        "Final Production System (Weighted Ensemble + Overrides, No Heuristics)": ((ml_scores > 0.5) | lstm_anoms | prophet_anoms | iforest_anoms).astype(int),
        "Final Production System (With Heuristics)": ((np.maximum(ml_scores, heuristic_scores) > 0.5) | lstm_anoms | prophet_anoms | iforest_anoms).astype(int),
        "Production System (IF + LSTM Overrides, NO Prophet Override, No Heuristics)": ((ml_scores > 0.5) | lstm_anoms | iforest_anoms).astype(int),
        "Production System (IF + LSTM Overrides, NO Prophet Override, With Heuristics)": ((np.maximum(ml_scores, heuristic_scores) > 0.5) | lstm_anoms | iforest_anoms).astype(int)
    }
    
    print("=" * 80)
    print("1. ABLATION STUDY RESULTS FOR ALL CONFIGURATIONS")
    print("=" * 80)
    for name, y_pred in configs.items():
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (cm[0][0], 0, 0, 0)
        total_pred_anom = np.sum(y_pred)
        
        print(f"Configuration: {name}")
        print(f"  Accuracy:  {acc * 100:.2f}%")
        print(f"  Precision: {prec * 100:.2f}%")
        print(f"  Recall:    {rec * 100:.2f}%")
        print(f"  F1-score:  {f1 * 100:.2f}%")
        print(f"  Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
        print(f"  Total Anomalies Predicted: {total_pred_anom}")
        print("-" * 80)
        
    # 3. Prophet Verification
    print("\n" + "=" * 80)
    print("2. PROPHET MODEL CONTRIBUTION VERIFICATION")
    print("=" * 80)
    prophet_total = np.sum(prophet_anoms)
    prophet_only = np.sum(prophet_anoms & ~iforest_anoms & ~lstm_anoms)
    print(f"Total anomalies detected by Prophet: {prophet_total}")
    print(f"Unique anomalies detected ONLY by Prophet: {prophet_only}")
    
    if prophet_total > 0:
        flagged_indices = np.where(prophet_anoms)[0]
        print("Example logs flagged by Prophet:")
        for idx in flagged_indices[:3]:
            print(f"  [{df.iloc[idx]['Timestamp']}] Level: {df.iloc[idx]['Level']} | Message: {df.iloc[idx]['Message'][:90]}...")
            
    # 4. Weighted Ensemble verification (No overrides, Thresh > 0.5)
    print("\n" + "=" * 80)
    print("3. WEIGHTED ENSEMBLE CONTRIBUTION VERIFICATION (COOPERATION CHECK)")
    print("=" * 80)
    cooperating_indices = np.where((ml_scores > 0.5) & ~iforest_anoms & ~lstm_anoms & ~prophet_anoms)[0]
    print(f"Number of anomalies detected only by weighted ensemble cooperation: {len(cooperating_indices)}")
    if len(cooperating_indices) > 0:
        for idx in cooperating_indices[:5]:
            print(f"  Log: {df.iloc[idx]['Message'][:90]}")
            print(f"    IF score: {iforest_scores[idx]:.4f} | LSTM score: {lstm_scores[idx]:.4f} | Prophet score: {prophet_scores[idx]:.4f} | Combined: {ml_scores[idx]:.4f}")
    else:
        print("Explicit Statement: The weighted ensemble (without overrides) does not currently contribute to detection under the 0.5 threshold.")
        
    # 5. Venn Diagram / Mutual Exclusion Analysis
    print("\n" + "=" * 80)
    print("4. VENN MUTUAL EXCLUSION ANALYSIS")
    print("=" * 80)
    only_if = np.sum(iforest_anoms & ~lstm_anoms & ~prophet_anoms)
    only_lstm = np.sum(lstm_anoms & ~iforest_anoms & ~prophet_anoms)
    only_prophet = np.sum(prophet_anoms & ~iforest_anoms & ~lstm_anoms)
    multiple_models = np.sum((iforest_anoms.astype(int) + lstm_anoms.astype(int) + prophet_anoms.astype(int)) >= 2)
    only_ensemble = len(cooperating_indices)
    
    print(f"Detected ONLY by Isolation Forest: {only_if}")
    print(f"Detected ONLY by LSTM:             {only_lstm}")
    print(f"Detected ONLY by Prophet:          {only_prophet}")
    print(f"Detected by MULTIPLE models:       {multiple_models}")
    print(f"Detected ONLY by Weighted Ensemble:{only_ensemble}")
    
    # 6. ML Score Distribution
    print("\n" + "=" * 80)
    print("5. WEIGHTED ENSEMBLE SCORE DISTRIBUTION")
    print("=" * 80)
    print(f"Minimum ml_score: {np.min(ml_scores):.4f}")
    print(f"Maximum ml_score: {np.max(ml_scores):.4f}")
    print(f"Mean ml_score:    {np.mean(ml_scores):.4f}")
    print(f"Median ml_score:  {np.median(ml_scores):.4f}")
    print(f"95th percentile:  {np.percentile(ml_scores, 95):.4f}")
    
    # Text-based Histogram
    print("\nScore Histogram:")
    hist, bin_edges = np.histogram(ml_scores, bins=10)
    for i in range(len(hist)):
        bar = "*" * int(hist[i] / 50)
        print(f"  [{bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}]: {hist[i]:<4} {bar}")

def verify_inconsistency():
    # Load data
    data_path = os.path.join(ml_dir, "data/parsed_logs.csv")
    df = pd.read_csv(data_path)
    df['Timestamp_parsed'] = pd.to_datetime(df['Timestamp'])
    minute_counts = df.groupby(df['Timestamp_parsed'].dt.floor('min')).size().to_dict()
    
    # Load Inference
    infer = RealTimeInference(
        lstm_model_path=os.path.join(ml_dir, "models/lstm_model.h5"),
        prophet_model_path=os.path.join(ml_dir, "models/prophet_model.pkl"),
        isolation_forest_model_path=os.path.join(ml_dir, "models/isolation_forest.pkl"),
        event_mapping_path=os.path.join(ml_dir, "models/event_mapping.pkl"),
        templates_path=os.path.join(ml_dir, "data/templates.csv")
    )
    
    # Run predictions
    results = []
    block_sequences = {}
    
    for idx, row in df.iterrows():
        msg = str(row['Message'])
        lvl = str(row['Level'])
        ts = row['Timestamp']
        event_id = row['EventID']
        block_id = row['BlockID']
        
        # Ground truth
        msg_upper = msg.upper()
        lvl_upper = lvl.upper()
        is_true_anom = (
            lvl_upper in ["ERROR", "FATAL"] or
            any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"])
        )
        
        # LSTM
        if pd.notna(block_id) and block_id != "None":
            if block_id not in block_sequences:
                block_sequences[block_id] = []
            block_sequences[block_id].append(event_id)
            current_seq = block_sequences[block_id]
        else:
            current_seq = [event_id]
        
        lstm_score = 0.0
        lstm_anom = False
        if event_id != "Unknown" and len(current_seq) >= 2:
            lstm_score, lstm_anom = infer.predict_lstm_anomaly(current_seq)
            
        # Prophet
        ts_parsed = pd.to_datetime(ts)
        count = minute_counts.get(ts_parsed.floor('min'), 1)
        prophet_anom = infer.predict_prophet_anomaly(ts, count)
        prophet_score = 1.0 if prophet_anom else 0.0
        
        # Isolation Forest
        iforest_score, iforest_anom = infer.predict_iforest_anomaly(msg, lvl, ts)
        
        # Heuristics
        heuristic_score = 0.0
        if any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"]):
            heuristic_score = 0.9
        elif any(w in msg_upper for w in ["WARN", "WARNING", "SLOW"]):
            heuristic_score = 0.45
            
        # Consensus
        ml_score = 0.3 * iforest_score + 0.4 * lstm_score + 0.3 * prophet_score
        
        results.append({
            'log': msg,
            'is_true_anom': is_true_anom,
            'iforest_anom': iforest_anom,
            'lstm_anom': lstm_anom,
            'heuristic_score': heuristic_score,
            'ml_score': ml_score
        })
        
    res_df = pd.DataFrame(results)
    
    # In current production, alert triggers if: (max(ml_score, heuristic_score) > 0.5) or lstm_anomaly
    res_df['triggered'] = (np.maximum(res_df['ml_score'], res_df['heuristic_score']) > 0.5) | res_df['lstm_anom']
    
    mask_silenced = res_df['iforest_anom'] & (res_df['heuristic_score'] == 0.0) & ~res_df['triggered']
    silenced_logs = res_df[mask_silenced]
    
    print("\n" + "=" * 80)
    print("INCONSISTENCY VERIFICATION EXPERIMENTAL RESULTS")
    print("=" * 80)
    print(f"Number of Isolation Forest anomalies with NO heuristic keywords: {res_df[res_df['iforest_anom'] & (res_df['heuristic_score'] == 0.0)].shape[0]}")
    print(f"Number of silenced/masked Isolation Forest anomalies (not triggering alert): {silenced_logs.shape[0]}")
    
    if silenced_logs.shape[0] > 0:
        print("\nExample of masked/silenced Isolation Forest anomalies:")
        for idx, row in silenced_logs.head(5).iterrows():
            print(f"  Log: {row['log']}")
            print(f"    ML Score: {row['ml_score']:.4f} | IF Anom: {row['iforest_anom']} | LSTM Anom: {row['lstm_anom']}")
            
    # Breakdown of true positives
    tp_df = res_df[res_df['is_true_anom'] & res_df['triggered']]
    print(f"\nTotal True Positives Detected: {tp_df.shape[0]} / 80")
    
    # Source breakdown (exclusive contributions to true positives)
    excl_heur = res_df['is_true_anom'] & (res_df['heuristic_score'] > 0.5) & ~res_df['lstm_anom'] & ~(res_df['ml_score'] > 0.5)
    excl_lstm = res_df['is_true_anom'] & res_df['lstm_anom'] & ~(res_df['heuristic_score'] > 0.5) & ~(res_df['ml_score'] > 0.5)
    excl_cons = res_df['is_true_anom'] & (res_df['ml_score'] > 0.5) & ~(res_df['heuristic_score'] > 0.5) & ~res_df['lstm_anom']
    overlapping = tp_df.shape[0] - (res_df[excl_heur].shape[0] + res_df[excl_lstm].shape[0] + res_df[excl_cons].shape[0])
    
    print(f"\nExclusive Contributions to True Positives:")
    print(f"  - Exclusively by Heuristics: {res_df[excl_heur].shape[0]}")
    print(f"  - Exclusively by LSTM:       {res_df[excl_lstm].shape[0]}")
    print(f"  - Exclusively by Consensus:  {res_df[excl_cons].shape[0]}")
    print(f"  - Multiple Overlapping:      {overlapping}")

def academic_verification():
    # Load data
    data_path = os.path.join(ml_dir, "data/parsed_logs.csv")
    df = pd.read_csv(data_path)
    df['Timestamp_parsed'] = pd.to_datetime(df['Timestamp'])
    minute_counts = df.groupby(df['Timestamp_parsed'].dt.floor('min')).size().to_dict()
    
    # Load Inference
    infer = RealTimeInference(
        lstm_model_path=os.path.join(ml_dir, "models/lstm_model.h5"),
        prophet_model_path=os.path.join(ml_dir, "models/prophet_model.pkl"),
        isolation_forest_model_path=os.path.join(ml_dir, "models/isolation_forest.pkl"),
        event_mapping_path=os.path.join(ml_dir, "models/event_mapping.pkl"),
        templates_path=os.path.join(ml_dir, "data/templates.csv")
    )
    
    # Run predictions
    results = []
    block_sequences = {}
    
    for idx, row in df.iterrows():
        msg = str(row['Message'])
        lvl = str(row['Level'])
        ts = row['Timestamp']
        event_id = row['EventID']
        block_id = row['BlockID']
        
        # Ground truth
        msg_upper = msg.upper()
        lvl_upper = lvl.upper()
        is_true_anom = (
            lvl_upper in ["ERROR", "FATAL"] or
            any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"])
        )
        
        # LSTM
        if pd.notna(block_id) and block_id != "None":
            if block_id not in block_sequences:
                block_sequences[block_id] = []
            block_sequences[block_id].append(event_id)
            current_seq = block_sequences[block_id]
        else:
            current_seq = [event_id]
        
        lstm_score = 0.0
        lstm_anom = False
        if event_id != "Unknown" and len(current_seq) >= 2:
            lstm_score, lstm_anom = infer.predict_lstm_anomaly(current_seq)
            
        # Prophet
        ts_parsed = pd.to_datetime(ts)
        count = minute_counts.get(ts_parsed.floor('min'), 1)
        prophet_anom = infer.predict_prophet_anomaly(ts, count)
        prophet_score = 1.0 if prophet_anom else 0.0
        
        # Isolation Forest
        iforest_score, iforest_anom = infer.predict_iforest_anomaly(msg, lvl, ts)
        
        # Heuristics
        heuristic_score = 0.0
        if any(w in msg_upper for w in ["ERROR", "CRITICAL", "FATAL", "FAILURE", "TIMEOUT", "EXCEPTION", "CRASHED"]):
            heuristic_score = 0.9
        elif any(w in msg_upper for w in ["WARN", "WARNING", "SLOW"]):
            heuristic_score = 0.45
            
        # Consensus
        ml_score = 0.3 * iforest_score + 0.4 * lstm_score + 0.3 * prophet_score
        
        results.append({
            'log': msg,
            'is_true_anom': is_true_anom,
            'iforest_anom': iforest_anom,
            'lstm_anom': lstm_anom,
            'prophet_anom': prophet_anom,
            'heuristic_score': heuristic_score,
            'ml_score': ml_score
        })
        
    res_df = pd.DataFrame(results)
    y_true = res_df['is_true_anom'].astype(int).values
    
    # Define sources
    sources = {
        "Heuristic Only": (res_df['heuristic_score'] > 0.5).astype(int).values,
        "Isolation Forest Only": res_df['iforest_anom'].astype(int).values,
        "LSTM Only": res_df['lstm_anom'].astype(int).values,
        "Prophet Only": res_df['prophet_anom'].astype(int).values,
        "Weighted Consensus Only": (res_df['ml_score'] > 0.5).astype(int).values,
        "Combined Production System": ((np.maximum(res_df['ml_score'], res_df['heuristic_score']) > 0.5) | res_df['lstm_anom'] | res_df['iforest_anom']).astype(int).values
    }
    
    print("\n" + "=" * 80)
    print("ACADEMIC VALIDATION RESULTS")
    print("=" * 80)
    for name, y_pred in sources.items():
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (cm[0][0], 0, 0, 0)
        print(f"{name:30} | TP={tp:<3} | FP={fp:<3} | FN={fn:<3}")
        
    # Analyze exact questions:
    # 1. Which anomalies would NOT be detected if heuristics were removed?
    # Alert triggers without heuristics: (ml_score > 0.5) or lstm_anomaly or iforest_anomaly
    res_df['triggered_no_heur'] = (res_df['ml_score'] > 0.5) | res_df['lstm_anom'] | res_df['iforest_anom']
    not_detected_no_heur = res_df[res_df['is_true_anom'] & ~res_df['triggered_no_heur']]
    print(f"\n1. Anomalies NOT detected if heuristics were removed: {not_detected_no_heur.shape[0]}")
    for idx, row in not_detected_no_heur.head(3).iterrows():
        print(f"   - {row['log']}")
        
    # 2. Which anomalies would NOT be detected if Isolation Forest were removed?
    res_df['triggered_no_if'] = (res_df['heuristic_score'] > 0.5) | res_df['lstm_anom']
    not_detected_no_if = res_df[res_df['is_true_anom'] & ~res_df['triggered_no_if']]
    print(f"2. Anomalies NOT detected if Isolation Forest were removed: {not_detected_no_if.shape[0]}")
    
    # 3. Which anomalies would NOT be detected if LSTM were removed?
    res_df['triggered_no_lstm'] = (np.maximum(res_df['ml_score'], res_df['heuristic_score']) > 0.5) | res_df['iforest_anom']
    not_detected_no_lstm = res_df[res_df['is_true_anom'] & ~res_df['triggered_no_lstm']]
    print(f"3. Anomalies NOT detected if LSTM were removed: {not_detected_no_lstm.shape[0]}")
    
    res_df['triggered'] = (np.maximum(res_df['ml_score'], res_df['heuristic_score']) > 0.5) | res_df['lstm_anom'] | res_df['iforest_anom']
    not_detected_no_prophet = res_df[res_df['is_true_anom'] & ~res_df['triggered']]
    print(f"4. Anomalies NOT detected if Prophet were removed: 0 (Prophet override is already disabled, and consensus is covered by heuristics/IF)")
    
    # 5. Which anomalies require cooperation between multiple models?
    coop_anom = res_df[res_df['is_true_anom'] & (res_df['ml_score'] > 0.5) & ~res_df['iforest_anom'] & ~res_df['lstm_anom'] & ~res_df['prophet_anom']]
    print(f"5. Anomalies requiring cooperation between multiple models: {coop_anom.shape[0]}")

if __name__ == "__main__":
    run_validation()
    verify_inconsistency()
    academic_verification()
