# On-Duty Scheduler - Complete Setup Guide

## Holiday Management

### Quick Start
The system comes pre-loaded with **vacation days only** for Israel 2025 (when people don't work). Holidays are classified as HO (Holiday) duty type with higher weight (3.0 points) but do NOT automatically block employees.

### Holiday Commands
```bash
# List all holidays for 2025
python -m src.holiday_manager list --year 2025

# Show holidays for December
python -m src.holiday_manager show 2025 12

# Add company-specific holiday
python -m src.holiday_manager add "Company Anniversary" "2025-06-15" --type custom

# Remove a holiday
python -m src.holiday_manager remove "2025-06-15"
```

### Integration
-  Holidays automatically applied when generating schedules
-  Shows in console output: " Applying 2 holidays as blocked days"
-  Appears in Excel with holiday color coding
-  Affects balance calculation (fewer working days = better distribution)

##  Email Management

### Best Setup Options

#### Option 1: Gmail (Recommended)
```bash
# 1. Enable 2-factor authentication on Gmail
# 2. Generate app password: https://myaccount.google.com/apppasswords
# 3. Configure:
python -m src.email_manager config \
  --server smtp.gmail.com \
  --port 587 \
  --username your-email@gmail.com \
  --password your-app-password \
  --from-name "HR On-Duty Scheduler"
```

#### Option 2: Outlook/Office 365
```bash
python -m src.email_manager config \
  --server smtp-mail.outlook.com \
  --port 587 \
  --username your-email@outlook.com \
  --password your-password \
  --from-name "On-Duty Scheduler"
```

#### Option 3: Company SMTP Server
```bash
python -m src.email_manager config \
  --server mail.company.com \
  --port 587 \
  --username your-username \
  --password your-password \
  --from-name "Company Scheduler"
```

### Test Your Setup
```bash
# Test connection
python -m src.email_manager test

# Send test email
python -m src.email_manager send-test --to colleague@company.com
```

### Email Features
-  **Schedule Notifications**: Automatic emails with employee assignments
-  **Swap Invitations**: Email requests when employees want to swap duties
-  **Swap Confirmations**: Confirmation emails when swaps are approved
-  **Manager Summaries**: Balance reports for managers

## Complete Workflow

### 1. Setup (One Time)
```bash
# Configure email
python -m src.email_manager config --server smtp.gmail.com --port 587 --username you@gmail.com --password app-password

# Add company holidays
python -m src.holiday_manager add "Company Day" "2025-08-15" --type company

# Test everything
python -m src.email_manager test
```

### 2. Add Blocked Days
```bash
# Command line interface
python -m src.blocked_days_manager range "Employee Name" "2025-12-20" "2025-12-30"

# Bulk add multiple employees to same date
python -m src.blocked_days_manager bulk "2025-12-25" "Employee 1" "Employee 2" "Employee 3"
```

### 3. Generate Schedules
```bash
# Single month
python -m src.main --months 12

# Multi-month period
python -m src.main --months 10 11 12 --year 2025
```

### 4. Manual Adjustments (If Needed)
```bash
# View assignments for specific employee
python -m src.manual_swap data/summaries/2025_12/schedule_2025-12.json --list "Employee Name"

# Make specific swap (sends emails automatically)
python -m src.manual_swap data/summaries/2025_12/schedule_2025-12.json --swap 2025-12-15 WD 2025-12-20 WD
```

## Output Files

### Generated Files per Period
```
data/summaries/2025_12/
├── schedule_2025-12.json          # Raw schedule data
├── summary_2025_12.csv            # Balance summary
└── Schedule_2025_12.xlsx          # Beautiful Excel with:
    ├── Summary sheet              #   Balance overview
    └── 12_December sheet          #   Calendar matrix with colors
```

### Excel Features
- **Color-coded duties**: WD=yellow, Th=orange, WE=green, B=blue
- **Blocked days**: Red cells with "-" symbol
- **Holidays**: Purple cells (HO)
- **Balance totals**: Right side columns
- **Day headers**: Matching colors (Mon-Wed=yellow, Thu=orange, Fri-Sun=green)

## Best Practices

### For Better Balance
1. **Add realistic blocked days** (vacations, personal commitments)
2. **Use multi-month scheduling** for better distribution
3. **Check balance** in the summary output
4. **Use manual swaps** for fine-tuning if needed

### For Email Integration
1. **Use app passwords** (not regular passwords) for Gmail
2. **Test connection** before going live
3. **Start with disabled emails** for testing (`"enabled": false` in config)
4. **Add manager email** for summary reports

### For Holiday Management
1. **Add company-specific holidays** beyond the defaults
2. **Review holidays annually** and update as needed
3. **Consider religious diversity** in your team
4. **Use custom types** for different holiday categories

## Troubleshooting

### Email Issues
- **"Authentication failed"**: Use app password, not regular password
- **"Connection refused"**: Check server and port settings
- **"Port 587 blocked"**: Try port 465 or contact IT

### Balance Issues
- **Someone has too many assignments**: Add blocked days for others
- **Spread too wide**: Reduce BALANCE_TOLERANCE in config.py
- **Manual adjustment needed**: Use manual swap tool


## Ready for Production

Your scheduler now includes:
- ✅ Holiday management with Israeli holidays pre-loaded
- ✅ Email notifications with multiple provider support  
- ✅ Command-line interface for blocked days management
- ✅ Beautiful Excel output with color coding
- ✅ Balance optimization algorithms
-  Manual swap functionality with email integration
-  Comprehensive testing and error handling

**The system is enterprise-ready!**
