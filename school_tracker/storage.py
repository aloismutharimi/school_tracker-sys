import json
import csv
import os
from pathlib import Path

# Package location
PACKAGE_DIR = Path(__file__).parent
SEED_DIR = PACKAGE_DIR / "data_seed"

# Where the app reads/writes data.
# Priority:
# 1. SCHOOL_TRACKER_DATA environment variable (explicit override)
# 2. ./data in the current working directory (predictable for CLI use)
_default_data = Path.cwd() / "data"
DATA_DIR = Path(os.environ.get("SCHOOL_TRACKER_DATA", _default_data))
REPORTS_DIR = DATA_DIR / "reports"


def _ensure_data_files():
    """Create data files from seed templates if missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SEED_DIR.exists():
        return
    for seed_file in SEED_DIR.glob("*.json"):
        target = DATA_DIR / seed_file.name
        if not target.exists():
            target.write_text(seed_file.read_text())


# Bootstrap on import
_ensure_data_files()


def load_json(filename):
    """Load a JSON file from data/. Returns [] if missing."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    if path.stat().st_size == 0:
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_json(filename, data):
    """Save data to a JSON file in data/."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def export_csv(filename, rows, fieldnames):
    """Export a list of dicts to CSV in reports/. Returns the path."""
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename

    # If the file exists and is locked, write to a timestamped fallback
    if path.exists():
        try:
            # Test writability by opening in append mode
            with open(path, "a"):
                pass
        except PermissionError:
            from datetime import datetime
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            stem = path.stem
            path = path.with_name(f"{stem}-{stamp}.csv")
            print(f"⚠ Original file is locked (open in Excel?).")
            print(f"  Writing to {path.name} instead.")

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def import_students_csv(csv_path):
    """Bulk-add students from CSV. Skips duplicate IDs. Returns count added."""
    students = load_json("students.json")
    existing_ids = {s["id"] for s in students}
    added = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] in existing_ids:
                continue
            students.append({
                "id": row["id"],
                "name": row["name"],
                "class": row["class"],
                "guardian_phone": row.get("guardian_phone", ""),
            })
            added += 1

    save_json("students.json", students)
    return added