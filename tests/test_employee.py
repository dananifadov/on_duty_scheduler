#!/usr/bin/env python3
"""
Tests for Employee class
"""
import unittest
from datetime import date
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from employee import Employee

class TestEmployee(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.employee = Employee(
            name="Test Employee",
            email="test@example.com",
            country="Israel",
            observes_sabbath=False,
            position_percentage=100,
            blocked_days=["2025-09-15"],
            blocked_ranges=[{"start": "2025-09-20", "end": "2025-09-22"}]
        )
    
    def test_employee_creation(self):
        """Test basic employee creation"""
        self.assertEqual(self.employee.name, "Test Employee")
        self.assertEqual(self.employee.email, "test@example.com")
        self.assertEqual(self.employee.position_percentage, 100)
        self.assertFalse(self.employee.observes_sabbath)
    
    def test_from_dict(self):
        """Test creating employee from dictionary"""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "observes_sabbath": True,
            "blocked_days": ["2025-09-01"],
            "blocked_ranges": [{"start": "2025-09-10", "end": "2025-09-12"}]
        }
        
        emp = Employee.from_dict(data)
        self.assertEqual(emp.name, "John Doe")
        self.assertTrue(emp.observes_sabbath)
        self.assertEqual(emp._raw_blocked_days, ["2025-09-01"])
    
    def test_to_dict(self):
        """Test converting employee to dictionary"""
        data = self.employee.to_dict()
        
        self.assertEqual(data['name'], "Test Employee")
        self.assertEqual(data['email'], "test@example.com")
        self.assertIn('blocked_days', data)
        self.assertIn('blocked_ranges', data)
    
    def test_prepare_for_month(self):
        """Test month preparation with blocked days expansion"""
        self.employee.prepare_for_month(2025, 9)
        
        # Should include single blocked day
        self.assertIn("2025-09-15", self.employee.blocked_days)
        
        # Should include expanded range
        self.assertIn("2025-09-20", self.employee.blocked_days)
        self.assertIn("2025-09-21", self.employee.blocked_days)
        self.assertIn("2025-09-22", self.employee.blocked_days)
    
    def test_sabbath_blocking(self):
        """Test sabbath day blocking"""
        sabbath_emp = Employee(
            name="Sabbath Observer",
            email="sabbath@example.com",
            observes_sabbath=True
        )
        
        sabbath_emp.prepare_for_month(2025, 9)
        
        # September 2025: Fridays are 5, 12, 19, 26; Saturdays are 6, 13, 20, 27
        self.assertIn("2025-09-06", sabbath_emp.blocked_days)  # First Saturday
        self.assertIn("2025-09-13", sabbath_emp.blocked_days)  # Second Saturday
        self.assertIn("2025-09-05", sabbath_emp.blocked_days)  # First Friday
    
    def test_is_available(self):
        """Test availability checking"""
        self.employee.prepare_for_month(2025, 9)
        
        # Available day
        self.assertTrue(self.employee.is_available(date(2025, 9, 1)))
        
        # Blocked single day
        self.assertFalse(self.employee.is_available(date(2025, 9, 15)))
        
        # Blocked range day
        self.assertFalse(self.employee.is_available(date(2025, 9, 21)))
    
    def test_add_assignment(self):
        """Test adding assignments and point calculation"""
        self.employee.add_assignment("2025-09-01", "WD")
        self.employee.add_assignment("2025-09-02", "WE")
        
        self.assertEqual(self.employee.counts["WD"], 1)
        self.assertEqual(self.employee.counts["WE"], 1)
        self.assertEqual(self.employee.points, 3.0)  # WD=1.0 + WE=2.0
        
        self.assertIn("2025-09-01", self.employee.assignments)
        self.assertEqual(self.employee.assignments["2025-09-01"], "WD")
    
    def test_reset_runtime(self):
        """Test runtime reset"""
        self.employee.add_assignment("2025-09-01", "WD")
        self.employee.reset_runtime()
        
        self.assertEqual(self.employee.points, 0.0)
        self.assertEqual(self.employee.assignments, {})
        self.assertEqual(self.employee.counts["WD"], 0)
    
    def test_assignment_prevents_availability(self):
        """Test that assignments prevent availability on same day"""
        self.employee.prepare_for_month(2025, 9)
        self.employee.add_assignment("2025-09-01", "WD")
        
        # Should not be available on assigned day
        self.assertFalse(self.employee.is_available(date(2025, 9, 1)))


if __name__ == "__main__":
    unittest.main()

