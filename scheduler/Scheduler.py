class Scheduler:
    def __init__(self, employees, schedule):
        self.employees = employees
        self.schedule = schedule

    def assign_month(self, dates, duty_type='WD'):
        for date in dates:
            available = [e for e in self.employees if e.is_available(date)]
            if not available:
                continue  # or handle conflict
            chosen = self.select_employee(available)
            self.schedule.assign(date, chosen, duty_type)

    def select_employee(self, candidates):
        # Simplest: pick the one with fewest assignments
        return min(candidates, key=lambda e: len(e.assignments))
