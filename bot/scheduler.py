import datetime as dt
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.scheduler.start()

    def schedule_daily(self, time_str: str, func: Callable, *args, **kwargs):
        hour, minute = map(int, time_str.split(":"))
        self.scheduler.add_job(
            func,
            trigger="cron",
            hour=hour,
            minute=minute,
            args=args,
            kwargs=kwargs,
        )
