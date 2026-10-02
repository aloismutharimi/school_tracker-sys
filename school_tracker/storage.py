import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"


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