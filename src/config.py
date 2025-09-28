DATA_DIR = "data"
EMPLOYEES_FILE = f"{DATA_DIR}/employees.json"
HOLIDAYS_FILE = f"{DATA_DIR}/holidays.json"
SCHEDULES_DIR = "schedules"

# duty weights (from your Excel logic)
WEIGHTS = {"WD": 1.0, "Th": 1.5, "WE": 2.0, "B": 0.5}

# fairness
DEFAULT_PERIOD = "month"  # or "quarter"