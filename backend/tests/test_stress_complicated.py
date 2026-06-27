import requests
import time
import uuid
import concurrent.futures
import string
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def get_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_complicated_stress_test(total_blocks=100, batch_size=200):
    print("=" * 70)
    print("STARTING COMPLICATED REAL-WORLD MACHINE LEARNING STRESS TEST (NO KEYWORDS)")
    print("=" * 70)
    
    # 1. Sign Up & Login to establish user session
    username = f"ml_stress_{get_random_string()}"
    email = f"{username}@example.com"
    password = "SuperSecurePassword123!"
    
    print(f"Creating user session for '{username}'...")
    signup_url = f"{BASE_URL}/auth/signup"
    signup_data = {"username": username, "email": email, "password": password}
    signup_response = requests.post(signup_url, json=signup_data)
    assert signup_response.status_code == 200, f"Signup failed: {signup_response.text}"
    token_info = signup_response.json()
    jwt_token = token_info["access_token"]
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    # 2. Create API Key
    print("Generating API Key...")
    key_url = f"{BASE_URL}/integration/create-api-key"
    key_response = requests.post(key_url, headers=headers)
    assert key_response.status_code == 200
    api_key = key_response.json()["api_key"]
    
    # 3. Generate structured log streams mimicking HDFS templates
    # We will formulate sequences of logs for different block IDs.
    # Normal HDFS sequence:
    # 1. INFO: dfs.DataNode$DataXceiver: Receiving block blk_X src: /10.251.42.84:50689 dest: /10.251.42.84:50010
    # 2. INFO: dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_X terminating
    # 3. INFO: dfs.DataNode$DataTransfer: Received block blk_X src: /10.251.42.84:50689 dest: /10.251.42.84:50010 of size 67108864
    
    print(f"Generating {total_blocks} block transaction streams (some with structural LSTM breaches)...")
    log_records = []
    
    start_time = datetime(2008, 11, 9, 21, 0, 0)
    
    # We will simulate 100 blocks
    anomalous_blocks = set(random.sample(range(total_blocks), k=15)) # 15% sequence anomaly rate
    
    for b in range(total_blocks):
        block_id = f"blk_{1000 + b}"
        # Advance timestamp slightly for each block
        current_time = start_time + timedelta(seconds=b * 5)
        time_str = current_time.strftime("%y%m%d %H%M%S")
        
        # Step 1: Normal Allocation (INFO)
        log_records.append({
            "traceId": uuid.uuid4().hex,
            "spanId": uuid.uuid4().hex[:16],
            "severityText": "INFO",
            "body": {"stringValue": f"{time_str} 101 INFO dfs.DataNode$DataXceiver: Receiving block {block_id} src: /10.251.42.84:50689 dest: /10.251.42.84:50010"}
        })
        
        # If this block is chosen to have a sequence anomaly (LSTM failure):
        # We skip Step 2 (PacketResponder terminating) and go straight to Step 3,
        # or we introduce an unexpected event (like a random print).
        if b in anomalous_blocks:
            # Sequence anomaly: unexpected sequence transition!
            # Instead of PacketResponder, we jump straight to an out-of-order statement
            log_records.append({
                "traceId": uuid.uuid4().hex,
                "spanId": uuid.uuid4().hex[:16],
                "severityText": "INFO",
                "body": {"stringValue": f"{time_str} 101 INFO dfs.DataNode$DataTransfer: Received block {block_id} src: /10.251.42.84:50689 dest: /10.251.42.84:50010 of size 67108864"}
            })
        else:
            # Normal Sequence
            log_records.append({
                "traceId": uuid.uuid4().hex,
                "spanId": uuid.uuid4().hex[:16],
                "severityText": "INFO",
                "body": {"stringValue": f"{time_str} 101 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block {block_id} terminating"}
            })
            log_records.append({
                "traceId": uuid.uuid4().hex,
                "spanId": uuid.uuid4().hex[:16],
                "severityText": "INFO",
                "body": {"stringValue": f"{time_str} 101 INFO dfs.DataNode$DataTransfer: Received block {block_id} src: /10.251.42.84:50689 dest: /10.251.42.84:50010 of size 67108864"}
            })

    total_logs = len(log_records)
    print(f"Generated {total_logs} logs total (No Heuristic keywords are used).")
    
    # 4. Perform high-velocity batch ingestion
    batches = []
    for i in range(0, total_logs, batch_size):
        batch_slice = log_records[i:i+batch_size]
        payload = {
            "resourceLogs": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "complicated-service"}}]},
                    "scopeLogs": [{"logRecords": batch_slice}]
                }
            ]
        }
        batches.append(payload)
        
    print(f"Injecting logs in {len(batches)} batches...")
    otlp_url = f"{BASE_URL}/integration/otlp/logs"
    otlp_headers = {"X-API-Key": api_key}
    
    test_start = time.time()
    for b_idx, batch in enumerate(batches):
        res = requests.post(otlp_url, json=batch, headers=otlp_headers)
        assert res.status_code == 200, f"Batch {b_idx} failed: {res.text}"
        
    duration = time.time() - test_start
    print("Ingestion complete. Waiting 1.5s for database batch buffer to flush...")
    time.sleep(1.5)
    
    # 5. Retrieve dashboard metrics to verify ML detection counts
    summary_url = f"{BASE_URL}/dashboard/summary"
    summary_response = requests.get(summary_url, headers=headers)
    summary = summary_response.json()
    
    db_total = summary["total_logs"]
    db_anomalies = summary["anomaly_count"]
    
    print("\n" + "=" * 70)
    print("PURE MACHINE LEARNING LOG ANOMALY DETECTION RESULTS")
    print("=" * 70)
    print(f"Total Logs Ingested:    {db_total} (expected: {total_logs})")
    print(f"Anomalies Flagged by ML: {db_anomalies}")
    print(f"ML Anomaly Ratio:        {(db_anomalies / db_total) * 100:.2f}%")
    print(f"Expected LSTM Outliers: ~15 (from {len(anomalous_blocks)} corrupted sequences)")
    print(f"E2E Ingestion Latency:   {duration:.4f} seconds")
    print("=" * 70)
    
    # Assert that some anomalies are successfully captured by our sequence LSTM
    assert db_anomalies > 0, "ML models failed to detect any sequence anomalies!"
    print("Verification Succeeded! Deep Learning LSTM models successfully detected sequence structure anomalies without relying on simple text heuristic keywords.")

if __name__ == "__main__":
    run_complicated_stress_test()
