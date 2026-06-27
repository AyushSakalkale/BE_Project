from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from app.models.database import get_db
from app.models.user_log import User, Log, APIKey
from app.services.ml_service import ml_service
from app.services.huggingface_service import huggingface_service
from app.api.auth import get_current_user
from sqlalchemy import select

router = APIRouter()

async def get_user_by_api_key(api_key: str, db: AsyncSession):
    result = await db.execute(select(APIKey).where(APIKey.key == api_key))
    key_entry = result.scalars().first()
    if not key_entry:
        return None
    result = await db.execute(select(User).where(User.id == key_entry.user_id))
    return result.scalars().first()

class PasteLogsIn(BaseModel):
    logs: List[str]
    service: Optional[str] = "default"

class IngestLogIn(BaseModel):
    service: str
    timestamp: Optional[str] = None
    level: Optional[str] = "INFO"
    message: str

@router.post("/paste")
async def paste_logs(data: PasteLogsIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    results = []
    for msg in data.logs:
        score, is_anomaly, event_id = await ml_service.predict_combined(msg)
        
        # Proactively explain if it's an anomaly OR a clear error message
        should_explain = is_anomaly or any(w in msg.upper() for w in ["ERROR", "CRITICAL", "FATAL"])
        explanation = await huggingface_service.explain_log(msg) if should_explain else None
        
        log_entry = Log(
            user_id=current_user.id,
            service_name=data.service,
            message=msg,
            parsed_event=event_id,
            anomaly_score=score,
            is_anomaly=is_anomaly,
            simplified_message=explanation
        )
        db.add(log_entry)
        results.append({
            "message": msg,
            "score": score,
            "is_anomaly": is_anomaly,
            "explanation": explanation
        })
    
    await db.commit()
    return results

@router.post("/upload")
async def upload_log_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    lines = content.decode().splitlines()
    
    # Simple batch for performance
    for line in lines:
        if not line.strip(): continue
        score, is_anomaly, event_id = await ml_service.predict_combined(line)
        log_entry = Log(
            user_id=current_user.id,
            service_name="file-upload",
            message=line,
            parsed_event=event_id,
            anomaly_score=score,
            is_anomaly=is_anomaly
        )
        db.add(log_entry)
        
    await db.commit()
    return {"status": "success", "lines_processed": len(lines)}

@router.post("/ingest-log")
async def ingest_log(data: IngestLogIn, x_api_key: str = Header(..., alias="X-API-Key"), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_api_key(x_api_key, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    score, is_anomaly, event_id = await ml_service.predict_combined(data.message, timestamp=data.timestamp, level=data.level)
    
    # Proactively explain if it's an anomaly OR a clear error message
    should_explain = is_anomaly or any(w in data.message.upper() for w in ["ERROR", "CRITICAL", "FATAL"])
    explanation = await huggingface_service.explain_log(data.message) if should_explain else None
    
    log_entry = Log(
        user_id=user.id,
        service_name=data.service,
        message=data.message,
        parsed_event=event_id,
        anomaly_score=score,
        is_anomaly=is_anomaly,
        simplified_message=explanation
    )
    db.add(log_entry)
    await db.commit()
    
    return {
        "score": score,
        "is_anomaly": is_anomaly,
        "explanation": explanation
    }
