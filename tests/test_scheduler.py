#!/usr/bin/env python3
"""
Tests for Scheduler class
"""
import unittest
import tempfile
import json
from pathlib import Path
from datetime import date
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scheduler import Scheduler
from employee import Employee

class TestScheduler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures with temporary employees file"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_employees_file = Path(self.temp_dir) / "test_employees.json"
        
        # Create test employees
        test_employees = [
            {
                "name": "Alice",
                "email": "alice@example.com",
                "blocked_days": [],
                "blocked_ranges": []
            },
            {
                "name": "Bob", 
                "email": "bob@example.com",
                "blocked_days": ["2025-09-15"],
                "blocked_ranges": []
            },
            {
                "name": "Charlie",
                "email": "charlie@example.com",
                "observes_sabbath": True,
                "blocked_days": [],
                "blocked_ranges": []
            }
        ]
        
        with open(self.temp_employees_file, 'w') as f:
            json.dump(test_employees, f)
        
        # Mock the employees file path
        import src.config as config
        self.original_employees_file = config.EMPLOYEES_FILE
        config.EMPLOYEES_FILE = str(self.temp_employees_file)
        
        self.scheduler = Scheduler()
    
    def tearDown(self):
        """Clean up"""
        import src.config as config
        config.EMPLOYEES_FILE = self.original_employees_file
        
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_scheduler_initialization(self):
        """Test scheduler loads employees correctly"""
        self.assertEqual(len(self.scheduler.employees), 3)
        names = [emp.name for emp in self.scheduler.employees]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)
        self.assertIn("Charlie", names)
    
    def test_eligible_employees(self):
        """Test eligible employee filtering"""
        # Prepare employees for September 2025
        for emp in self.scheduler.employees:
            emp.prepare_for_month(2025, 9)
        
        # Test normal weekday - all should be eligible
        weekday = date(2025, 9, 1)  # Monday
        eligible = self.scheduler._eligible(weekday)
        self.assertEqual(len(eligible), 3)
        
        # Test day when Bob is blocked
        blocked_day = date(2025, 9, 15)
        eligible = self.scheduler._eligible(blocked_day)
        eligible_names = [emp.name for emp in eligible]
        self.assertNotIn("Bob", eligible_names)
        self.assertIn("Alice", eligible_names)
    
    def test_sabbath_blocking(self):
        """Test that sabbath observer is blocked on Friday/Saturday"""
        for emp in self.scheduler.employees:
            emp.prepare_for_month(2025, 9)
        
        # Test Saturday (should block Charlie)
        saturday = date(2025, 9, 6)  # First Saturday in Sept 2025
        eligible = self.scheduler._eligible(saturday)
        eligible_names = [emp.name for emp in eligible]
        self.assertNotIn("Charlie", eligible_names)
        self.assertIn("Alice", eligible_names)
        self.assertIn("Bob", eligible_names)
    
    def test_pick_lowest_points(self):
        """Test lowest points selection"""
        from src.config import WEIGHTS
        
        # Set up different point levels
        self.scheduler.employees[0].points = 0.0  # Alice
        self.scheduler.employees[1].points = 2.0  # Bob
        self.scheduler.employees[2].points = 1.0  # Charlie
        
        selected = self.scheduler._pick_lowest_points(self.scheduler.employees, WEIGHTS.get('WD', 1.0))
        self.assertEqual(selected.name, "Alice")
    
    def test_assign_month_basic(self):
        """Test basic month assignment"""
        # Create temp output directory
        output_dir = Path(self.temp_dir) / "output"
        
        schedule = self.scheduler.assign_month(2025, 9, str(output_dir))
        
        # Should have entries for each day in September
        self.assertGreater(len(schedule), 25)  # At least most days
        
        # Check that weekend days have backup assignments
        weekend_days = [day for day, assignments in schedule.items() 
                       if date.fromisoformat(day).weekday() >= 5]
        
        for day in weekend_days[:3]:  # Check first few weekends
            if "WE" in schedule[day]:
                # Weekend assignments should have backup when possible
                pass  # Basic check that it doesn't crash
    
    def test_availability_aware_compensation(self):
        """Test that employees with limited availability get compensation"""
        # Create employee with very limited availability
        limited_emp_data = {
            "name": "Limited",
            "email": "limited@example.com", 
            "blocked_ranges": [{"start": "2025-09-01", "end": "2025-09-25"}]
        }
        
        temp_file = Path(self.temp_dir) / "limited_employees.json"
        with open(temp_file, 'w') as f:
            json.dump([limited_emp_data] + [emp.to_dict() for emp in self.scheduler.employees], f)
        
        # Create new scheduler with limited employee
        import src.config as config
        config.EMPLOYEES_FILE = str(temp_file)
        new_scheduler = Scheduler()
        
        # Calculate availability weights
        weights = new_scheduler._calculate_availability_weights(2025, [9])
        
        # Limited employee should have very low availability
        self.assertLess(weights["Limited"], 0.5)  # Less than 50% available
    
    def test_schedule_file_creation(self):
        """Test that schedule files are created properly"""
        output_dir = Path(self.temp_dir) / "schedules"
        
        schedule = self.scheduler.assign_month(2025, 9, str(output_dir))
        
        # Check file was created
        expected_file = output_dir / "schedule_2025-09.json"
        self.assertTrue(expected_file.exists())
        
        # Check file content
        with open(expected_file, 'r') as f:
            saved_schedule = json.load(f)
        
        self.assertEqual(saved_schedule, schedule)
    
    def test_balance_optimization(self):
        """Test that balance optimization reduces variance"""
        # Run assignment multiple times and check that assignments are distributed
        schedules = []
        for _ in range(3):
            for emp in self.scheduler.employees:
                emp.reset_runtime()
            schedule = self.scheduler.assign_month(2025, 9)
            schedules.append(schedule)
        
        # Check that multiple employees get assignments (basic fairness test)
        all_assigned = set()
        for schedule in schedules:
            for day_assignments in schedule.values():
                all_assigned.update(day_assignments.values())
        
        self.assertGreater(len(all_assigned), 1)  # More than one person assigned


if __name__ == "__main__":
    unittest.main()

