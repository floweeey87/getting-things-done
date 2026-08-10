#!/usr/bin/env python3
"""Determine which watchlist companies are due for a valuation rewrite.

Computes the most recent fiscal quarter whose reporting window has elapsed
(quarter end + reporting_lag_days) and compares it against the company's
last_processed_quarter. Date arithmetic lives here rather than in the run
prompt so every run derives the same quarter from the same watchlist.

Reporting a company as due means "the report should exist by now" — the run
still has to confirm via primary sources that it was actually published.

Usage:
  python3 kurssturzkompass/scripts/earnings_due.py
  python3 kurssturzkompass/scripts/earnings_due.py --today 2026-08-10
  python3 kurssturzkompass/scripts/earnings_due.py --json
"""

import argparse
import calendar
import json
import sys
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WATCHLIST = BASE / "config" / "watchlist.json"


def shift_months(year: int, month: int, delta: int) -> tuple[int, int]:
    """Shift (year, month) by delta months."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def quarter_ends(fy_end_month: int, around_year: int) -> list[tuple[str, date]]:
    """Quarter end dates for the fiscal years ending around `around_year`.

    A fiscal year is labelled by the calendar year in which it ends, matching
    how issuers label FY2026 etc. Q4 ends in fy_end_month; Q1-Q3 precede it in
    three-month steps.
    """
    out: list[tuple[str, date]] = []
    for fy in (around_year - 1, around_year, around_year + 1):
        for quarter in (1, 2, 3, 4):
            year, month = shift_months(fy, fy_end_month, -3 * (4 - quarter))
            out.append((f"Q{quarter}-{fy}", month_end(year, month)))
    out.sort(key=lambda item: item[1])
    return out


def evaluate(company: dict, today: date) -> dict:
    """Return the due-status for one company."""
    fy_end = str(company.get("fiscal_year_end", "12-31"))
    try:
        fy_end_month = int(fy_end.split("-")[0])
        if not 1 <= fy_end_month <= 12:
            raise ValueError
    except (ValueError, IndexError):
        return {
            "slug": company.get("slug"),
            "due": False,
            "error": f"invalid fiscal_year_end {fy_end!r}, expected MM-DD",
        }

    lag = int(company.get("reporting_lag_days", 45))
    candidates = [(label, end) for label, end in quarter_ends(fy_end_month, today.year) if end < today]

    expected = None
    for label, end in reversed(candidates):
        if today >= end + timedelta(days=lag):
            expected = (label, end)
            break

    result = {
        "slug": company.get("slug"),
        "name": company.get("name"),
        "ticker": company.get("ticker"),
        "isin": company.get("isin"),
        "expected_quarter": expected[0] if expected else None,
        "quarter_end": expected[1].isoformat() if expected else None,
        "expected_report_by": (expected[1] + timedelta(days=lag)).isoformat() if expected else None,
        "last_processed_quarter": company.get("last_processed_quarter"),
    }

    last = company.get("last_processed_quarter")
    # A company that reported early can already be processed past the quarter
    # the schedule expects; never walk backwards into an older quarter.
    ends = dict(quarter_ends(fy_end_month, today.year))
    last_end = ends.get(last)

    if expected is None:
        result["due"] = False
        result["reason"] = "no quarter past its reporting window yet"
    elif last == expected[0]:
        result["due"] = False
        result["reason"] = f"{expected[0]} already processed"
    elif last_end is not None and last_end >= expected[1]:
        result["due"] = False
        result["reason"] = f"{last} already processed, newer than expected {expected[0]}"
    else:
        result["due"] = True
        result["reason"] = f"{expected[0]} due since {result['expected_report_by']}"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for testing")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()

    if not WATCHLIST.exists():
        print(f"error: {WATCHLIST} not found", file=sys.stderr)
        return 1
    watchlist = json.loads(WATCHLIST.read_text(encoding="utf-8"))
    companies = [c for c in watchlist.get("companies", []) if c.get("active")]

    results = [evaluate(c, today) for c in companies]
    due = [r for r in results if r.get("due")]
    # Oldest outstanding quarter first: that company waited longest.
    due.sort(key=lambda r: r["quarter_end"])

    if args.json:
        print(json.dumps({"today": today.isoformat(), "due": due, "all": results}, ensure_ascii=False, indent=2))
        return 0

    if not companies:
        print("watchlist has no active companies - nothing to check")
        return 0

    print(f"Stichtag: {today.isoformat()}  aktive Unternehmen: {len(companies)}")
    for r in results:
        if r.get("error"):
            print(f"  [FEHLER] {r['slug']}: {r['error']}")
        else:
            mark = "FÄLLIG " if r["due"] else "       "
            print(f"  {mark}{r['slug']}: {r['reason']}")
    print()
    if due:
        print(f"Nächstes zu verarbeitendes Unternehmen: {due[0]['slug']} ({due[0]['expected_quarter']})")
    else:
        print("Kein Unternehmen fällig - Lauf ohne Änderungen beenden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
