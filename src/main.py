#!/usr/bin/env python3
"""
On-Duty Scheduler - Main entry point

Generates fair work schedules based on employee availability and weighted duty types.
Supports multi-month scheduling with balance optimization and summary reporting.
"""
import argparse
import sys
from src.scheduler import Scheduler

def main():
    ap = argparse.ArgumentParser(
        description="Generate fair on-duty schedules for employees",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument("--year", type=int, default=2025, help="Target year for scheduling")
    ap.add_argument("--months", type=int, nargs="+", default=[9], 
                   help="List of months to schedule, e.g. 9 10 11")
    args = ap.parse_args()

    try:
        # Validate inputs
        if not all(1 <= m <= 12 for m in args.months):
            print("Error: All months must be between 1 and 12", file=sys.stderr)
            return 1

        print(f"Generating schedule for {args.year}, months: {args.months}")

        sch = Scheduler()
        if not sch.employees:
            print("Warning: No employees loaded. Check employees.json file.", file=sys.stderr)
            return 1

        # Load holidays for duty classification (not as blocked days)
        from src.holiday_manager import HolidayManager
        holiday_manager = HolidayManager()
        holidays = []
        for month in args.months:
            month_holidays = holiday_manager.get_holidays_for_month(args.year, month)
            holidays.extend(month_holidays)
        
        if holidays:
            print(f"Found {len(holidays)} holidays for duty weight calculation:")
            for holiday in holidays:
                print(f"  - {holiday['date']}: {holiday['name']} (HO duty type, weight: 3.0)")

        sch.assign_months(args.year, args.months)

        # Report schedule files and folder
        month_range = f"{min(args.months):02d}-{max(args.months):02d}" if len(args.months) > 1 else f"{args.months[0]:02d}"
        period_folder = f"data/summaries/{args.year}_{month_range}"
        print(f"Created period folder: {period_folder}")
        for m in args.months:
            print(f"Saved {period_folder}/schedule_{args.year}-{m:02d}.json")

        # Generate and save summary
        summary = sch.summarize_period(months_count=len(args.months))
        summary_file = sch.save_summary(summary, args.year, args.months)
        print(f"Summary saved to: {summary_file}")
        
        # Create Excel output
        from src.excel_writer import create_excel_output
        excel_dir = create_excel_output(args.year, args.months, str(period_folder))
        
        # Print summary to console
        print("\n--- SUMMARY (period) ---")
        if summary:
            headers = list(summary[0].keys())
            print("\t".join(headers))
            for row in summary:
                print("\t".join(str(row[h]) for h in headers))
        
        print(f"\nSuccessfully generated schedules for {len(args.months)} month(s)")
        print(f"Manual swapping: python -m src.manual_swap {period_folder}/schedule_*-*.json")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
