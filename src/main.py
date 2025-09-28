import argparse
from .scheduler import Scheduler

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--month", type=int, default=9)  # September
    args = ap.parse_args()

    sch = Scheduler()
    out = sch.assign_month(args.year, args.month)
    # also saved to data/schedule_YYYY-MM.json by Scheduler
    print(f"Generated schedule for {args.year}-{args.month:02d} and saved to data/schedule_{args.year}-{args.month:02d}.json")

if __name__ == "__main__":
    main()
