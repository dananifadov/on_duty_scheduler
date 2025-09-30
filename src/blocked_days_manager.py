#!/usr/bin/env python3
"""
Blocked Days Management System
Easy interface to manage employee blocked days and ranges
"""
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import calendar

class BlockedDaysManager:
    """Manages employee blocked days with easy add/remove operations"""
    
    def __init__(self, employees_file: str = "data/employees.json"):
        self.employees_file = Path(employees_file)
        self.employees = self._load_employees()
    
    def _load_employees(self) -> List[Dict]:
        """Load employees from JSON file"""
        if not self.employees_file.exists():
            return []
        
        with open(self.employees_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_employees(self):
        """Save employees back to JSON file"""
        with open(self.employees_file, 'w', encoding='utf-8') as f:
            json.dump(self.employees, f, indent=2, ensure_ascii=False)
    
    def list_employees(self) -> List[str]:
        """Get list of all employee names"""
        return [emp['name'] for emp in self.employees]
    
    def get_employee_blocked_days(self, employee_name: str) -> Dict:
        """Get blocked days and ranges for an employee"""
        for emp in self.employees:
            if emp['name'] == employee_name:
                return {
                    'blocked_days': emp.get('blocked_days', []),
                    'blocked_ranges': emp.get('blocked_ranges', []),
                    'observes_sabbath': emp.get('observes_sabbath', False)
                }
        return {'blocked_days': [], 'blocked_ranges': [], 'observes_sabbath': False}
    
    def add_blocked_day(self, employee_name: str, blocked_date: str) -> bool:
        """Add a single blocked day for an employee"""
        # Validate date format
        try:
            date.fromisoformat(blocked_date)
        except ValueError:
            return False
        
        for emp in self.employees:
            if emp['name'] == employee_name:
                if 'blocked_days' not in emp:
                    emp['blocked_days'] = []
                
                if blocked_date not in emp['blocked_days']:
                    emp['blocked_days'].append(blocked_date)
                    emp['blocked_days'].sort()
                    self._save_employees()
                    return True
        return False
    
    def remove_blocked_day(self, employee_name: str, blocked_date: str) -> bool:
        """Remove a single blocked day for an employee"""
        for emp in self.employees:
            if emp['name'] == employee_name:
                if 'blocked_days' in emp and blocked_date in emp['blocked_days']:
                    emp['blocked_days'].remove(blocked_date)
                    self._save_employees()
                    return True
        return False
    
    def add_blocked_range(self, employee_name: str, start_date: str, end_date: str) -> bool:
        """Add a blocked date range for an employee"""
        # Validate date formats
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            if start > end:
                start, end = end, start  # Swap if wrong order
        except ValueError:
            return False
        
        for emp in self.employees:
            if emp['name'] == employee_name:
                if 'blocked_ranges' not in emp:
                    emp['blocked_ranges'] = []
                
                # Check for overlapping ranges
                new_range = {'start': start.isoformat(), 'end': end.isoformat()}
                emp['blocked_ranges'].append(new_range)
                self._save_employees()
                return True
        return False
    
    def remove_blocked_range(self, employee_name: str, start_date: str, end_date: str) -> bool:
        """Remove a blocked date range for an employee"""
        for emp in self.employees:
            if emp['name'] == employee_name:
                if 'blocked_ranges' in emp:
                    # Find and remove the matching range
                    for i, range_data in enumerate(emp['blocked_ranges']):
                        if (range_data['start'] == start_date and 
                            range_data['end'] == end_date):
                            emp['blocked_ranges'].pop(i)
                            self._save_employees()
                            return True
        return False
    
    def get_blocked_calendar(self, employee_name: str, year: int, month: int) -> Dict[int, str]:
        """Get a calendar view of blocked days for a specific month"""
        blocked_info = self.get_employee_blocked_days(employee_name)
        blocked_calendar = {}
        
        # Get all days in the month
        days_in_month = calendar.monthrange(year, month)[1]
        
        for day in range(1, days_in_month + 1):
            day_date = date(year, month, day)
            day_str = day_date.isoformat()
            
            # Check if blocked
            is_blocked = False
            reason = ""
            
            # Check single blocked days
            if day_str in blocked_info['blocked_days']:
                is_blocked = True
                reason = "Single day block"
            
            # Check blocked ranges
            for range_data in blocked_info['blocked_ranges']:
                start_date = date.fromisoformat(range_data['start'])
                end_date = date.fromisoformat(range_data['end'])
                if start_date <= day_date <= end_date:
                    is_blocked = True
                    reason = f"Range: {range_data['start']} to {range_data['end']}"
                    break
            
            # Check sabbath
            if blocked_info['observes_sabbath'] and day_date.weekday() in (4, 5):
                is_blocked = True
                reason = "Sabbath observance"
            
            if is_blocked:
                blocked_calendar[day] = reason
        
        return blocked_calendar
    
    def bulk_add_days(self, employee_name: str, dates: List[str]) -> Dict[str, bool]:
        """Add multiple blocked days at once"""
        results = {}
        for date_str in dates:
            results[date_str] = self.add_blocked_day(employee_name, date_str)
        return results
    
    def bulk_add_employees_to_date(self, date_str: str, employee_names: List[str]) -> Dict[str, bool]:
        """Add multiple employees to be blocked on the same date"""
        # Validate date format
        try:
            date.fromisoformat(date_str)
        except ValueError:
            return {emp: False for emp in employee_names}
        
        results = {}
        for employee_name in employee_names:
            results[employee_name] = self.add_blocked_day(employee_name, date_str)
        return results
    
    def clear_all_blocked_days(self, employee_name: str) -> bool:
        """Clear all blocked days and ranges for an employee"""
        for emp in self.employees:
            if emp['name'] == employee_name:
                emp['blocked_days'] = []
                emp['blocked_ranges'] = []
                self._save_employees()
                return True
        return False


def blocked_days_cli():
    """Command-line interface for blocked days management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage employee blocked days")
    parser.add_argument("--employees-file", default="data/employees.json", 
                       help="Path to employees JSON file")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List employees
    list_parser = subparsers.add_parser('list', help='List all employees')
    
    # Show blocked days
    show_parser = subparsers.add_parser('show', help='Show blocked days for employee')
    show_parser.add_argument('employee', help='Employee name')
    show_parser.add_argument('--year', type=int, help='Year for calendar view')
    show_parser.add_argument('--month', type=int, help='Month for calendar view')
    
    # Add blocked day
    add_parser = subparsers.add_parser('add', help='Add blocked day')
    add_parser.add_argument('employee', help='Employee name')
    add_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    
    # Add blocked range
    range_parser = subparsers.add_parser('range', help='Add blocked date range')
    range_parser.add_argument('employee', help='Employee name')
    range_parser.add_argument('start_date', help='Start date in YYYY-MM-DD format')
    range_parser.add_argument('end_date', help='End date in YYYY-MM-DD format')
    
    # Remove blocked day
    remove_parser = subparsers.add_parser('remove', help='Remove blocked day')
    remove_parser.add_argument('employee', help='Employee name')
    remove_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    
    # Clear all
    clear_parser = subparsers.add_parser('clear', help='Clear all blocked days for employee')
    clear_parser.add_argument('employee', help='Employee name')
    
    # Bulk add employees to date
    bulk_parser = subparsers.add_parser('bulk', help='Add multiple employees to the same blocked date')
    bulk_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    bulk_parser.add_argument('employees', nargs='+', help='Employee names (space separated)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = BlockedDaysManager(args.employees_file)
    
    try:
        if args.command == 'list':
            employees = manager.list_employees()
            print("Employees:")
            for emp in employees:
                print(f"  {emp}")
        
        elif args.command == 'show':
            if args.year and args.month:
                # Calendar view
                blocked_calendar = manager.get_blocked_calendar(args.employee, args.year, args.month)
                month_name = calendar.month_name[args.month]
                print(f"\nBlocked days for {args.employee} in {month_name} {args.year}:")
                
                if blocked_calendar:
                    for day, reason in blocked_calendar.items():
                        print(f"  {day:2d}: {reason}")
                else:
                    print("  No blocked days")
            else:
                # Show all blocked days
                blocked_info = manager.get_employee_blocked_days(args.employee)
                print(f"\nBlocked days for {args.employee}:")
                print(f"  Single days: {blocked_info['blocked_days']}")
                print(f"  Ranges: {blocked_info['blocked_ranges']}")
                print(f"  Observes Sabbath: {blocked_info['observes_sabbath']}")
        
        elif args.command == 'add':
            success = manager.add_blocked_day(args.employee, args.date)
            if success:
                print(f"✓ Added blocked day {args.date} for {args.employee}")
            else:
                print(f"✗ Failed to add blocked day (employee not found or invalid date)")
        
        elif args.command == 'range':
            success = manager.add_blocked_range(args.employee, args.start_date, args.end_date)
            if success:
                print(f"✓ Added blocked range {args.start_date} to {args.end_date} for {args.employee}")
            else:
                print(f"✗ Failed to add blocked range (employee not found or invalid dates)")
        
        elif args.command == 'remove':
            success = manager.remove_blocked_day(args.employee, args.date)
            if success:
                print(f"✓ Removed blocked day {args.date} for {args.employee}")
            else:
                print(f"✗ Failed to remove blocked day (not found)")
        
        elif args.command == 'clear':
            success = manager.clear_all_blocked_days(args.employee)
            if success:
                print(f"✓ Cleared all blocked days for {args.employee}")
            else:
                print(f"✗ Failed to clear blocked days (employee not found)")
        
        elif args.command == 'bulk':
            results = manager.bulk_add_employees_to_date(args.date, args.employees)
            print(f"Bulk adding blocked date {args.date}:")
            for employee, success in results.items():
                if success:
                    print(f"  ✓ {employee}")
                else:
                    print(f"  ✗ {employee} (employee not found or invalid date)")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(blocked_days_cli())
