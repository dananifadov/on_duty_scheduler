# on_duty_scheduler/src/scheduler.py
import json
from typing import Dict
from pathlib import Path
from datetime import date
from src import loader
from src.calendar_utils import iter_month, classify_duty
from src.config import DATA_DIR, SUMMARIES_DIR, BALANCE_TOLERANCE, WEIGHTS, COMPANY_WEEKENDS

class Scheduler:
    def __init__(self):
        self.employees = loader.load_employees()
        # Load holiday manager for duty classification
        from src.holiday_manager import HolidayManager
        self.holiday_manager = HolidayManager()

    def _eligible(self, d):
        return [e for e in self.employees if e.is_available(d)]

    def _pick_lowest_points(self, candidates, duty_weight: float, exclude_names=frozenset()):
        pool = [e for e in candidates if e.name not in exclude_names]
        if not pool:
            return None

        min_points = min(e.points for e in pool)
        tol = BALANCE_TOLERANCE  # points-scale tolerance
        at_min = [e for e in pool if e.points <= min_points + tol]

        if len(at_min) > 1:
            return self._pick_best_for_balance(at_min, duty_weight)
        return at_min[0]
    
    def _pick_best_for_balance(self, candidates, duty_weight: float):
        best = None
        best_var = float("inf")
        for cand in candidates:
            # simulate points after this assignment (use duty_weight)
            tmp_points = []
            for e in self.employees:
                p = e.points + (duty_weight if e is cand else 0.0)
                tmp_points.append(p)
            mean = sum(tmp_points) / len(tmp_points)
            var = sum((p - mean) ** 2 for p in tmp_points) / len(tmp_points)
            if var < best_var:
                best_var = var
                best = cand
        return best or candidates[0]

    def assign_month(self, year: int, month: int, output_dir: str = None) -> Dict[str, Dict[str, str]]:
        """Return and also save: schedule_{YYYY}-{MM}.json in specified directory"""
        if not self.employees:
            return {}

        # NOTE: blocked_days must already be prepared for this month.

        # Phase 1: Initial greedy assignment
        out = self._initial_assignment(year, month)
        
        # Phase 2: Post-optimization to reduce spikes
        out = self._optimize_balance(out, year, month)

        # Save to specified directory or default
        if output_dir is None:
            output_dir = DATA_DIR
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        out_path = Path(output_dir) / f"schedule_{year}-{month:02d}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    def _initial_assignment(self, year: int, month: int) -> Dict[str, Dict[str, str]]:
        """Phase 1: Create initial schedule using greedy algorithm"""
        out: Dict[str, Dict[str, str]] = {}
        
        for d in iter_month(year, month):
            iso = d.isoformat()
            duty = classify_duty(d, self.holiday_manager)
            cands = self._eligible(d)
            day_rec: Dict[str, str] = {}

            # primary
            duty_weight = WEIGHTS.get(duty, 1.0)
            p = self._pick_lowest_points(cands, duty_weight)
            if p:
                p.add_assignment(iso, duty)
                day_rec[duty] = p.name
            else:
                out[iso] = day_rec
                continue

            # weekend backup
            if duty == "WE":
                backup_weight = WEIGHTS.get("B", 0.5)
                b = self._pick_lowest_points(cands, backup_weight, exclude_names={p.name})
                if b:
                    b.add_assignment(iso, "B")
                    day_rec["B"] = b.name

            out[iso] = day_rec
        
        return out

    def _optimize_balance(
        self,
        schedule: Dict[str, Dict[str, str]],
        year: int,
        month: int,
        max_iterations: int = 50,  # Much more aggressive balancing
    ) -> Dict[str, Dict[str, str]]:
        """
        Phase 2 (compact): rebalance by points (WD=1, Th=1.5, WE=2, B=0.5).
        - Works within the given month only (month-local points).
        - Considers moving a single duty from an 'over' to an 'under' employee.
        - Only executes a swap if it strictly reduces squared error (SSE) vs month mean.
        - Respects availability & same-day double-booking.
        """
        from src.config import WEIGHTS, BALANCE_TOLERANCE
        from datetime import date

        # ----- tiny helpers ------------------------------------------------------
        start_pts = {e.name: e.points for e in self.employees}
        emp_by = {e.name: e for e in self.employees}
        blocked = {e.name: set(e.blocked_days) for e in self.employees}
        days = sorted(schedule.keys())

        def month_points() -> dict[str, float]:
            # points added in THIS month (since start_pts snapshot)
            return {e.name: e.points - start_pts[e.name] for e in self.employees}

        def mean(vals) -> float:
            return (sum(vals) / len(vals)) if vals else 0.0

        def sse(points: dict[str, float]) -> float:
            m = mean(points.values())
            return sum((p - m) ** 2 for p in points.values())

        def feasible(day: str, duty: str, to_name: str) -> bool:
            # not blocked that day
            if day in blocked[to_name]:
                return False
            # not already assigned to *any* duty that day
            if to_name in schedule[day].values():
                return False
            # also not already assigned in runtime (covers future rules)
            if day in emp_by[to_name].assignments:
                return False
            return True

        # precompute, for each 'over' employee, their (day, duty, weight) holdings this month
        def holdings(name: str) -> list[tuple[str, str, float]]:
            items: list[tuple[str, str, float]] = []
            for d in days:
                for duty, who in schedule[d].items():
                    if who == name:
                        items.append((d, duty, WEIGHTS.get(duty, 0.0)))
            # try heavier duties first to reduce spikes faster
            items.sort(key=lambda x: -x[2])
            return items

        # ----- main loop ---------------------------------------------------------
        for _ in range(max_iterations):
            pts = month_points()
            if not pts:
                break

            avg = mean(pts.values())
            over = [n for n, p in pts.items() if p > avg + BALANCE_TOLERANCE]
            under = [n for n, p in pts.items() if p < avg - BALANCE_TOLERANCE]
            
            # If no one is significantly over/under by tolerance, use a smaller threshold
            if not over or not under:
                smaller_tolerance = BALANCE_TOLERANCE / 3
                over = [n for n, p in pts.items() if p > avg + smaller_tolerance]
                under = [n for n, p in pts.items() if p < avg - smaller_tolerance]
                if not over or not under:
                    break

            # Try one improving swap (greedy best-first). If found, do it and iterate again.
            improved = False

            # Examine most-overloaded first; most-underloaded first.
            over.sort(key=lambda n: pts[n], reverse=True)
            under.sort(key=lambda n: pts[n])

            base_sse = sse(pts)

            for o in over:
                o_holdings = holdings(o)
                if not o_holdings:
                    continue

                best = None  # (delta_sse, day, duty, to_name)
                for d, duty, w in o_holdings:
                    # consider all 'under' targets that are feasible on that day
                    feasibles = [u for u in under if feasible(d, duty, u)]
                    if not feasibles:
                        continue

                    for u in feasibles:
                        # simulate: move weight w from o -> u (month-local points)
                        sim = pts.copy()
                        sim[o] -= w
                        sim[u] += w
                        delta = sse(sim) - base_sse
                        if best is None or delta < best[0]:
                            best = (delta, d, duty, u)

                # apply the single best improving swap for this 'o'
                if best and best[0] < 0.0:
                    _, day, duty, u = best
                    self._perform_swap(
                        schedule,
                        date_str=day,
                        duty_type=duty,
                        from_emp=emp_by[o],
                        to_emp=emp_by[u],
                    )
                    improved = True
                    break  # re-evaluate from new state

            if not improved:
                break

        return schedule

    
    def _get_available_employees_for_month(self, year: int, month: int):
        """Get employees who are available for at least some days in the month"""
        available_employees = []
        for emp in self.employees:
            # Check if employee has any availability in the month
            has_availability = False
            for d in iter_month(year, month):
                iso = d.isoformat()
                if iso not in emp.blocked_days:
                    has_availability = True
                    break
            if has_availability:
                available_employees.append(emp)
        return available_employees

    def _try_swap_assignment(self, schedule: Dict[str, Dict[str, str]], from_emp: str, to_emp: str, year: int, month: int) -> bool:
        """Try to swap one assignment from overloaded employee to underloaded employee"""
        
        # Get employee objects
        to_emp_obj = next((e for e in self.employees if e.name == to_emp), None)
        from_emp_obj = next((e for e in self.employees if e.name == from_emp), None)
        
        if not to_emp_obj or not from_emp_obj:
            return False
        
        # Try to find the best assignment to swap (prioritize lower-weight duties first)
        swap_candidates = []
        
        for date_str, day_assignments in schedule.items():
            for duty_type, assigned_name in day_assignments.items():
                if assigned_name == from_emp:
                    date_obj = date.fromisoformat(date_str)
                    iso = date_obj.isoformat()
                    
                    # Check if to_emp was originally available for this date
                    was_available = (iso not in to_emp_obj.blocked_days)
                    
                    if was_available and not self._would_create_conflict(schedule, date_str, duty_type, to_emp):
                        from src.config import WEIGHTS
                        weight = WEIGHTS.get(duty_type, 0.0)
                        swap_candidates.append((date_str, duty_type, weight))
        
        # prefer swapping heavier first during balance step
        swap_candidates.sort(key=lambda x: -x[2])  # weight desc
        
        # Try the best candidate
        for date_str, duty_type, weight in swap_candidates:
            self._perform_swap(schedule, date_str, duty_type, from_emp_obj, to_emp_obj)
            return True
        
        return False

    def _would_create_conflict(self, schedule: Dict[str, Dict[str, str]], date_str: str, duty_type: str, new_assignee: str) -> bool:
        """Check if assigning new_assignee to this duty would create a conflict"""
        day_assignments = schedule[date_str]
        
        # Can't have same person assigned to multiple duties on same day
        for existing_duty, existing_assignee in day_assignments.items():
            if existing_duty != duty_type and existing_assignee == new_assignee:
                return True
        
        return False

    def _perform_swap(self, schedule: Dict[str, Dict[str, str]], date_str: str, duty_type: str, from_emp, to_emp):
        """Perform the actual assignment swap and update employee states"""
        from src.config import WEIGHTS
        
        # Update schedule
        schedule[date_str][duty_type] = to_emp.name
        
        # Update from_emp (remove assignment)
        if date_str in from_emp.assignments:
            old_duty = from_emp.assignments[date_str]
            del from_emp.assignments[date_str]
            from_emp.counts[old_duty] -= 1
            from_emp.points -= WEIGHTS.get(old_duty, 0.0)
        
        # Update to_emp (add assignment)
        to_emp.assignments[date_str] = duty_type
        to_emp.counts[duty_type] += 1
        to_emp.points += WEIGHTS.get(duty_type, 0.0)

    def assign_months(self, year: int, months: list[int]) -> dict[str, dict[str, dict[str, str]]]:
        """
        Assign multiple months and return a mapping:
        { 'YYYY-MM': { 'YYYY-MM-DD': {'WD'|'Th'|'WE': 'Name', 'B': 'Name'?}, ... }, ... }
        Also writes each month to organized period folder.
        Implements availability-aware distribution across the entire period.
        """
        # Create period-specific folder
        month_range = f"{min(months):02d}-{max(months):02d}" if len(months) > 1 else f"{months[0]:02d}"
        period_folder = Path(SUMMARIES_DIR) / f"{year}_{month_range}"
        
        # Reset runtime ONCE for the whole period
        for e in self.employees:
            e.reset_runtime()

        # Calculate availability weights for each employee across the entire period
        availability_weights = self._calculate_availability_weights(year, months)
        
        # Apply availability-aware initial weighting
        self._apply_availability_weighting(availability_weights)

        result = {}
        for m in months:
            # prepare per-employee blocked set for this month
            for e in self.employees:
                e.prepare_for_month(year, m)
            # build the month (keeps accumulating points/counts)
            result[f"{year}-{m:02d}"] = self.assign_month(year, m, str(period_folder))
        return result

    def _calculate_availability_weights(self, year: int, months: list[int]) -> dict[str, float]:
        """Calculate availability percentage for each employee across the period"""
        weights = {}
        
        for emp in self.employees:
            total_days = 0
            available_days = 0
            
            for month in months:
                emp.prepare_for_month(year, month)  # Set up blocked days for this month
                
                for d in iter_month(year, month):
                    total_days += 1
                    if d.isoformat() not in emp.blocked_days:
                        available_days += 1
            
            # Calculate availability percentage (0.0 to 1.0)
            availability_pct = available_days / total_days if total_days > 0 else 0.0
            weights[emp.name] = availability_pct
            
        return weights

    def _apply_availability_weighting(self, availability_weights: dict[str, float]):
        """Adjust employee points based on their availability to compensate for blocked periods"""
        if not availability_weights:
            return
            
        # Find the average availability
        avg_availability = sum(availability_weights.values()) / len(availability_weights)
        
        # Adjust points inversely to availability: 
        # Less available employees start with lower points (get priority)
        for emp in self.employees:
            availability = availability_weights.get(emp.name, avg_availability)
            
            # If someone is much less available, give them a head start
            if availability < avg_availability * 0.8:  # Less than 80% of average
                compensation = (avg_availability - availability) * 10  # Scale factor
                emp.points -= compensation  # Lower points = higher priority
                print(f"Compensating {emp.name}: {availability:.1%} available, -{compensation:.1f} point adjustment")

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
                "HO": e.counts["HO"],
                "Total": round(total, 3),
                "factor": f"{factor:.2f}",
                "Total_per_month": round(total_pm, 3),
                "Avg": round(avg_per_month, 3),
                "Balance": round(total_pm - avg_per_month, 3),
            })

        rows.append({
            "Employee": "TOTAL",
            "WD": sum(e.counts["WD"] for e in emps),
            "Th": sum(e.counts["Th"] for e in emps),
            "WE": sum(e.counts["WE"] for e in emps),
            "B": sum(e.counts["B"] for e in emps),
            "HO": sum(e.counts["HO"] for e in emps),
            "Total": round(total_sum, 3),
            "factor": f"{factor:.2f}",
            "Total_per_month": round(total_sum / factor if factor else total_sum, 9),
            "Avg": round(avg_per_month, 3),
            "Balance": ""
        })
        return rows
    
    def save_summary(self, summary, year: int, months: list[int], output_dir: str = None):
        """Save summary to a CSV file in organized folder structure."""
        if output_dir is None:
            # Use same period folder as schedules
            month_range = f"{min(months):02d}-{max(months):02d}" if len(months) > 1 else f"{months[0]:02d}"
            output_dir = Path(SUMMARIES_DIR) / f"{year}_{month_range}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create filename based on period
        month_range = f"{min(months):02d}-{max(months):02d}" if len(months) > 1 else f"{months[0]:02d}"
        filename = f"summary_{year}_{month_range}.csv"
        filepath = Path(output_dir) / filename
        
        # Convert to CSV format
        if not summary:
            return filepath
            
        headers = list(summary[0].keys())
        csv_content = ",".join(headers) + "\n"
        
        for row in summary:
            csv_content += ",".join(str(row[h]) for h in headers) + "\n"
        
        filepath.write_text(csv_content, encoding="utf-8")
        return filepath
