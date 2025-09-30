#!/usr/bin/env python3
"""
Manual employee swapping functionality with email notifications
"""
import json
import smtplib
from datetime import date, datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional, List

class ManualSwapManager:
    """Handles manual employee assignment swaps and notifications"""
    
    def __init__(self, schedule_file: str, employees_file: str = None):
        self.schedule_file = Path(schedule_file)
        self.employees_file = Path(employees_file) if employees_file else None
        self.schedule = self._load_schedule()
        self.employees = self._load_employees() if self.employees_file else {}
    
    def _load_schedule(self) -> Dict:
        """Load schedule from JSON file"""
        if not self.schedule_file.exists():
            raise FileNotFoundError(f"Schedule file not found: {self.schedule_file}")
        
        with open(self.schedule_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_employees(self) -> Dict[str, Dict]:
        """Load employee data and create name->data mapping"""
        if not self.employees_file or not self.employees_file.exists():
            return {}
        
        with open(self.employees_file, 'r', encoding='utf-8') as f:
            employees_list = json.load(f)
        
        return {emp['name']: emp for emp in employees_list}
    
    def _save_schedule(self):
        """Save modified schedule back to file"""
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(self.schedule, f, indent=2, ensure_ascii=False)
    
    def list_assignments(self, employee_name: str = None, date_filter: str = None) -> List[Dict]:
        """
        List assignments, optionally filtered by employee or date
        Returns list of {date, duty, employee, available_for_swap}
        """
        assignments = []
        
        for date_str, day_assignments in self.schedule.items():
            if date_filter and date_filter not in date_str:
                continue
                
            for duty, assigned_employee in day_assignments.items():
                if employee_name and assigned_employee != employee_name:
                    continue
                
                assignments.append({
                    'date': date_str,
                    'duty': duty,
                    'employee': assigned_employee,
                    'available_for_swap': True  # Could add logic to check conflicts
                })
        
        # Sort by date
        assignments.sort(key=lambda x: x['date'])
        return assignments
    
    def propose_swap(self, date1: str, duty1: str, date2: str, duty2: str) -> Dict:
        """
        Propose a swap between two assignments
        Returns validation result and swap details
        """
        # Get current assignments
        day1_assignments = self.schedule.get(date1, {})
        day2_assignments = self.schedule.get(date2, {})
        
        if duty1 not in day1_assignments:
            return {'valid': False, 'error': f'No {duty1} assignment on {date1}'}
        if duty2 not in day2_assignments:
            return {'valid': False, 'error': f'No {duty2} assignment on {date2}'}
        
        emp1 = day1_assignments[duty1]
        emp2 = day2_assignments[duty2]
        
        # Check for conflicts (same person can't be on multiple duties same day)
        conflicts = []
        
        # Check if emp2 is already assigned on date1
        if emp2 in day1_assignments.values():
            conflicts.append(f'{emp2} already assigned on {date1}')
        
        # Check if emp1 is already assigned on date2
        if emp1 in day2_assignments.values():
            conflicts.append(f'{emp1} already assigned on {date2}')
        
        if conflicts:
            return {'valid': False, 'error': '; '.join(conflicts)}
        
        return {
            'valid': True,
            'emp1': emp1,
            'emp2': emp2,
            'date1': date1,
            'duty1': duty1,
            'date2': date2,
            'duty2': duty2,
            'description': f'Swap {emp1} ({duty1} on {date1}) ↔ {emp2} ({duty2} on {date2})'
        }
    
    def execute_swap(self, date1: str, duty1: str, date2: str, duty2: str, 
                     send_notifications: bool = True) -> Dict:
        """
        Execute the swap and optionally send email notifications
        """
        # Validate swap first
        validation = self.propose_swap(date1, duty1, date2, duty2)
        if not validation['valid']:
            return validation
        
        # Execute the swap
        emp1 = validation['emp1']
        emp2 = validation['emp2']
        
        self.schedule[date1][duty1] = emp2
        self.schedule[date2][duty2] = emp1
        
        # Save changes
        self._save_schedule()
        
        # Send notifications if requested
        notifications_sent = []
        if send_notifications:
            notifications_sent = self._send_swap_notifications(validation)
        
        return {
            'success': True,
            'description': validation['description'],
            'notifications_sent': notifications_sent,
            'updated_file': str(self.schedule_file)
        }
    
    def _send_swap_notifications(self, swap_details: Dict) -> List[str]:
        """Send email notifications about the swap"""
        notifications = []
        
        # Get email addresses
        emp1_email = self.employees.get(swap_details['emp1'], {}).get('email')
        emp2_email = self.employees.get(swap_details['emp2'], {}).get('email')
        
        if not emp1_email or not emp2_email:
            notifications.append("Warning: Missing email addresses, notifications not sent")
            return notifications
        
        # Create email content
        subject = f"Schedule Change: Assignment Swap for {swap_details['date1']} and {swap_details['date2']}"
        
        body = f"""
Dear Team,

A schedule swap has been executed:

{swap_details['description']}

New assignments:
• {swap_details['emp1']}: {swap_details['duty2']} on {swap_details['date2']}
• {swap_details['emp2']}: {swap_details['duty1']} on {swap_details['date1']}

Please update your calendars accordingly.

Best regards,
On-Duty Scheduler
"""
        
        # In a real implementation, you would configure SMTP settings
        # For now, just log what would be sent
        notifications.append(f"Email notification prepared for {emp1_email}")
        notifications.append(f"Email notification prepared for {emp2_email}")
        notifications.append("Note: Email sending requires SMTP configuration")
        
        return notifications


def swap_command_line():
    """Command-line interface for manual swapping"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manual assignment swapping tool")
    parser.add_argument("schedule_file", help="Path to schedule JSON file")
    parser.add_argument("--employees", help="Path to employees JSON file")
    parser.add_argument("--list", help="List assignments for employee")
    parser.add_argument("--swap", nargs=4, metavar=('DATE1', 'DUTY1', 'DATE2', 'DUTY2'),
                       help="Execute swap: date1 duty1 date2 duty2")
    parser.add_argument("--no-email", action="store_true", help="Don't send email notifications")
    
    args = parser.parse_args()
    
    try:
        manager = ManualSwapManager(args.schedule_file, args.employees)
        
        if args.list:
            assignments = manager.list_assignments(employee_name=args.list)
            print(f"\nAssignments for {args.list}:")
            for assignment in assignments:
                print(f"  {assignment['date']}: {assignment['duty']}")
        
        elif args.swap:
            date1, duty1, date2, duty2 = args.swap
            
            # First, propose the swap to check validity
            proposal = manager.propose_swap(date1, duty1, date2, duty2)
            if not proposal['valid']:
                print(f"Error: {proposal['error']}")
                return 1
            
            print(f"Proposed swap: {proposal['description']}")
            confirm = input("Execute this swap? (y/N): ")
            
            if confirm.lower() == 'y':
                result = manager.execute_swap(date1, duty1, date2, duty2, 
                                            send_notifications=not args.no_email)
                if result['success']:
                    print(f"✓ Swap executed: {result['description']}")
                    print(f"✓ Schedule updated: {result['updated_file']}")
                    for notification in result['notifications_sent']:
                        print(f"✓ {notification}")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
            else:
                print("Swap cancelled.")
        
        else:
            print("Use --list EMPLOYEE or --swap DATE1 DUTY1 DATE2 DUTY2")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(swap_command_line())
