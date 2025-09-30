# On-Duty Scheduler

A fair and balanced employee scheduling system for on-duty shifts with weighted duty types and multi-month support.

## Features

- **Fair Assignment**: Balances workload using weighted point system
- **Multi-Duty Types**: Supports WD (weekday), Th (Thursday), WE (weekend), B (backup)
- **Flexible Blocking**: Employee availability via blocked days and date ranges
- **Sabbath Support**: Automatic Friday/Saturday blocking for observant employees
- **Multi-Month Scheduling**: Generate schedules across multiple months
- **Balance Optimization**: Minimizes variance in assignments across team
- **Summary Reports**: Detailed CSV reports with balance analysis

## Quick Start

```bash
# Generate schedule for September 2025 (default)
python -m src.main

# Generate for multiple months
python -m src.main --year 2025 --months 9 10 11

# Custom year and month
python -m src.main --year 2024 --months 12
```

## Project Structure

```
src/
├── main.py           # CLI entry point
├── scheduler.py      # Core scheduling logic
├── employee.py       # Employee model and availability
├── loader.py         # Data loading utilities
├── calendar_utils.py # Date/duty classification
└── config.py         # Configuration and weights

data/
├── employees.json    # Employee data (input)
├── schedule_*.json   # Generated schedules (output)
└── summaries/        # CSV summary reports (output)
```

## Configuration

Edit `src/config.py` to adjust:

- **Duty Weights**: Point values for different duty types
- **Balance Tolerance**: Algorithm sensitivity for fairness
- **Directory Paths**: Input/output locations

## Employee Data Format

```json
[
  {
    "name": "John Doe",
    "email": "john@example.com",
    "country": "Israel",
    "observes_sabbath": true,
    "position_percentage": 100,
    "blocked_days": ["2025-09-15"],
    "blocked_ranges": [
      {"start": "2025-09-20", "end": "2025-09-25"}
    ]
  }
]
```

## Algorithm

1. **Load** employee data and availability
2. **Classify** each day as WD/Th/WE duty type
3. **Filter** available employees for each day
4. **Select** employee with lowest points (with variance minimization)
5. **Assign** and update points based on duty weights
6. **Accumulate** across months for multi-month fairness

## Output

### Schedules
JSON files with daily assignments:
```json
{
  "2025-09-01": {"WD": "John Doe"},
  "2025-09-06": {"WE": "Jane Smith", "B": "Bob Wilson"}
}
```

### Summary Reports
CSV files with balance analysis showing total assignments, averages, and balance deviations.

## Dependencies

Pure Python 3.7+ - no external dependencies required.