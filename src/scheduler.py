# on_duty_scheduler/src/scheduler.py
import json
from typing import Dict
from pathlib import Path
from src import loader
from src.calendar_utils import iter_month, classify_duty
from src.config import DATA_DIR

class Scheduler:
    def __init__(self):
        self.employees = loader.load_employees()

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

        # NOTE: blocked_days must already be prepared for this month.

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

        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        out_path = Path(DATA_DIR) / f"schedule_{year}-{month:02d}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    def assign_months(self, year: int, months: list[int]) -> dict[str, dict[str, dict[str, str]]]:
        """
        Assign multiple months and return a mapping:
        { 'YYYY-MM': { 'YYYY-MM-DD': {'WD'|'Th'|'WE': 'Name', 'B': 'Name'?}, ... }, ... }
        Also writes each month to data/schedule_YYYY-MM.json.
        """
        # Reset runtime ONCE for the whole period
        for e in self.employees:
            e.reset_runtime()

        result = {}
        for m in months:
            # prepare per-employee blocked set for this month
            for e in self.employees:
                e.prepare_for_month(year, m)
            # build the month (keeps accumulating points/counts)
            result[f"{year}-{m:02d}"] = self.assign_month(year, m)
        return result

    def summarize_period(self, months_count: int):
        """Quarter-style summary (Totals over period; per-month averages)."""
        emps = self.employees
        n = len(emps)
        if n == 0:
            return []

        total_sum = sum(e.points for e in emps)  # over the whole period
        factor = float(months_count)
        avg_per_month = total_sum / (n * factor) if n and factor else 0.0

        rows = []
        for e in emps:
            total = e.points
            total_pm = total / factor if factor else total
            rows.append({
                "Employee": e.name,
                "WD": e.counts["WD"],
                "Th": e.counts["Th"],
                "WE": e.counts["WE"],
                "B": e.counts["B"],
                "HO": 0,
                "Total": round(total, 3),
                "factor": f"{factor:.2f}",
                "Total_per_month": round(total_pm, 9),
                "Avg": round(avg_per_month, 3),
                "Balance": round(total_pm - avg_per_month, 3),
            })

        rows.append({
            "Employee": "TOTAL",
            "WD": sum(e.counts["WD"] for e in emps),
            "Th": sum(e.counts["Th"] for e in emps),
            "WE": sum(e.counts["WE"] for e in emps),
            "B": sum(e.counts["B"] for e in emps),
            "HO": 0,
            "Total": round(total_sum, 3),
            "factor": f"{factor:.2f}",
            "Total_per_month": round(total_sum / factor if factor else total_sum, 9),
            "Avg": round(avg_per_month, 3),
            "Balance": ""
        })
        return rows
