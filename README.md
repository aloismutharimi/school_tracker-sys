# School Fees & Results Tracker 🎓

A command-line tool that stores student payments, balances, and exam scores — then generates a ranked term report with arrears flags and a CSV export.

Built for small schools and tutoring centers still tracking fees and grades by hand.

---

## What It Does

- **Manages students** — add individually or bulk-import from CSV
- **Records payments** — amount, term, method (cash / mpesa / bank)
- **Records exam scores** — per subject, per term
- **Computes balances** — fees due, paid, outstanding, arrears status
- **Ranks students** — average score and class rank per term
- **Generates reports** — formatted terminal output + CSV export for Excel

All data stored as plain JSON. No database, no server, no subscription.

---

## Why It Exists

Small school administrators track fees and grades in paper ledgers or scattered Excel files. That leads to:

- Billing errors and missed arrears
- No fast way to rank students by performance
- Term reports that take hours to assemble

This tool replaces the manual process with three commands: record, compute, report. It runs anywhere Python runs, keeps data human-readable, and exports to formats admins already use.

Built as a demonstration that **practical internal tools don't need a web app** — a well-structured CLI can solve a real operational problem in under 500 lines.

---

## Stack

`Python 3.10+` · `Pandas` · `argparse` · `pathlib` · `json` · `csv` — no database, no web server

## How to Run It

### 1. Install

```bash
git clone https://github.com/aloismutharimi/school-tracker.git
cd school-tracker
pip install -r requirements.txt


