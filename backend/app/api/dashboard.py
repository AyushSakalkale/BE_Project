from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.database import get_db
from app.models.user_log import User, Log
from app.api.logs import get_current_user
from typing import List

router = APIRouter()

@router.get("/summary")
async def get_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Total logs
    total_result = await db.execute(select(func.count(Log.id)).where(Log.user_id == current_user.id))
    total_logs = total_result.scalar()
    
    # Anomaly count
    anomaly_result = await db.execute(select(func.count(Log.id)).where(Log.user_id == current_user.id, Log.is_anomaly == True))
    anomaly_count = anomaly_result.scalar()
    
    anomaly_percent = (anomaly_count / total_logs * 100) if total_logs > 0 else 0
    
    return {
        "total_logs": total_logs,
        "anomaly_count": anomaly_count,
        "anomaly_percentage": round(anomaly_percent, 2)
    }

@router.get("/recent")
async def get_recent(limit: int = 10, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Log).where(Log.user_id == current_user.id).order_by(Log.timestamp.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return logs

@router.get("/trends")
async def get_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Group by date/hour for trends
    # Simplified for now: just daily anomaly counts
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    result = await db.execute(
        select(func.date(Log.timestamp), func.count(Log.id))
        .where(Log.user_id == current_user.id, Log.is_anomaly == True, Log.timestamp >= seven_days_ago)
        .group_by(func.date(Log.timestamp))
        .order_by(func.date(Log.timestamp))
    )
    trends = [{"date": str(row[0]), "count": row[1]} for row in result]
    return trends
