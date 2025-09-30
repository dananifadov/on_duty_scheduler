# on_duty_scheduler/src/calendar_utils.py
from datetime import date, timedelta
from src.config import COMPANY_WEEKENDS

def iter_month(year: int, month: int):
    d0 = date(year, month, 1)
    d1 = date(year + (month==12), (1 if month==12 else month+1), 1)
    cur = d0
    while cur < d1:
        yield cur
        cur += timedelta(days=1)

def classify_duty(d: date, holiday_manager=None) -> str:
    """
    Classify duty type for a given date.
    Priority: Holiday > Company Weekend > Thursday > Weekend > Weekday
    """
    date_str = d.isoformat()
    
    # Check if it's a holiday first (highest priority)
    if holiday_manager and holiday_manager.is_holiday(date_str):
        return "HO"
    
    # Check if it's a company weekend
    if date_str in COMPANY_WEEKENDS:
        return "WE"
    
    wd = d.weekday()  # Mon=0 ... Sun=6
    if wd == 3:
        return "Th"
    if wd in (4, 5):
        return "WE"
    return "WD"
