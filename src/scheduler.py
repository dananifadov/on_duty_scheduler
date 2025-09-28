# on_duty_scheduler/src/scheduler.py
import json
from typing import Dict
from . import loader
from .calendar_utils import iter_month, classify_duty
from .config import DATA_DIR

class Scheduler:
    def __init__(self):
        self.employees = loader.load_employees()

    def _prepare_month(self, year: int, month: int):
        for e in self.employees:
            e.reset_runtime()
            e.prepare_for_month(year, month)

    def _eligible(self, d):
        return [e for e in self.employees if e.is_available(d)]

    def _pick_lowest_points(self, candidates, exclude_names=frozenset()):
        pool = [e for e in candidates if e.name not in exclude_names]
        if not pool:
            return None
        return min(pool, key=lambda x: (x.points, x.name))

    def assign_month(self, year: int, month: int) -> Dict[str, Dict[str, str]]:
        """Return and also save: data/schedule_{YYYY}-{MM}.json"""
        if not self.employees:
            return {}

        self._prepare_month(year, month)
        out: Dict[str, Dict[str, str]] = {}

        for d in iter_month(year, month):
            iso = d.isoformat()
            duty = classify_duty(d)
            cands = self._eligible(d)
            day_rec: Dict[str, str] = {}

            # primary
            p = self._pick_lowest_points(cands)
            if p:
                p.add_assignment(iso, duty)
                day_rec[duty] = p.name
            else:
                out[iso] = day_rec
                continue

            # weekend backup
            if duty == "WE":
                b = self._pick_lowest_points(cands, exclude_names={p.name})
                if b:
                    b.add_assignment(iso, "B")
                    day_rec["B"] = b.name

            out[iso] = day_rec

        # write JSON to on_duty_scheduler/data/
        DATA_DIR_PATH = DATA_DIR  # string from config; ensure directory exists at runtime
        from pathlib import Path
        Path(DATA_DIR_PATH).mkdir(parents=True, exist_ok=True)
        out_path = Path(DATA_DIR_PATH) / f"schedule_{year}-{month:02d}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

        return out
