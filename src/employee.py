# on_duty_scheduler/src/employee.py
from datetime import date, timedelta
from .config import WEIGHTS

class Employee:
    def __init__(self, name, email, country='Israel',
                 observes_sabbath=False, position_percentage=100,
                 blocked_days=None, blocked_ranges=None):
        self.name = name
        self.email = email
        self.country = country
        self.observes_sabbath = bool(observes_sabbath)
        self.position_percentage = int(position_percentage)

        # raw inputs from JSON
        self._raw_blocked_days = set(blocked_days or [])
        self._raw_blocked_ranges = blocked_ranges or []  # list of {"start": "...", "end": "..."}

        # final, month-specific blocked set (populated by prepare_for_month)
        self.blocked_days = set()

        # runtime (for current build)
        self.assignments = {}               # {'YYYY-MM-DD': 'WD'/'Th'/'WE'/'B'}
        self.points = 0.0                   # weighted, live
        self.counts = {"WD": 0, "Th": 0, "WE": 0, "B": 0}
    
    # ---------- construction / persistence ----------
    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            name=d["name"],
            email=d["email"],
            country=d.get("country", "Israel"),
            observes_sabbath=d.get("observes_sabbath", False),
            position_percentage=d.get("position_percentage", 100),
            blocked_days=d.get("blocked_days", []),
            blocked_ranges=d.get("blocked_ranges", []),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "position_percentage": self.position_percentage,
            "country": self.country,
            "observes_sabbath": self.observes_sabbath,
            "blocked_days": sorted(self.blocked_days),
            "blocked_ranges": self.blocked_ranges,
        }

    # -------- runtime helpers --------
    def reset_runtime(self):
        self.assignments = {}
        self.points = 0.0
        self.counts = {"WD": 0, "Th": 0, "WE": 0, "B": 0}

    def is_available(self, d: date) -> bool:
        iso = d.isoformat()
        return (iso not in self.blocked_days) and (iso not in self.assignments)

    def add_assignment(self, date_str: str, duty_type: str):
        self.assignments[date_str] = duty_type
        self.counts[duty_type] += 1
        self.points += float(WEIGHTS.get(duty_type, 0.0))
