# on_duty_scheduler/src/main.py
import argparse, json
from src.scheduler import Scheduler

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", type=int, nargs="+", default=[9], help="List of months, e.g. 7 8 9")
    args = ap.parse_args()

    sch = Scheduler()
    sch.assign_months(args.year, args.months)

    for m in args.months:
        print(f"Saved data/schedule_{args.year}-{m:02d}.json")

    summary = sch.summarize_period(months_count=len(args.months))
    print("\n--- SUMMARY (period) ---")
    headers = list(summary[0].keys())
    print("\t".join(headers))
    for row in summary:
        print("\t".join(str(row[h]) for h in headers))

if __name__ == "__main__":
    main()
