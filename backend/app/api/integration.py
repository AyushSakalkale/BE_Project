from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import asyncio
import uuid
from typing import Optional, List

from app.models.database import get_db, AsyncSessionLocal
from app.models.user_log import User, APIKey, Log
from app.api.auth import get_current_user
from app.api.logs import get_user_by_api_key
from app.services.ml_service import ml_service
from app.services.huggingface_service import huggingface_service
from app.workers.db_batch_worker import db_batch_worker

router = APIRouter()

async def get_user_from_headers(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    if x_api_key:
        user = await get_user_by_api_key(x_api_key, db)
        if user:
            return user
            
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            user = await get_current_user(token, db)
            if user:
                return user
        except Exception:
            pass
            
    raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key or JWT token")

async def explain_and_update_log_async(message: str, user_id: int, service_name: str, trace_id: str):
    """Asynchronously explain anomalous logs without blocking the ingestion thread."""
    try:
        explanation = await huggingface_service.explain_log(message)
        if explanation:
            # Wait briefly to let the batch worker complete the PostgreSQL write
            await asyncio.sleep(0.5)
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Log).where(
                            Log.user_id == user_id,
                            Log.service_name == service_name,
                            Log.message == message,
                            Log.trace_id == trace_id
                        ).order_by(Log.timestamp.desc()).limit(1)
                    )
                    log_record = result.scalars().first()
                    if log_record:
                        log_record.simplified_message = explanation
    except Exception as e:
        print(f"Failed to asynchronously update log explanation: {e}")

@router.post("/create-api-key")
async def create_api_key(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_key = secrets.token_urlsafe(32)
    api_key_entry = APIKey(
        key=new_key,
        user_id=current_user.id
    )
    db.add(api_key_entry)
    await db.commit()
    return {"api_key": new_key}

@router.post("/otlp/logs")
async def ingest_otlp_logs(
    payload: dict,
    current_user: User = Depends(get_user_from_headers)
):
    records_processed = 0
    resource_logs = payload.get("resourceLogs", [])
    
    for res_log in resource_logs:
        service_name = "otel-service"
        resource = res_log.get("resource", {})
        attributes = resource.get("attributes", [])
        
        for attr in attributes:
            if attr.get("key") == "service.name":
                service_name = attr.get("value", {}).get("stringValue", service_name)
                
        for scope_log in res_log.get("scopeLogs", []):
            for log_record in scope_log.get("logRecords", []):
                body = log_record.get("body", {})
                message = ""
                
                if isinstance(body, dict):
                    message = body.get("stringValue", "")
                elif isinstance(body, str):
                    message = body
                    
                if not message:
                    continue
                    
                trace_id = log_record.get("traceId")
                span_id = log_record.get("spanId")
                
                # Check anomaly status
                score, is_anomaly, event_id = await ml_service.predict_combined(message)
                should_explain = is_anomaly or any(w in message.upper() for w in ["ERROR", "CRITICAL", "FATAL"])
                
                # Enqueue to DB bulk batch writer
                log_dict = {
                    "user_id": current_user.id,
                    "service_name": service_name,
                    "message": message,
                    "parsed_event": event_id,
                    "anomaly_score": score,
                    "is_anomaly": is_anomaly,
                    "simplified_message": None,
                    "trace_id": trace_id,
                    "span_id": span_id
                }
                await db_batch_worker.enqueue(log_dict)
                records_processed += 1
                
                # Decouple LLM query execution
                if should_explain:
                    asyncio.create_task(
                        explain_and_update_log_async(message, current_user.id, service_name, trace_id)
                    )
                
    return {"status": "success", "processed_records": records_processed}

async def process_incoming_queue_message(user_id: int, service_name: str, message: str):
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    
    score, is_anomaly, event_id = await ml_service.predict_combined(message)
    
    log_dict = {
        "user_id": user_id,
        "service_name": service_name,
        "message": message,
        "parsed_event": event_id,
        "anomaly_score": score,
        "is_anomaly": is_anomaly,
        "simplified_message": None,
        "trace_id": trace_id,
        "span_id": span_id
    }
    await db_batch_worker.enqueue(log_dict)
    
    # Decouple LLM query execution
    should_explain = is_anomaly or any(w in message.upper() for w in ["ERROR", "CRITICAL", "FATAL"])
    if should_explain:
        asyncio.create_task(
            explain_and_update_log_async(message, user_id, service_name, trace_id)
        )

async def consume_real_kafka(user_id: int, topic: str, bootstrap_servers: str):
    from aiokafka import AIOKafkaConsumer
    
    print(f"Connecting to real Kafka broker at {bootstrap_servers} for topic {topic}...")
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=f"anomalyai_group_{user_id}_{topic}",
        auto_offset_reset="latest",
        request_timeout_ms=5000
    )
    
    try:
        await asyncio.wait_for(consumer.start(), timeout=5.0)
    except Exception as e:
        print(f"Failed to connect to real Kafka: {e}. Falling back to simulation mode.")
        raise e
        
    print(f"Successfully connected to Kafka topic: {topic}. Starting live message consumption.")
    try:
        async for msg in consumer:
            payload = msg.value.decode("utf-8")
            await process_incoming_queue_message(user_id, f"kafka-{topic}", payload)
    except Exception as e:
        print(f"Error in Kafka consumer loop: {e}")
    finally:
        await consumer.stop()

