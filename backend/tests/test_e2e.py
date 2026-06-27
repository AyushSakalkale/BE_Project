import requests
import random
import string
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

def get_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_e2e_tests():
    print("=" * 60)
    print("STARTING END-TO-END ANOMALYAI INTEGRATION WORKFLOW")
    print("=" * 60)
    
    # Generate unique user details
    username = f"user_{get_random_string()}"
    email = f"{username}@example.com"
    password = "SuperSecurePassword123!"
    
    # 1. Sign Up
    print("\n[Step 1] Creating a new user via /auth/signup...")
    signup_url = f"{BASE_URL}/auth/signup"
    signup_data = {
        "username": username,
        "email": email,
        "password": password
    }
    signup_response = requests.post(signup_url, json=signup_data)
    assert signup_response.status_code == 200, f"Signup failed: {signup_response.text}"
    token_info = signup_response.json()
    assert "access_token" in token_info, "access_token missing in signup response"
    print(f"-> Success! Registered user '{username}' and received access token.")
    
    # 2. Login
    print("\n[Step 2] Authenticating via OAuth2 /auth/login...")
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "username": username,
        "password": password
    }
    login_response = requests.post(login_url, data=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_token_info = login_response.json()
    jwt_token = login_token_info["access_token"]
    headers = {"Authorization": f"Bearer {jwt_token}"}
    print("-> Success! Logged in and established JWT headers.")
    
    # 3. Paste Logs (Bulk Ingestion)
    print("\n[Step 3] Pasting a batch of normal and anomalous logs via /logs/paste...")
    paste_url = f"{BASE_URL}/logs/paste"
    sample_logs = [
        "081109 203518 143 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1608999687919862906",
        "081109 203519 143 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1608999687919862906",
        "081109 203520 143 ERROR dfs.DataNode$DataXceiver: Failed to write block blk_-1608999687919862906",
        "081109 203521 143 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1608999687919862907",
        "081109 203522 143 FATAL dfs.DataNode$DataXceiver: Connection timed out block blk_-1608999687919862907"
    ]
    paste_data = {
        "logs": sample_logs,
        "service": "hdfs-ingest"
    }
    paste_response = requests.post(paste_url, json=paste_data, headers=headers)
    assert paste_response.status_code == 200, f"Paste logs failed: {paste_response.text}"
    paste_results = paste_response.json()
    assert len(paste_results) == len(sample_logs), "Not all logs were processed"
    
    print("\nIngestion Results:")
    anomalies_detected = 0
    for idx, res in enumerate(paste_results):
        msg = res["message"]
        score = res["score"]
        is_anomaly = res["is_anomaly"]
        explanation = res["explanation"]
        
        print(f"Log {idx+1}: {msg[:45]}...")
        print(f"  - Anomaly Score: {score}")
        print(f"  - Flagged Anomaly: {is_anomaly}")
        print(f"  - AI Explanation: {explanation}")
        
        if is_anomaly:
            anomalies_detected += 1
            
    # Heuristics check: ERROR/FATAL logs must be classified as anomalies (score > 0.5)
    assert paste_results[2]["is_anomaly"] is True, "ERROR log was not flagged as anomaly"
    assert paste_results[4]["is_anomaly"] is True, "FATAL log was not flagged as anomaly"
    assert anomalies_detected == 2, f"Expected 2 anomalies, found {anomalies_detected}"
    print(f"-> Success! Successfully ingested logs. Detected {anomalies_detected}/5 anomalies as expected.")
    
    # 4. Generate API Key
    print("\n[Step 4] Generating microservice API Key via /integration/create-api-key...")
    key_url = f"{BASE_URL}/integration/create-api-key"
    key_response = requests.post(key_url, headers=headers)
    assert key_response.status_code == 200, f"API key generation failed: {key_response.text}"
    api_key = key_response.json()["api_key"]
    print(f"-> Success! Generated API Key: {api_key}")
    
    # 5. Ingest Single Log with API Key
    print("\n[Step 5] Ingesting a single log via /logs/ingest-log using the X-API-Key header...")
    ingest_url = f"{BASE_URL}/logs/ingest-log"
    ingest_headers = {"X-API-Key": api_key}
    
    # Ingest a normal log
    ingest_data_normal = {
        "service": "k8s-pod-1",
        "message": "081109 203530 143 INFO dfs.DataNode$DataXceiver: Receiving block blk_-9999",
        "level": "INFO"
    }
    ingest_response = requests.post(ingest_url, json=ingest_data_normal, headers=ingest_headers)
    assert ingest_response.status_code == 200, f"Microservice ingestion failed: {ingest_response.text}"
    ingest_normal_res = ingest_response.json()
    assert ingest_normal_res["is_anomaly"] is False, "Normal log was incorrectly flagged as anomaly"
    print("-> Normal log successfully processed and scored.")
    
    # Ingest an error log
    ingest_data_error = {
        "service": "k8s-pod-1",
        "message": "081109 203531 143 ERROR dfs.DataNode$DataXceiver: Disk crash detected",
        "level": "ERROR"
    }
    ingest_response_error = requests.post(ingest_url, json=ingest_data_error, headers=ingest_headers)
    assert ingest_response_error.status_code == 200, f"Microservice ingestion failed: {ingest_response_error.text}"
    ingest_error_res = ingest_response_error.json()
    assert ingest_error_res["is_anomaly"] is True, "Critical error log was not flagged as anomaly"
    print("-> Anomalous log successfully processed, scored, and flagged.")
    
    # 6. Upload File
    print("\n[Step 6] Uploading a log file via /logs/upload...")
    upload_url = f"{BASE_URL}/logs/upload"
    file_content = (
        "081109 203540 INFO Receiving block blk_100\n"
        "081109 203541 ERROR Failed to write block blk_100\n"
    )
    files = {'file': ('test.log', file_content)}
    upload_response = requests.post(upload_url, files=files, headers=headers)
    assert upload_response.status_code == 200, f"Upload file failed: {upload_response.text}"
    print(f"-> Success! Ingested log file. Response: {upload_response.json()}")

    # 7. Retrieve Dashboard Summary and Recent Logs
    print("\n[Step 7] Verifying dashboard aggregates via /dashboard/summary...")
    summary_url = f"{BASE_URL}/dashboard/summary"
    summary_response = requests.get(summary_url, headers=headers)
    assert summary_response.status_code == 200, f"Summary failed: {summary_response.text}"
    summary = summary_response.json()
    
    assert summary["total_logs"] == 9, f"Expected 9 logs total (5 from bulk + 2 from API Key + 2 from File), got {summary['total_logs']}"
    assert summary["anomaly_count"] == 4, f"Expected 4 anomalies total (2 from bulk + 1 from API Key + 1 from File), got {summary['anomaly_count']}"
    print("-> Success! Dashboard summary stats match exactly.")
    
    # 8. Retrieve Recent Logs
    print("\n[Step 8] Checking recent logs table via /dashboard/recent...")
    recent_url = f"{BASE_URL}/dashboard/recent?limit=100"
    recent_response = requests.get(recent_url, headers=headers)
    assert recent_response.status_code == 200, f"Recent logs failed: {recent_response.text}"
    recent_logs = recent_response.json()
    assert len(recent_logs) == 9, f"Expected 9 recent log entries, got {len(recent_logs)}"
    print("-> Success! Verified all 9 logs are retrievable.")

    # 9. Ingest OpenTelemetry OTLP structured log payload
    print("\n[Step 9] Ingesting OpenTelemetry OTLP JSON logs via /integration/otlp/logs...")
    otlp_url = f"{BASE_URL}/integration/otlp/logs"
    otlp_payload = {
        "resourceLogs": [
          {
            "resource": {
              "attributes": [{"key": "service.name", "value": {"stringValue": "auth-service-otel"}}]
            },
            "scopeLogs": [
              {
                "logRecords": [
                  {
                    "traceId": "0af7651916cd43dd8448eb211c80319c",
                    "spanId": "b5c841381d8d9efd",
                    "severityText": "INFO",
                    "body": {"stringValue": "081109 203600 INFO User auth-service: Login successful for user_mlavscby"}
                  },
                  {
                    "traceId": "0af7651916cd43dd8448eb211c80319c",
                    "spanId": "b5c841381d8d9efe",
                    "severityText": "ERROR",
                    "body": {"stringValue": "081109 203601 ERROR User auth-service: Failed database replication heartbeat"}
                  }
                ]
              }
            ]
          }
        ]
    }
    otlp_response = requests.post(otlp_url, json=otlp_payload, headers={"X-API-Key": api_key})
    assert otlp_response.status_code == 200, f"OTLP ingestion failed: {otlp_response.text}"
    assert otlp_response.json()["processed_records"] == 2, f"Expected 2 processed records, got {otlp_response.json()}"
    print("-> Success! OTLP JSON ingestion payload parsed and processed successfully.")
    
    # Wait for the bulk batcher to write logs to DB
    print("Waiting 0.3s for DB batch worker to flush OTel logs...")
    time.sleep(0.3)

    # 10. Verify updated Dashboard aggregates
    print("\n[Step 10] Verifying updated dashboard aggregates after OTLP Ingestion...")
    summary_response = requests.get(summary_url, headers=headers)
    assert summary_response.status_code == 200, f"Summary failed: {summary_response.text}"
    summary = summary_response.json()
    assert summary["total_logs"] == 11, f"Expected 11 logs total (9 + 2 OTel), got {summary['total_logs']}"
    assert summary["anomaly_count"] == 5, f"Expected 5 anomalies total (4 + 1 OTel error), got {summary['anomaly_count']}"
    print("-> Success! Dashboard summary updated counts verify trace aggregation.")

    # 11. Verify updated recent logs trace IDs
    print("\n[Step 11] Verifying trace correlation in recent logs table...")
    recent_response = requests.get(recent_url, headers=headers)
    assert recent_response.status_code == 200, f"Recent logs failed: {recent_response.text}"
    recent_logs = recent_response.json()
    assert len(recent_logs) == 11, f"Expected 11 recent log entries, got {len(recent_logs)}"
    # Check if the most recent log (the OTel ERROR one) has the correct trace_id
    otel_error_log = recent_logs[0]  # Lifo order
    assert otel_error_log["trace_id"] == "0af7651916cd43dd8448eb211c80319c", f"Trace ID not propagated correctly, got {otel_error_log['trace_id']}"
    assert otel_error_log["span_id"] == "b5c841381d8d9efe", f"Span ID not propagated correctly, got {otel_error_log['span_id']}"
    print("-> Success! OpenTelemetry Trace ID and Span ID verified in database logs.")

    # 12. Stress Test Ingestion of 1,000 Logs
    print("\n[Step 12] Stress testing high-velocity ingestion (sending 1,000 logs in a single payload)...")
    stress_log_records = []
    for i in range(1000):
        stress_log_records.append({
            "traceId": uuid.uuid4().hex,
            "spanId": uuid.uuid4().hex[:16],
            "severityText": "INFO",
            "body": {"stringValue": f"081109 203610 INFO dfs.DataNode: Stress log message index={i}"}
        })
    stress_payload = {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [{"key": "service.name", "value": {"stringValue": "stress-test-service"}}]
                },
                "scopeLogs": [
                    {
                        "logRecords": stress_log_records
                    }
                ]
            }
        ]
    }
    
    start_time = time.time()
    stress_response = requests.post(otlp_url, json=stress_payload, headers={"X-API-Key": api_key})
    latency = time.time() - start_time
    assert stress_response.status_code == 200, f"Stress test failed: {stress_response.text}"
    assert stress_response.json()["processed_records"] == 1000, "Not all logs were processed in stress test"
    print(f"-> Ingestion API responded in {latency:.4f} seconds (highly concurrent).")
    
    # Wait for the bulk writer to flush
    print("Waiting 0.5s for DB batch worker to flush queue...")
    time.sleep(0.5)
    
    # Verify DB contains all 1,011 logs
    summary_response = requests.get(summary_url, headers=headers)
    summary = summary_response.json()
    print(f"Post-Stress Total Logs: {summary['total_logs']}")
    assert summary["total_logs"] == 1011, f"Expected 1011 logs total, got {summary['total_logs']}"
    print("-> Success! Database successfully saved all 1,000 logs via bulk batch insertion.")

    print("\n" + "=" * 60)
    print("ALL TESTCASES PASSED SUCCESSFULLY! END-TO-END WORKFLOW VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_tests()
