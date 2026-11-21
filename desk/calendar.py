from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import os

ZONE = ZoneInfo("Asia/Kolkata")
DAY = timedelta(hours=9)
ZERO = timedelta()
REPLY = {"urgent":timedelta(hours=2), "medium":DAY/2, "low":DAY}
FIX = {"medium":3*DAY, "low":5*DAY}

def shift(day):
    return tuple(datetime.combine(day, t, ZONE) for t in (time(9,30), time(18,30)))

def next_period(moment):
    holidays = set(os.getenv("HOLIDAYS", "").split(","))
    moment = moment.astimezone(ZONE)
    day = moment.date()
    while True:
        start, end = shift(day)
        if day.weekday() < 5 and day.isoformat() not in holidays and moment < end:
            return max(start, moment), end
        day += timedelta(days=1)

def add_work(moment, duration):
    if duration <= ZERO:
        return moment
    while True:
        start, end = next_period(moment)
        available = end - start
        if duration <= available:
            return start + duration
        duration -= available
        moment = end

def worked(start, end):
    total = ZERO
    while start < end:
        start, limit = next_period(start)
        total += max(ZERO, min(end, limit) - start)
        start = limit
    return total

def deadlines(start, priority):
    reply = add_work(start, REPLY[priority])
    fix = next_period(start)[1] if priority == "urgent" else add_work(start, FIX[priority])
    return reply, fix
