#!/usr/bin/env python3
"""
Tests for Excel writer functionality
"""
import unittest
import tempfile
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from excel_writer import ExcelWriter

class TestExcelWriter(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.writer = ExcelWriter(self.temp_dir)
        
        # Sample schedule data
        self.sample_schedule = {
            "2025-09": {
                "2025-09-01": {"WD": "Alice"},
                "2025-09-02": {"WD": "Bob"},
                "2025-09-06": {"WE": "Charlie", "B": "Alice"},
                "2025-09-07": {"WE": "Bob", "B": "Charlie"}
            }
        }
        
        # Sample summary data
        self.sample_summary = [
            {
                "Employee": "Alice",
                "WD": 1,
                "Th": 0,
                "WE": 0,
                "B": 1,
                "Total": 1.5,
                "Balance": 0.1
            },
            {
                "Employee": "Bob", 
                "WD": 1,
                "Th": 0,
                "WE": 1,
                "B": 0,
                "Total": 3.0,
                "Balance": -0.1
            }
        ]
        
        # Sample employee data
        self.sample_employees = [
            {
                "name": "Alice",
                "email": "alice@example.com",
                "blocked_days": ["2025-09-15"],
                "blocked_ranges": [],
                "observes_sabbath": False
            },
            {
                "name": "Bob",
                "email": "bob@example.com",
                "blocked_days": [],
                "blocked_ranges": [{"start": "2025-09-20", "end": "2025-09-22"}],
                "observes_sabbath": False
            }
        ]
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_excel_writer_initialization(self):
        """Test ExcelWriter initializes correctly"""
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertIsInstance(self.writer.colors, dict)
        self.assertIn('WD', self.writer.colors)
        self.assertIn('blocked', self.writer.colors)
    
    def test_color_definitions(self):
        """Test that all required colors are defined"""
        required_colors = ['WD', 'Th', 'WE', 'B', 'HO', 'blocked', 'header']
        day_colors = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for color in required_colors + day_colors:
            self.assertIn(color, self.writer.colors)
    
    def test_write_schedule_workbook(self):
        """Test creating Excel workbook"""
        filepath = self.writer.write_schedule_workbook(
            year=2025,
            months=[9],
            schedules=self.sample_schedule,
            summary=self.sample_summary,
            employees_data=self.sample_employees
        )
        
        self.assertTrue(filepath.exists())
        self.assertTrue(str(filepath).endswith('.xlsx'))
        
        # Check file size is reasonable (not empty)
        self.assertGreater(filepath.stat().st_size, 1000)
    
    def test_blocked_days_detection(self):
        """Test blocked days detection for employees"""
        blocked_days = self.writer._get_blocked_days(2025, 9, self.sample_employees)
        
        # Should detect Alice's single blocked day
        self.assertIn("2025-09-15", blocked_days)
        self.assertIn("Alice", blocked_days["2025-09-15"])
        
        # Should detect Bob's blocked range
        self.assertIn("2025-09-20", blocked_days)
        self.assertIn("2025-09-21", blocked_days)
        self.assertIn("2025-09-22", blocked_days)
        for day in ["2025-09-20", "2025-09-21", "2025-09-22"]:
            self.assertIn("Bob", blocked_days[day])
    
    def test_sabbath_blocking_detection(self):
        """Test sabbath day blocking detection"""
        sabbath_employee = {
            "name": "Sabbath Observer",
            "email": "sabbath@example.com",
            "blocked_days": [],
            "blocked_ranges": [],
            "observes_sabbath": True
        }
        
        blocked_days = self.writer._get_blocked_days(2025, 9, [sabbath_employee])
        
        # Should block Fridays and Saturdays
        friday_blocks = [day for day, employees in blocked_days.items() 
                        if "Sabbath Observer" in employees and 
                        day.endswith("-06") or day.endswith("-13")]  # Some Fridays/Saturdays
        
        self.assertGreater(len(friday_blocks), 0)
    
    def test_multi_month_workbook(self):
        """Test creating workbook with multiple months"""
        multi_schedule = {
            "2025-09": {"2025-09-01": {"WD": "Alice"}},
            "2025-10": {"2025-10-01": {"WD": "Bob"}},
            "2025-11": {"2025-11-01": {"WD": "Charlie"}}
        }
        
        filepath = self.writer.write_schedule_workbook(
            year=2025,
            months=[9, 10, 11],
            schedules=multi_schedule,
            summary=self.sample_summary,
            employees_data=self.sample_employees
        )
        
        self.assertTrue(filepath.exists())
        # Should be larger file with multiple sheets
        self.assertGreater(filepath.stat().st_size, 2000)
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        filepath = self.writer.write_schedule_workbook(
            year=2025,
            months=[9],
            schedules={},
            summary=[],
            employees_data=[]
        )
        
        self.assertTrue(filepath.exists())
        # Should still create valid Excel file
        self.assertGreater(filepath.stat().st_size, 500)
    
    def test_date_range_expansion(self):
        """Test that date ranges are properly expanded"""
        employee_with_range = {
            "name": "Range Employee",
            "email": "range@example.com",
            "blocked_days": [],
            "blocked_ranges": [{"start": "2025-09-10", "end": "2025-09-15"}],
            "observes_sabbath": False
        }
        
        blocked_days = self.writer._get_blocked_days(2025, 9, [employee_with_range])
        
        # Should include all days in range
        expected_days = ["2025-09-10", "2025-09-11", "2025-09-12", 
                        "2025-09-13", "2025-09-14", "2025-09-15"]
        
        for day in expected_days:
            self.assertIn(day, blocked_days)
            self.assertIn("Range Employee", blocked_days[day])
    
    def test_cross_month_range_handling(self):
        """Test handling of date ranges that cross month boundaries"""
        cross_month_employee = {
            "name": "Cross Month",
            "email": "cross@example.com", 
            "blocked_days": [],
            "blocked_ranges": [{"start": "2025-08-25", "end": "2025-09-05"}],
            "observes_sabbath": False
        }
        
        # Test September - should only include September days from range
        blocked_days = self.writer._get_blocked_days(2025, 9, [cross_month_employee])
        
        # Should include Sep 1-5 but not August days
        self.assertIn("2025-09-01", blocked_days)
        self.assertIn("2025-09-05", blocked_days)
        self.assertNotIn("2025-08-25", blocked_days)


if __name__ == "__main__":
    unittest.main()

