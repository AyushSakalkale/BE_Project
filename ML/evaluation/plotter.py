import matplotlib.pyplot as plt
import os

def plot_loss(history, out_dir="evaluation/plots"):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['loss'], label='Train Loss')
    if 'val_loss' in history.history:
        plt.plot(history.history['val_loss'], label='Val Loss')
    plt.title('Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.savefig(os.path.join(out_dir, "lstm_loss.png"))
    plt.close()

def plot_prophet_forecast(df_result, out_dir="evaluation/plots"):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    plt.figure(figsize=(12, 6))
    plt.plot(df_result['ds'], df_result['y'], 'k.', label='Actual')
    plt.plot(df_result['ds'], df_result['yhat'], 'b-', label='Forecast')
    plt.fill_between(df_result['ds'], df_result['yhat_lower'], df_result['yhat_upper'], color='blue', alpha=0.2, label='Confidence Interval')
    
    # Mark anomalies
    anomalies = df_result[df_result['anomaly']]
    plt.plot(anomalies['ds'], anomalies['y'], 'ro', label='Anomaly')
    
    plt.title('Prophet Anomaly Detection')
    plt.xlabel('Timestamp')
    plt.ylabel('Log Count')
    plt.legend()
    plt.savefig(os.path.join(out_dir, "prophet_anomalies.png"))
    plt.close()
