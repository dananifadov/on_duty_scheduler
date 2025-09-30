#!/usr/bin/env python3
"""
Tests for BlockedDaysManager
"""
import unittest
import tempfile
import json
from pathlib import Path
from datetime import date
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from blocked_days_manager import BlockedDaysManager

class TestBlockedDaysManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_employees_file = Path(self.temp_dir) / "test_employees.json"
        
        # Create test employees
        test_employees = [
            {
                "name": "Alice",
                "email": "alice@example.com",
                "blocked_days": ["2025-09-15"],
                "blocked_ranges": [{"start": "2025-09-20", "end": "2025-09-22"}],
                "observes_sabbath": False
            },
            {
                "name": "Bob",
                "email": "bob@example.com", 
                "blocked_days": [],
                "blocked_ranges": [],
                "observes_sabbath": True
            }
        ]
        
        with open(self.temp_employees_file, 'w') as f:
            json.dump(test_employees, f)
        
        self.manager = BlockedDaysManager(str(self.temp_employees_file))
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_list_employees(self):
        """Test listing employees"""
        employees = self.manager.list_employees()
        self.assertEqual(len(employees), 2)
        self.assertIn("Alice", employees)
        self.assertIn("Bob", employees)
    
    def test_get_employee_blocked_days(self):
        """Test getting employee blocked days"""
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        
        self.assertEqual(alice_blocked['blocked_days'], ["2025-09-15"])
        self.assertEqual(len(alice_blocked['blocked_ranges']), 1)
        self.assertFalse(alice_blocked['observes_sabbath'])
        
        bob_blocked = self.manager.get_employee_blocked_days("Bob")
        self.assertTrue(bob_blocked['observes_sabbath'])
    
    def test_add_blocked_day(self):
        """Test adding a blocked day"""
        success = self.manager.add_blocked_day("Alice", "2025-09-25")
        self.assertTrue(success)
        
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        self.assertIn("2025-09-25", alice_blocked['blocked_days'])
        
        # Test duplicate addition (should still return True but not duplicate)
        success2 = self.manager.add_blocked_day("Alice", "2025-09-25")
        self.assertTrue(success2)
        
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        self.assertEqual(alice_blocked['blocked_days'].count("2025-09-25"), 1)
    
    def test_remove_blocked_day(self):
        """Test removing a blocked day"""
        success = self.manager.remove_blocked_day("Alice", "2025-09-15")
        self.assertTrue(success)
        
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        self.assertNotIn("2025-09-15", alice_blocked['blocked_days'])
        
        # Test removing non-existent day
        success2 = self.manager.remove_blocked_day("Alice", "2025-09-99")
        self.assertFalse(success2)
    
    def test_add_blocked_range(self):
        """Test adding a blocked range"""
        success = self.manager.add_blocked_range("Bob", "2025-10-01", "2025-10-05")
        self.assertTrue(success)
        
        bob_blocked = self.manager.get_employee_blocked_days("Bob")
        self.assertEqual(len(bob_blocked['blocked_ranges']), 1)
        self.assertEqual(bob_blocked['blocked_ranges'][0]['start'], "2025-10-01")
        self.assertEqual(bob_blocked['blocked_ranges'][0]['end'], "2025-10-05")
    
    def test_remove_blocked_range(self):
        """Test removing a blocked range"""
        success = self.manager.remove_blocked_range("Alice", "2025-09-20", "2025-09-22")
        self.assertTrue(success)
        
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        self.assertEqual(len(alice_blocked['blocked_ranges']), 0)
    
    def test_get_blocked_calendar(self):
        """Test getting blocked calendar for a month"""
        # Test Alice's blocked calendar for September 2025
        blocked_calendar = self.manager.get_blocked_calendar("Alice", 2025, 9)
        
        # Should include single blocked day
        self.assertIn(15, blocked_calendar)
        
        # Should include range days
        self.assertIn(20, blocked_calendar)
        self.assertIn(21, blocked_calendar)
        self.assertIn(22, blocked_calendar)
        
        # Test Bob's sabbath blocking
        bob_calendar = self.manager.get_blocked_calendar("Bob", 2025, 9)
        
        # Should include Fridays and Saturdays
        friday_count = sum(1 for day, reason in bob_calendar.items() 
                          if "Sabbath" in reason and 
                          date(2025, 9, day).weekday() == 4)  # Friday
        self.assertGreater(friday_count, 0)
    
    def test_bulk_add_days(self):
        """Test bulk adding multiple days"""
        dates = ["2025-11-01", "2025-11-02", "2025-11-03"]
        results = self.manager.bulk_add_days("Alice", dates)
        
        self.assertTrue(all(results.values()))
        
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        for date_str in dates:
            self.assertIn(date_str, alice_blocked['blocked_days'])
    
    def test_clear_all_blocked_days(self):
        """Test clearing all blocked days"""
        success = self.manager.clear_all_blocked_days("Alice")
        self.assertTrue(success)
        
        alice_blocked = self.manager.get_employee_blocked_days("Alice")
        self.assertEqual(alice_blocked['blocked_days'], [])
        self.assertEqual(alice_blocked['blocked_ranges'], [])
    
    def test_invalid_date_handling(self):
        """Test handling of invalid dates"""
        success = self.manager.add_blocked_day("Alice", "invalid-date")
        self.assertFalse(success)
        
        success = self.manager.add_blocked_range("Alice", "invalid", "2025-09-25")
        self.assertFalse(success)
    
    def test_nonexistent_employee(self):
        """Test operations on non-existent employee"""
        success = self.manager.add_blocked_day("NonExistent", "2025-09-01")
        self.assertFalse(success)
        
        blocked_info = self.manager.get_employee_blocked_days("NonExistent")
        self.assertEqual(blocked_info['blocked_days'], [])
    
    def test_date_range_ordering(self):
        """Test that date ranges work regardless of order"""
        # Add range with end before start (should auto-correct)
        success = self.manager.add_blocked_range("Bob", "2025-12-31", "2025-12-01")
        self.assertTrue(success)
        
        bob_blocked = self.manager.get_employee_blocked_days("Bob")
        range_data = bob_blocked['blocked_ranges'][0]
        self.assertEqual(range_data['start'], "2025-12-01")
        self.assertEqual(range_data['end'], "2025-12-31")


if __name__ == "__main__":
    unittest.main()
