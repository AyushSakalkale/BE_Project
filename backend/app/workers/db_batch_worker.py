import asyncio
from sqlalchemy import insert
from app.models.database import AsyncSessionLocal
from app.models.user_log import Log

class DBBatchWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self._task = None
        
    def start(self):
        self._task = asyncio.create_task(self._run())
        
    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
    async def enqueue(self, log_dict: dict):
        await self.queue.put(log_dict)
        
    async def _run(self):
        while True:
            try:
                # Wait for at least one item
                first_item = await self.queue.get()
                batch = [first_item]
                self.queue.task_done()
                
                # Try to batch more items up to 500 records or 100ms max wait time
                start_time = asyncio.get_event_loop().time()
                while len(batch) < 500:
                    time_left = 0.1 - (asyncio.get_event_loop().time() - start_time)
                    if time_left <= 0:
                        break
                    try:
                        item = await asyncio.wait_for(self.queue.get(), timeout=time_left)
                        batch.append(item)
                        self.queue.task_done()
                    except asyncio.TimeoutError:
                        break
                        
                # Bulk insert into PostgreSQL using core insert for maximum performance
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        await session.execute(insert(Log), batch)
                        
            except asyncio.CancelledError:
                # Flush remaining logs in queue on cancel/shutdown
                remaining = []
                while not self.queue.empty():
                    remaining.append(self.queue.get_nowait())
                    self.queue.task_done()
                if remaining:
                    try:
                        async with AsyncSessionLocal() as session:
                            async with session.begin():
                                await session.execute(insert(Log), remaining)
                    except Exception as e:
                        print(f"Failed to flush DBBatchWorker queue on shutdown: {e}")
                break
            except Exception as e:
                print(f"Error in DBBatchWorker: {e}")
                await asyncio.sleep(1.0)

db_batch_worker = DBBatchWorker()
