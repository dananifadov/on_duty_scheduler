"""Configuration settings for the on-duty scheduler."""

# Directory structure
DATA_DIR = "data"
EMPLOYEES_FILE = f"{DATA_DIR}/employees.json"
HOLIDAYS_FILE = f"{DATA_DIR}/holidays.json"
SCHEDULES_DIR = f"{DATA_DIR}/summaries/schedules"
SUMMARIES_DIR = f"{DATA_DIR}/summaries"

# Duty weights (aligned with business logic)
WEIGHTS = {
    "WD": 1.0,     # Weekday
    "Th": 1.5,     # Thursday (slightly higher load)
    "WE": 2.0,     # Weekend (higher load)
    "B": 0.5,      # Backup (lower commitment)
    "HO": 3.0      # Holiday 
}

# Algorithm parameters
BALANCE_TOLERANCE = 0.1  # Points difference to consider "equally good" candidates (very tight balance)
DEFAULT_PERIOD = "month"

# Company weekends (long weekends every 6 weeks)
COMPANY_WEEKENDS = [
    "2025-11-16"  # Company long weekend
]