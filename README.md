# School Fees & Results Tracker 🎓

A command-line tool that stores student payments, balances, and exam scores — then generates term reports with arrears flags, class rankings, and CSV export.

Built for small schools and tutoring centers still tracking fees and grades by hand.

---

## What It Does

**Manages records**
- Add students individually or bulk-import from CSV
- Record fee payments — amount, term, method (cash / mpesa / bank)
- Record exam scores — per subject, per term
- Store everything as plain JSON

**Computes and reports**
- Fees due, paid, outstanding, and arrears status per student
- Class rank by average score — always within class, never across
- Term reports in five modes:

| Mode | Command | Output |
|---|---|---|
| Full report | `--full` (default) | All classes, fees + grades, per-class and school summaries |
| Fees only | `--fees` | Balances and arrears only |
| Grades only | `--grades` | Rankings and averages only |
| Per class | `--class "Form 2"` | One class in detail |
| Solo student | `--student STU001` | One student — fees, rank in class, subject breakdown |

- CSV export that opens directly in Excel

No database. No server. No subscription.

---

## Why It Exists

Small school administrators track fees and grades in paper ledgers or scattered Excel files. That leads to:

- Billing errors and missed arrears
- No fast way to rank students by performance
- Term reports that take hours to assemble

This tool replaces the manual process with a handful of commands. It runs anywhere Python runs, keeps data human-readable, and exports to formats admins already use.

Built as a demonstration that **practical internal tools don't need a web app** — a well-structured CLI can solve a real operational problem in under 600 lines.

---

## How to Run It

### 1. Install

```bash
git clone https://github.com/aloismutharimi/school_tracker-sys.git
cd school_tracker-sys
pip install -r requirements.txt
```
Requires Python 3.10+. Only external dependency is pandas.

### 2. Set up the fee schedule
Edit data/fees.json to match your school:

json
[
  { "class": "Form 1", "term": "2026-T1", "amount": 25000 },
  { "class": "Form 2", "term": "2026-T1", "amount": 28000 },
  { "class": "Form 3", "term": "2026-T1", "amount": 30000 }
]
### 3. Run commands
All commands run from src/:

```bash
cd src
```

Add a student:
```bash
python cli.py add-student --id STU001 --name "Wanjiku Kamau" --class "Form 2" --phone "+254712345001"
```

Bulk import from CSV:
```bash
python cli.py import-students --csv ../students-bulk.csv
```
CSV format: id, name, class, guardian_phone

Record a payment:

```bash
python cli.py record-payment --id STU001 --term 2026-T1 --amount 15000 --method mpesa
```

Record a score:
```bash
python cli.py record-score --id STU001 --term 2026-T1 --subject Mathematics --score 78
```

List all students:
```bash
python cli.py list-students
```

Report Modes
Every report runs against a term and can be scoped to a class or a single student.
```bash
# Full report — all classes, fees + grades, per-class and school summaries
python cli.py report --term 2026-T1

# Fees only
python cli.py report --term 2026-T1 --fees

# Grades only
python cli.py report --term 2026-T1 --grades

# One class
python cli.py report --term 2026-T1 --class "Form 2"

# One student — includes rank against their class and subject breakdown
python cli.py report --term 2026-T1 --student STU001

# Add --export-csv to any of the above
python cli.py report --term 2026-T1 --export-csv
```
Reports are printed to the terminal. --export-csv writes a flat, merged CSV to reports/ that opens directly in Excel.

## What the Output Looks Like

### Full report (default)

Broken down by class, with per-class summaries and a school-wide summary at the end:

```text
================================================================================
  TERM REPORT — 2026-T1
================================================================================
================================================================================
  FORM 1
================================================================================

SECTION: FEES & BALANCES

  Student Name         Class          Due      Paid   Balance  Status
  -------------------- -------- --------- --------- ---------  --------
  David Ochieng        Form 1      25,000    12,000    13,000  ⚠ ARREARS
  Fatuma Ali           Form 1      25,000    25,000         0  ✓ CLEARED
  Mercy Achieng        Form 1      25,000    25,000         0  ✓ CLEARED

SECTION: PERFORMANCE RANKING

  Rank  Student Name         Class     Average
  ----- -------------------- -------- --------
  #1    Fatuma Ali           Form 1      83.5%
  #2    Mercy Achieng        Form 1      80.0%
  #3    David Ochieng        Form 1      56.3%

SECTION: CLASS SUMMARY

  Total billed:        75,000
  Total collected:     62,000
  Outstanding:         13,000
  In arrears:          1/3 students
  Class average:         73.3%
  Top performer:       Fatuma Ali (83.5%)

... (Form 2, Form 3) ...

================================================================================
  SCHOOL SUMMARY
================================================================================

  Total billed:       278,000
  Total collected:    195,000
  Outstanding:         83,000
  In arrears:        5/10 students

================================================================================
```

### Solo student report

Shows their rank against their full class, plus a subject-by-subject breakdown:

```text
================================================================================
  STUDENT REPORT — Amina Hassan (STU003) — 2026-T1
================================================================================

SECTION: FEES & BALANCES

  Student Name         Class          Due      Paid   Balance  Status
  -------------------- -------- --------- --------- ---------  --------
  Amina Hassan         Form 2      28,000    28,000         0  ✓ CLEARED

SECTION: PERFORMANCE

  Rank in class:    #1 of 5
  Class average:    89.0%

SUBJECT BREAKDOWN

  Subject              Score  Percentage
  --------------- ----------  ----------
  Biology             86/100      86.0%
  English             88/100      88.0%
  Kiswahili           90/100      90.0%
  Mathematics         92/100      92.0%

================================================================================
```

### CSV export

Opens directly in Excel:

```csv
student_id,name,class,term,due,paid,balance,in_arrears,average,rank
STU001,Wanjiku Kamau,Form 2,2026-T1,28000.0,28000.0,0.0,False,83.5,2
STU002,Brian Otieno,Form 2,2026-T1,28000.0,15000.0,13000.0,True,69.5,4
```

---

## Architecture

```text
school_tracker-sys/
├── data/                    # JSON source of truth
│   ├── students.json
│   ├── payments.json
│   ├── scores.json
│   └── fees.json
├── reports/                 # Generated CSVs
├── src/
│   ├── storage.py           # File I/O — JSON + CSV
│   ├── tracker.py           # Business logic — students, payments, balances
│   ├── report.py            # Aggregation, ranking, formatting
│   └── cli.py               # Command-line interface
├── students-bulk.csv        # Sample bulk-import file
├── requirements.txt
└── README.md
```

**Layered design:**

| Module | Responsibility |
|---|---|
| `storage.py` | Load/save JSON, export CSV, handle locked files |
| `tracker.py` | Validation, balance computation, term fees |
| `report.py` | Aggregation, per-class ranking, terminal formatting |
| `cli.py` | Argument parsing, user feedback, exit codes |

Each layer only depends on the one below it. `cli.py` never touches files directly — it goes through `tracker` and `report`, which go through `storage`.

---

## Design Decisions

**JSON as source of truth, CSV for exchange.**
JSON handles nested records and updates cleanly. CSV is what admins already open in Excel. Both, for different purposes.

**Ranking is always within class.**
A Form 1 student is never ranked against a Form 3 student. Every class gets its own ranking that resets to `#1`.

**Solo student reports rank against the full class.**
Even when the report shows one student, their rank is computed against every classmate — not against themselves.

**Validation in `tracker.py`, not `storage.py`.**
Storage does I/O. Business rules ("no duplicate IDs", "student must exist") live in the logic layer.

**Graceful handling of locked CSVs.**
If Excel has the report open, the tool writes to a timestamped fallback file instead of crashing.

---

## Stack

`Python 3.10+` · `Pandas` · `argparse` · `pathlib` · `json` · `csv` — no database, no web server
