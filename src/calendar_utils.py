# on_duty_scheduler/src/calendar_utils.py
from datetime import date, timedelta

def iter_month(year: int, month: int):
    d0 = date(year, month, 1)
    d1 = date(year + (month==12), (1 if month==12 else month+1), 1)
    cur = d0
    while cur < d1:
        yield cur
        cur += timedelta(days=1)

def classify_duty(d: date) -> str:
    wd = d.weekday()  # Mon=0 ... Sun=6
    if wd == 3:
        return "Th"
    if wd in (4, 5):
        return "WE"
    return "WD"