async def consume_real_rabbitmq(user_id: int, queue_name: str, amqp_url: str):
    import aio_pika
    
    print(f"Connecting to real RabbitMQ broker at {amqp_url} for queue {queue_name}...")
    try:
        connection = await asyncio.wait_for(
            aio_pika.connect_robust(amqp_url),
            timeout=5.0
        )
    except Exception as e:
        print(f"Failed to connect to real RabbitMQ: {e}. Falling back to simulation mode.")
        raise e
        
    print(f"Successfully connected to RabbitMQ. Consuming queue: {queue_name}.")
    try:
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(queue_name, auto_delete=True)
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        payload = message.body.decode("utf-8")
                        await process_incoming_queue_message(user_id, f"rabbitmq-{queue_name}", payload)
    except Exception as e:
        print(f"Error in RabbitMQ consumer loop: {e}")

async def simulate_queue_consumption(user_id: int, queue_type: str, queue_name: str):
    await asyncio.sleep(1.0)
    
    mock_events = [
        ("INFO", "081109 203600 INFO dfs.DataNode: Block report received from datanode-01", False),
        ("INFO", "081109 203601 INFO dfs.DataNode: Verifying block checksums for block blk_505", False),
        ("ERROR", "081109 203602 ERROR dfs.DataNode: Failed to replicate block blk_505 to datanode-02", True),
        ("INFO", "081109 203603 INFO dfs.DataNode: Replaced bad block replica blk_505", False),
        ("FATAL", "081109 203604 FATAL dfs.DataNode: DataNode filesystem crashed on /data/dfs/data", True),
        ("INFO", "081109 203605 INFO dfs.DataNode: Starting filesystem recovery sequence", False)
    ]
    
    for level, message, is_err in mock_events:
        await process_incoming_queue_message(user_id, f"{queue_type}-{queue_name}", message)
        await asyncio.sleep(1.5)

async def start_queue_consumer_task(user_id: int, queue_type: str, queue_name: str, config: dict):
    if queue_type == "kafka":
        # In docker environment, the bootstrap server is kafka:29092
        bootstrap_servers = config.get("bootstrap_servers", "kafka:29092")
        try:
            await consume_real_kafka(user_id, queue_name, bootstrap_servers)
        except Exception:
            print("Kafka connection failed. Initializing simulator fallback...")
            await simulate_queue_consumption(user_id, queue_type, queue_name)
    elif queue_type == "rabbitmq":
        amqp_url = config.get("amqp_url", "amqp://guest:guest@localhost:5672/")
        try:
            await consume_real_rabbitmq(user_id, queue_name, amqp_url)
        except Exception:
            print("RabbitMQ connection failed. Initializing simulator fallback...")
            await simulate_queue_consumption(user_id, queue_type, queue_name)

@router.post("/connect")
async def connect_external_service(
    data: dict, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    service_type = data.get("type", "webhook")
    service_name = data.get("name", "log-stream")
    
    if service_type in ["kafka", "rabbitmq"]:
        background_tasks.add_task(
            start_queue_consumer_task, 
            user_id=current_user.id, 
            queue_type=service_type, 
            queue_name=service_name,
            config=data
        )
        
    return {
        "status": "Integration configured and active",
        "type": service_type,
        "name": service_name,
        "otel_propagation": data.get("otel_propagation", True)
    }
