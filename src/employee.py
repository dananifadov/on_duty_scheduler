# on_duty_scheduler/src/employee.py
from datetime import date, timedelta
from src.config import WEIGHTS  # absolute import; run with: python -m src.main

class Employee:
    """
    Single blocked_days set per month:
      - explicit single blocked days
      - expanded blocked ranges
      - shabbat days (Fri/Sat) for the target month if observes_sabbath=True
    """
    def __init__(self, name, email, country='Israel',
                 observes_sabbath=False, position_percentage=100,
                 blocked_days=None, blocked_ranges=None):
        self.name = name
        self.email = email
        self.country = country
        self.observes_sabbath = bool(observes_sabbath)
        self.position_percentage = int(position_percentage)

        # raw inputs from JSON
        self._raw_blocked_days = blocked_days or []
        self._raw_blocked_ranges = blocked_ranges or []  # list of {"start": "...", "end": "..."}

        # final, month-specific blocked set (built by prepare_for_month)
        self.blocked_days = set()

        # runtime (for current build)
        self.assignments = {}               # {'YYYY-MM-DD': 'WD'/'Th'/'WE'/'B'}
        self.points = 0.0                   # weighted, live
        self.counts = {"WD": 0, "Th": 0, "WE": 0, "B": 0}

    @classmethod
    def from_dict(cls, d: dict):
        # accept both observes_sabbath and observes_shabat (alias)
        observes = d.get("observes_sabbath")
        if observes is None:
            observes = d.get("observes_shabat", False)
        return cls(
            name=d["name"],
            email=d["email"],
            country=d.get("country", "Israel"),
            observes_sabbath=observes,
            position_percentage=d.get("position_percentage", 100),
            blocked_days=d.get("blocked_days", []),
            blocked_ranges=d.get("blocked_ranges", []),
        )

    def to_dict(self) -> dict:
        # persists only the raw inputs (blocked_days/ranges), not runtime
        return {
            "name": self.name,
            "email": self.email,
            "position_percentage": self.position_percentage,
            "country": self.country,
            "observes_sabbath": self.observes_sabbath,
            "blocked_days": sorted(self._raw_blocked_days),
            "blocked_ranges": self._raw_blocked_ranges,
        }

    # -------- month prep: build the single blocked set --------
    def prepare_for_month(self, year: int, month: int):
        """Build the final blocked_days set for this specific month (one set, done)."""
        # start with explicit singles
        self.blocked_days = set(self._raw_blocked_days)

        # expand ranges (inclusive)
        for rng in self._raw_blocked_ranges:
            try:
                start = date.fromisoformat(rng["start"])
                end = date.fromisoformat(rng["end"])
            except Exception:
                continue
            if end < start:
                start, end = end, start
            cur = start
            while cur <= end:
                self.blocked_days.add(cur.isoformat())
                cur += timedelta(days=1)

        # translate observes_sabbath into blocked Fri/Sat for the target month
        if self.observes_sabbath:
            cur = date(year, month, 1)
            nxt = date(year + (month == 12), (1 if month == 12 else month + 1), 1)
            while cur < nxt:
                if cur.weekday() in (4, 5):  # Fri, Sat
                    self.blocked_days.add(cur.isoformat())
                cur += timedelta(days=1)

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
