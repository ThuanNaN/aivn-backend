import time
from fastapi import APIRouter
import asyncio

router = APIRouter()

@router.get("/sleep60ms")
async def make_sleep60ms():
    await asyncio.sleep(0.06)
    return {"message": "I slept for 60ms"}


@router.get("/busy60ms")
async def make_busy60ms():
    start_time = time.perf_counter()
    while (time.perf_counter() - start_time) < 0.06:
        pass
    return {"message": "I kept the CPU busy for 60ms"}
