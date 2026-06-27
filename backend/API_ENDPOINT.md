# API Documentation: Log Anomaly Detection System

This document outlines the available endpoints for the FastAPI backend, including request/response formats and authentication requirements.

## Base URL
`http://localhost:8000`

---

## 1. Authentication (`/auth`)

### **Signup**
- **Endpoint**: `/auth/signup`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword"
  }
  ```
- **Response**: `{"access_token": "...", "token_type": "bearer"}`

### **Login**
- **Endpoint**: `/auth/login`
- **Method**: `POST`
- **Body**: `OAuth2 Form Data` (username, password)
- **Response**: `{"access_token": "...", "token_type": "bearer"}`

---

## 2. Log Management (`/logs`)

### **Paste Logs**
- **Endpoint**: `/logs/paste`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body**:
  ```json
  {
    "logs": ["raw log string 1", "raw log string 2"],
    "service": "optional-service-name"
  }
  ```
- **Description**: Uses hybrid ML (LSTM+Prophet) for scoring and HuggingFace for anomaly explanations.

### **Upload Log File**
- **Endpoint**: `/logs/upload`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body**: `Multipart File Upload` (key: "file")
- **Description**: Batch processes `.log` or `.txt` files.

### **Ingest Single Log (Microservice)**
- **Endpoint**: `/logs/ingest-log`
- **Method**: `POST`
- **Headers**: `X-API-Key: <YOUR_API_KEY>`
- **Body**:
  ```json
  {
    "service": "web-server-1",
    "message": "081109 203518 INFO Receiving block blk_123",
    "timestamp": "optional-ISO-string",
    "level": "INFO"
  }
  ```
- **Response**: `{"score": 0.05, "is_anomaly": false, "explanation": null}`

---

## 3. Dashboard & Analytics (`/dashboard`)

### **Summary Stats**
- **Endpoint**: `/dashboard/summary`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response**:
  ```json
  {
    "total_logs": 1250,
    "anomaly_count": 45,
    "anomaly_percentage": 3.6
  }
  ```

---

## 4. Integrations (`/integration`)

### **Generate API Key**
- **Endpoint**: `/integration/create-api-key`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response**: `{"api_key": "your_generated_secret_key"}`

### **Connect External Service**
- **Endpoint**: `/integration/connect`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body**: `{"type": "webhook", "url": "https://..."}`

---

## Error Handling
- **401 Unauthorized**: Missing or invalid JWT token.
- **404 Not Found**: Endpoint does not exist.
- **422 Unprocessable Entity**: Missing required fields in JSON body.
- **500 Internal Server Error**: Unexpected server-side failure.
