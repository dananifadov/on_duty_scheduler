#!/usr/bin/env python3
"""
Email Management System for On-Duty Scheduler
Handles sending schedule notifications and swap invitations
"""
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

class EmailManager:
    """Manages email notifications for scheduling system"""
    
    def __init__(self, config_file: str = "config/email_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load email configuration"""
        default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_name": "On-Duty Scheduler",
            "enabled": False
        }
        
        if not self.config_file.exists():
            # Create config directory if needed
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        
        return config
    
    def configure(self, smtp_server: str, smtp_port: int, username: str, password: str, from_name: str = "On-Duty Scheduler"):
        """Configure email settings"""
        self.config.update({
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "from_name": from_name,
            "enabled": True
        })
        
        # Save config
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def test_connection(self) -> bool:
        """Test email connection"""
        if not self.config.get('enabled', False):
            return False
        
        try:
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['username'], self.config['password'])
            server.quit()
            return True
        except Exception as e:
            print(f"Email connection test failed: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send an email"""
        if not self.config.get('enabled', False):
            print(f"📧 Email disabled - Would send to {to_email}: {subject}")
            return True  # Return True for testing purposes
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.config['from_name']} <{self.config['username']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['username'], self.config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def send_schedule_notification(self, employee_email: str, employee_name: str, assignments: List[Dict], month_year: str) -> bool:
        """Send schedule notification to employee"""
        subject = f"📅 Your On-Duty Schedule for {month_year}"
        
        # Create assignment list
        assignment_text = ""
        for assignment in assignments:
            duty_names = {
                'WD': 'Weekday Duty',
                'Th': 'Thursday Duty',
                'WE': 'Weekend Duty',
                'B': 'Backup Duty',
                'HO': 'Holiday Duty'
            }
            duty_name = duty_names.get(assignment['duty'], assignment['duty'])
            assignment_text += f"• {assignment['date']}: {duty_name}\n"
        
        body = f"""
Hi {employee_name},

Your on-duty schedule for {month_year} is ready:

{assignment_text}

Please review your assignments and let us know if you have any conflicts.

Best regards,
On-Duty Scheduler System
        """.strip()
        
        return self._send_email(employee_email, subject, body)
    
    def send_swap_invitation(self, from_emp: Dict, to_emp: Dict, swap_details: Dict) -> bool:
        """Send swap invitation email"""
        subject = f"🔄 Duty Swap Request from {from_emp['name']}"
        
        duty_names = {
            'WD': 'Weekday Duty',
            'Th': 'Thursday Duty', 
            'WE': 'Weekend Duty',
            'B': 'Backup Duty',
            'HO': 'Holiday Duty'
        }
        
        from_duty = duty_names.get(swap_details['from_duty'], swap_details['from_duty'])
        to_duty = duty_names.get(swap_details['to_duty'], swap_details['to_duty'])
        
        body = f"""
Hi {to_emp['name']},

{from_emp['name']} has requested to swap duties with you:

PROPOSED SWAP:
• {from_emp['name']}: {swap_details['from_date']} ({from_duty}) → {swap_details['to_date']} ({to_duty})
• {to_emp['name']}: {swap_details['to_date']} ({to_duty}) → {swap_details['from_date']} ({from_duty})

Please respond if you agree to this swap.

Best regards,
On-Duty Scheduler System
        """.strip()
        
        return self._send_email(to_emp['email'], subject, body)
    
    def send_swap_confirmation(self, emp1: Dict, emp2: Dict, swap_details: Dict) -> bool:
        """Send swap confirmation to both employees"""
        subject = f"✅ Duty Swap Confirmed"
        
        duty_names = {
            'WD': 'Weekday Duty',
            'Th': 'Thursday Duty',
            'WE': 'Weekend Duty', 
            'B': 'Backup Duty',
            'HO': 'Holiday Duty'
        }
        
        from_duty = duty_names.get(swap_details['from_duty'], swap_details['from_duty'])
        to_duty = duty_names.get(swap_details['to_duty'], swap_details['to_duty'])
        
        # Send to both employees
        success1 = self._send_email(
            emp1['email'],
            subject,
            f"""
Hi {emp1['name']},

Your duty swap has been confirmed:

NEW ASSIGNMENT:
• You now have: {swap_details['to_date']} ({to_duty})
• {emp2['name']} now has: {swap_details['from_date']} ({from_duty})

Please update your calendars accordingly.

Best regards,
On-Duty Scheduler System
            """.strip()
        )
        
        success2 = self._send_email(
            emp2['email'],
            subject,
            f"""
Hi {emp2['name']},

Your duty swap has been confirmed:

NEW ASSIGNMENT:
• You now have: {swap_details['from_date']} ({from_duty})
• {emp1['name']} now has: {swap_details['to_date']} ({to_duty})

Please update your calendars accordingly.

Best regards,
On-Duty Scheduler System
            """.strip()
        )
        
        return success1 and success2
    
    def send_schedule_summary(self, manager_email: str, summary_data: Dict, period: str) -> bool:
        """Send schedule summary to manager"""
        subject = f"📊 Schedule Summary for {period}"
        
        # Create summary table
        summary_text = "SCHEDULE SUMMARY:\n"
        summary_text += "=" * 50 + "\n"
        
        for emp_summary in summary_data.get('employees', []):
            name = emp_summary.get('Employee', 'Unknown')
            total = emp_summary.get('Total', 0)
            balance = emp_summary.get('Balance', 0)
            summary_text += f"{name:15}: {total:4.1f} points (balance: {balance:+.1f})\n"
        
        body = f"""
Schedule summary for {period} is ready:

{summary_text}

Full details are available in the Excel report.

Best regards,
On-Duty Scheduler System
        """.strip()
        
        return self._send_email(manager_email, subject, body)


def email_cli():
    """Command-line interface for email management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage email settings and send notifications")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Configure email
    config_parser = subparsers.add_parser('config', help='Configure email settings')
    config_parser.add_argument('--server', required=True, help='SMTP server')
    config_parser.add_argument('--port', type=int, default=587, help='SMTP port')
    config_parser.add_argument('--username', required=True, help='Email username')
    config_parser.add_argument('--password', required=True, help='Email password')
    config_parser.add_argument('--from-name', default='On-Duty Scheduler', help='From name')
    
    # Test connection
    test_parser = subparsers.add_parser('test', help='Test email connection')
    
    # Send test email
    send_parser = subparsers.add_parser('send-test', help='Send test email')
    send_parser.add_argument('--to', required=True, help='Recipient email')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = EmailManager()
    
    try:
        if args.command == 'config':
            manager.configure(
                args.server, args.port, args.username, 
                args.password, args.from_name
            )
            print("✅ Email configuration saved")
        
        elif args.command == 'test':
            success = manager.test_connection()
            if success:
                print("✅ Email connection successful")
            else:
                print("❌ Email connection failed")
        
        elif args.command == 'send-test':
            success = manager._send_email(
                args.to,
                "Test Email from On-Duty Scheduler",
                "This is a test email from the on-duty scheduler system."
            )
            if success:
                print(f"✅ Test email sent to {args.to}")
            else:
                print(f"❌ Failed to send test email to {args.to}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(email_cli())

