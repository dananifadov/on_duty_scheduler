# Data Team On-Duty Scheduler 🗓️

A comprehensive scheduling system for managing on-duty rotations for data teams, with support for religious observances, fair workload distribution, and flexible constraint management.

## 🚀 Features

- **Intelligent Scheduling**: Automatically generate fair and balanced duty schedules
- **Religious Observance Support**: Respect Sabbath and other religious constraints
- **Flexible Constraint Management**: Handle blocked days, preferences, and availability
- **Weighted Scoring System**: Ensure equitable workload distribution
- **Weekend Coverage**: Automatic primary + backup assignment for weekends
- **CLI Interface**: Easy-to-use command-line tools for schedule management
- **Holiday Integration**: Special handling for company and national holidays

## 📋 Scoring System

The scheduler uses a weighted point system to ensure fair distribution:

- **Regular weekdays**: 1.0 point
- **Thursday**: 1.5 points (preparation for weekend)
- **Weekend days**: 2.0 points
- **Holidays**: 3.0 points
- **Backup shifts**: 0.5 points

## 🛠️ Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/on-duty-scheduler.git
   cd on-duty-scheduler
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. **Install development dependencies** (optional):
   ```bash
   pip install -e ".[dev]"
   ```

5. **Set up pre-commit hooks** (optional):
   ```bash
   pre-commit install
   ```

## 🎯 Usage

### Basic Commands

```bash
# Generate a schedule for Q1 2024
scheduler generate --start-date 2024-01-01 --end-date 2024-03-31

# Import employee data
scheduler import-employees --file data/employees.json

# List all employees
scheduler list-employees

# Export schedule to CSV
scheduler export --format csv --output schedule.csv
```

### Employee Data Format

Create a JSON file with employee information:

```json
[
  {
    "name": "Dana",
    "email": "dana@example.com",
    "weekend_days": ["Saturday"],
    "observes_sabbath": true,
    "blocked_days": ["2024-06-15", "2024-07-01"]
  },
  {
    "name": "Eli",
    "email": "eli@example.com",
    "weekend_days": ["Friday", "Saturday"],
    "observes_sabbath": true,
    "blocked_days": []
  }
]
```

### Configuration

The scheduler can be configured through environment variables or a config file:

```bash
# Set timezone
export SCHEDULER_TIMEZONE="UTC"

# Set working days (Monday=0, Sunday=6)
export SCHEDULER_WORKING_DAYS="0,1,2,3,4"

# Set holiday calendar
export SCHEDULER_HOLIDAY_CALENDAR="US"
```

## 📚 Development

### Project Structure

```
on_duty_scheduler/
├── scheduler/           # Core scheduling logic
│   ├── models.py       # Data models
│   ├── generator.py    # Schedule generation
│   ├── scoring.py      # Scoring system
│   ├── validator.py    # Constraint validation
│   └── cli.py          # Command-line interface
├── data/               # Sample data files
├── tests/              # Test suite
├── old/                # Legacy code (deprecated)
└── docs/               # Documentation
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scheduler

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Format code
black scheduler/ tests/

# Sort imports
isort scheduler/ tests/

# Lint code
flake8 scheduler/ tests/

# Type checking
mypy scheduler/
```

### Pre-commit Hooks

Pre-commit hooks run automatically on every commit:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 🚀 Release Plan

### Phase 1: Foundation (v0.1.0) - Current
- ✅ Basic data models
- ✅ Core scheduling algorithm
- ✅ CLI interface
- ✅ Constraint validation
- ✅ Scoring system

### Phase 2: Advanced Features (v0.2.0) - Next
- 🔄 Holiday integration
- 🔄 Advanced fairness optimization
- 🔄 Reporting and analytics
- 🔄 Data import/export

### Phase 3: Integration (v0.3.0)
- 📋 PagerDuty integration
- 📋 Web interface
- 📋 Email notifications
- 📋 Database persistence

### Phase 4: Enterprise (v1.0.0)
- 📋 Multi-team support
- 📋 API endpoints
- 📋 Advanced security
- 📋 Performance optimization

## 🧪 Testing

### Test Data

The project includes factory functions for generating test data:

```python
from tests.factories import EmployeeFactory, ConstraintFactory

# Create test employees
employees = EmployeeFactory.create_batch(5)

# Create test constraints
constraints = ConstraintFactory.create_batch(10)
```

### Test Coverage

Maintain >80% test coverage:

```bash
# Generate coverage report
pytest --cov=scheduler --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📖 API Reference

### Core Classes

#### Employee
```python
class Employee(BaseModel):
    id: str
    name: str
    email: str
    observes_sabbath: bool = False
    weekend_days: List[str] = []
    blocked_days: List[str] = []
```

#### Schedule
```python
class Schedule(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    shifts: List[Shift] = []
```

#### Shift
```python
class Shift(BaseModel):
    id: str
    date: date
    employee_id: str
    shift_type: ShiftType
    points: float
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints for all function signatures
- Add docstrings for public functions and classes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: data-team@company.com
- 💬 Slack: #data-team-support
- 📝 Issues: [GitHub Issues](https://github.com/your-org/on-duty-scheduler/issues)

## 🙏 Acknowledgments

- The data team for requirements and feedback
- Open source scheduling libraries for inspiration
- The Python community for excellent tools and libraries

## 🔄 Changelog

### v0.1.0 (Current)
- Initial release with basic scheduling functionality
- CLI interface for schedule generation
- Employee and constraint management
- Sabbath observance support
- Fair workload distribution

---

**Happy Scheduling!** 🎉 