class Employee:
    def __init__(self, name):
        self.name = name
        self.assignments = {}  # e.g., {'2025-01-03': 'WD', ...}
        self.blocked_days = set()
        self.points = 0  # Or track separate duty types

    def add_assignment(self, date, duty_type):
        self.assignments[date] = duty_type

    def is_available(self, date):
        return date not in self.blocked_days and date not in self.assignments
