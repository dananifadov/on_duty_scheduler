#!/usr/bin/env python3
"""
Data Team On-Duty Scheduler - Simple Entry Point

Usage:
    python main.py add     # Add employee
    python main.py list    # List employees  
    python main.py remove  # Remove employee
    python main.py update  # Update employee
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))



if __name__ == '__main__':
    pass
