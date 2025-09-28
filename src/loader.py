import json
from .config import EMPLOYEES_FILE
from .employee import Employee

def load_employees():
    try:
        raw = json.loads(open(EMPLOYEES_FILE, "r", encoding="utf-8").read())
    except FileNotFoundError:
        return []
    return [Employee.from_dict(e) for e in raw]
