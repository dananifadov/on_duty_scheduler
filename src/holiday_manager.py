#!/usr/bin/env python3
"""
Holiday Management System
Manages holidays and integrates them with the scheduling system
"""
import json
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional
import calendar

class HolidayManager:
    """Manages holidays and their integration with scheduling"""
    
    def __init__(self, holidays_file: str = "data/holidays.json"):
        self.holidays_file = Path(holidays_file)
        self.holidays = self._load_holidays()
    
    def _load_holidays(self) -> List[Dict]:
        """Load holidays from JSON file - converts clustered format to flat list"""
        if not self.holidays_file.exists():
            return []
        
        with open(self.holidays_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert new clustered format to flat list for backward compatibility
        if isinstance(data, dict) and any(year.isdigit() for year in data.keys()):
            # New clustered format
            holidays = []
            for year, year_data in data.items():
                for month, month_holidays in year_data.items():
                    holidays.extend(month_holidays)
            return holidays
        else:
            # Old flat format (backward compatibility)
            return data
    
    def _save_holidays(self):
        """Save holidays back to JSON file in clustered format"""
        # Group holidays by year and month
        clustered = {}
        
        for holiday in self.holidays:
            holiday_date = date.fromisoformat(holiday['date'])
            year_str = str(holiday_date.year)
            month_name = calendar.month_name[holiday_date.month]
            
            if year_str not in clustered:
                clustered[year_str] = {}
            if month_name not in clustered[year_str]:
                clustered[year_str][month_name] = []
                
            clustered[year_str][month_name].append(holiday)
        
        # Sort months within each year
        for year in clustered:
            month_order = [calendar.month_name[i] for i in range(1, 13)]
            ordered_months = {}
            for month in month_order:
                if month in clustered[year]:
                    ordered_months[month] = clustered[year][month]
            clustered[year] = ordered_months
        
        with open(self.holidays_file, 'w', encoding='utf-8') as f:
            json.dump(clustered, f, indent=2, ensure_ascii=False)
    
    def add_holiday(self, name: str, date_str: str, holiday_type: str = "custom", country: str = "Israel") -> bool:
        """Add a new holiday"""
        try:
            # Validate date format
            date.fromisoformat(date_str)
        except ValueError:
            return False
        
        # Check if holiday already exists
        for holiday in self.holidays:
            if holiday['date'] == date_str:
                return False  # Holiday already exists on this date
        
        new_holiday = {
            "name": name,
            "date": date_str,
            "type": holiday_type,
            "country": country
        }
        
        self.holidays.append(new_holiday)
        self.holidays.sort(key=lambda h: h['date'])  # Keep sorted by date
        self._save_holidays()
        return True
    
    def remove_holiday(self, date_str: str) -> bool:
        """Remove a holiday by date"""
        for i, holiday in enumerate(self.holidays):
            if holiday['date'] == date_str:
                self.holidays.pop(i)
                self._save_holidays()
                return True
        return False
    
    def get_holidays_for_month(self, year: int, month: int) -> List[Dict]:
        """Get all holidays for a specific month"""
        month_holidays = []
        for holiday in self.holidays:
            holiday_date = date.fromisoformat(holiday['date'])
            if holiday_date.year == year and holiday_date.month == month:
                month_holidays.append(holiday)
        return month_holidays
    
    def get_holidays_for_year(self, year: int) -> List[Dict]:
        """Get all holidays for a specific year"""
        year_holidays = []
        for holiday in self.holidays:
            holiday_date = date.fromisoformat(holiday['date'])
            if holiday_date.year == year:
                year_holidays.append(holiday)
        return year_holidays
    
    def is_holiday(self, date_str: str) -> Optional[Dict]:
        """Check if a date is a holiday and return holiday info"""
        for holiday in self.holidays:
            if holiday['date'] == date_str:
                return holiday
        return None
    
    def get_holiday_calendar(self, year: int, month: int) -> Dict[int, Dict]:
        """Get a calendar view of holidays for a specific month"""
        holiday_calendar = {}
        holidays = self.get_holidays_for_month(year, month)
        
        for holiday in holidays:
            holiday_date = date.fromisoformat(holiday['date'])
            holiday_calendar[holiday_date.day] = holiday
        
        return holiday_calendar
    
    def apply_holidays_to_employees(self, employees_data: List[Dict], year: int, months: List[int]):
        """DEPRECATED: Holidays are no longer applied as blocked days.
        They are now handled as HO (Holiday) duty type with higher weight (3.0).
        This method is kept for backward compatibility but does nothing."""
        pass
    
    def list_holidays(self, year: Optional[int] = None) -> List[Dict]:
        """List all holidays, optionally filtered by year"""
        if year is None:
            return self.holidays
        return self.get_holidays_for_year(year)


def holiday_cli():
    """Command-line interface for holiday management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage holidays")
    parser.add_argument("--holidays-file", default="data/holidays.json", 
                       help="Path to holidays JSON file")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List holidays
    list_parser = subparsers.add_parser('list', help='List all holidays')
    list_parser.add_argument('--year', type=int, help='Filter by year')
    
    # Show holidays for month
    show_parser = subparsers.add_parser('show', help='Show holidays for month')
    show_parser.add_argument('year', type=int, help='Year')
    show_parser.add_argument('month', type=int, help='Month')
    
    # Add holiday
    add_parser = subparsers.add_parser('add', help='Add holiday')
    add_parser.add_argument('name', help='Holiday name')
    add_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    add_parser.add_argument('--type', default='custom', help='Holiday type')
    add_parser.add_argument('--country', default='Israel', help='Country')
    
    # Remove holiday
    remove_parser = subparsers.add_parser('remove', help='Remove holiday')
    remove_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = HolidayManager(args.holidays_file)
    
    try:
        if args.command == 'list':
            holidays = manager.list_holidays(args.year)
            if holidays:
                print(f"Holidays{' for ' + str(args.year) if args.year else ''}:")
                for holiday in holidays:
                    print(f"  {holiday['date']}: {holiday['name']} ({holiday['type']})")
            else:
                print("No holidays found")
        
        elif args.command == 'show':
            holiday_calendar = manager.get_holiday_calendar(args.year, args.month)
            month_name = calendar.month_name[args.month]
            print(f"\nHolidays in {month_name} {args.year}:")
            
            if holiday_calendar:
                for day, holiday in holiday_calendar.items():
                    print(f"  {day:2d}: {holiday['name']} ({holiday['type']})")
            else:
                print("  No holidays")
        
        elif args.command == 'add':
            success = manager.add_holiday(args.name, args.date, args.type, args.country)
            if success:
                print(f"Added holiday: {args.name} on {args.date}")
            else:
                print(f" Failed to add holiday (invalid date or already exists)")
        
        elif args.command == 'remove':
            success = manager.remove_holiday(args.date)
            if success:
                print(f"Removed holiday on {args.date}")
            else:
                print(f"No holiday found on {args.date}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(holiday_cli())
