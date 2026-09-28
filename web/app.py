import sys
from pathlib import Path

# Make src/ importable from the web layer
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from flask import Flask, render_template

# Import existing modules — this proves the web layer can reach the CLI logic
from storage import load_json
from tracker import list_students
from report import build_finance_table, build_performance_table


app = Flask(__name__)


@app.route("/")
def home():
    students = list_students()
    return render_template("home.html", student_count=len(students))


@app.route("/health")
def health():
    """Quick check that the app can read data."""
    students = list_students()
    return {
        "status": "ok",
        "students": len(students),
        "src_path": str(SRC_DIR),
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)