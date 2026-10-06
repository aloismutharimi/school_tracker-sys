# School Fees & Results Tracker 🎓

A command-line tool that stores student payments, balances, and exam scores — then generates term reports with arrears flags, class rankings, and CSV/PDF export.

Built for small schools and tutoring centers still tracking fees and grades by hand.

---

## Live Demo

Try the web interface: [School Tracker](https://school-tracker-web.onrender.com)

## What It Does

**Manages records**
- Add students individually or bulk-import from CSV
- Record fee payments — amount, term, method (cash / mpesa / bank)
- Record exam scores — per subject, per term
- Store everything as plain JSON

**Computes and reports**
- Fees due, paid, outstanding, and arrears status per student
- Class rank by average score — always within class, never across
- Export to CSV and PDF
- Term reports in five modes:

| Mode | Command | Output |
|---|---|---|
| Full report | `--full` (default) | All classes, fees + grades, per-class and school summaries |
| Fees only | `--fees` | Balances and arrears only |
| Grades only | `--grades` | Rankings and averages only |
| Per class | `--class "Grade 2"` | One class in detail |
| Solo student | `--student STU001` | One student — fees, rank in class, subject breakdown |


No database. No server. No subscription.

---

## Why It Exists

Small school administrators track fees and grades in paper ledgers or scattered Excel files. That leads to:

- Billing errors and missed arrears
- No fast way to rank students by performance
- Term reports that take hours to assemble

This tool replaces the manual process with a handful of commands. It runs anywhere Python runs, keeps data human-readable, and exports to formats admins already use.

---

## Installation

### 1. Install the package

```bash
pip install git+https://github.com/aloismutharimi/school_tracker-sys.git
```

Requires **Python 3.10+**.

### 2. Data is created automatically

On first run, the tool creates a `data/` folder in your current working directory, seeded with:

- `students.json`, `payments.json`, `scores.json` — empty
- `fees.json` — a starter fee schedule (edit this to match your school)

You don't need to create any files manually. Just run any command, and the tool sets up the folder.

### 3. Set your fee schedule

Edit `data/fees.json` to match your school's fees:

```json
[
  { "class": "Grade 1", "term": "2026-T1", "amount": 500 },
  { "class": "Grade 2", "term": "2026-T1", "amount": 7000 },
  { "class": "Grade 3", "term": "2026-T1", "amount": 9000 },
  { "class": "Grade 4", "term": "2026-T1", "amount": 1100 },
  { "class": "Grade 5", "term": "2026-T1", "amount": 12000 },
  { "class": "Grade 6", "term": "2026-T1", "amount": 13000 }
]
```

### Data location

By default, data lives in `./data/` — relative to wherever you run the command.

To use a fixed location, set an environment variable:

```bash
export SCHOOL_TRACKER_DATA=/path/to/your/data      # macOS/Linux
set SCHOOL_TRACKER_DATA=D:\school_data             # Windows
```

---

## Usage

Run commands from anywhere once installed:

```bash
# Add a student
school-tracker add-student --id STU001 --name "Wanjiku Kamau" --class "Grade 2" --phone "+254712345001"

# Bulk import from CSV
school-tracker import-students --csv students-bulk.csv

# Record a payment
school-tracker record-payment --id STU001 --term 2026-T1 --amount 5000 --method mpesa

# Record a score
school-tracker record-score --id STU001 --term 2026-T1 --subject Mathematics --score 78

# List all students
school-tracker list-students
```

### Report modes

```bash
# Full report (default) — all classes, broken down per class
school-tracker report --term 2026-T1

# Fees only
school-tracker report --term 2026-T1 --fees

# Grades only
school-tracker report --term 2026-T1 --grades

# One class
school-tracker report --term 2026-T1 --class "Grade 2"

# One student
school-tracker report --term 2026-T1 --student STU001

# Export CSV
school-tracker report --term 2026-T1 --export-csv

# Export PDF
school-tracker report --term 2026-T1 --pdf
```

---

## What the Output Looks Like

### Full report (default)

Broken down by class, with per-class summaries and a school-wide summary at the end:

```text
================================================================================
  TERM REPORT — 2026-T1
================================================================================
================================================================================
  GRADE 1
================================================================================

SECTION: FEES & BALANCES

  Student Name         Class          Due      Paid   Balance  Status
  -------------------- -------- --------- --------- ---------  --------
  David Ochieng        Grade 1      25,000    12,000    13,000  ⚠ ARREARS
  Fatuma Ali           Grade 1      25,000    25,000         0  ✓ CLEARED
  Mercy Achieng        Grade 1      25,000    25,000         0  ✓ CLEARED

SECTION: PERFORMANCE RANKING

  Rank  Student Name         Class     Average
  ----- -------------------- -------- --------
  #1    Fatuma Ali           Grade 1      83.5%
  #2    Mercy Achieng        Grade 1      80.0%
  #3    David Ochieng        Grade 1      56.3%

SECTION: CLASS SUMMARY

  Total billed:        75,000
  Total collected:     62,000
  Outstanding:         13,000
  In arrears:          1/3 students
  Class average:         73.3%
  Top performer:       Fatuma Ali (83.5%)

... (Grade 2, Grade 3, ...) ...

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
  Amina Hassan         Grade 2      28,000    28,000         0  ✓ CLEARED

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
STU001,Wanjiku Kamau,Grade 2,2026-T1,7000.0,7000.0,0.0,False,83.5,2
STU002,Brian Otieno,Grade 2,2026-T1,7000.0,3000.0,4000.0,True,69.5,4
```

---

## Architecture

```text
school_tracker-sys/
├── school_tracker/          # the Python package
│   ├── __init__.py
│   ├── storage.py           # File I/O — JSON + CSV
│   ├── tracker.py           # Business logic — students, payments, balances
│   ├── report.py            # Aggregation, ranking, formatting
│   ├── pdf_report.py        # PDF generation via ReportLab
│   ├── cli.py               # Command-line interface
│   └── data_seed/           # Starter data templates (shipped with package)
│       ├── students.json
│       ├── payments.json
│       ├── scores.json
│       └── fees.json
├── data/                    # Local runtime data (ignored by Git)
├── reports/                 # Generated CSVs and PDFs
├── pyproject.toml
└── README.md
```

**Layered design:**

| Module | Responsibility |
|---|---|
| `storage.py` | Load/save JSON, export CSV, bootstrap data on first run |
| `tracker.py` | Validation, balance computation, term fees |
| `report.py` | Aggregation, per-class ranking, terminal formatting |
| `pdf_report.py` | Renders reports as styled A4 PDFs |
| `cli.py` | Argument parsing, user feedback, exit codes |

---

## Related Projects

- **[school_tracker-web](https://github.com/aloismutharimi/school_tracker-web)** — A Flask web interface built on top of this CLI. Same logic, browser-based for non-technical users.

---

## Stack

`Python 3.10+` · `Pandas` · `ReportLab` · `argparse` · `pathlib` · `json` · `csv`

---

## License

MIT