import _paths  # noqa: F401 — sets up sys.path before other imports

from flask import Flask, render_template, request, flash, redirect, url_for
from storage import load_json
from tracker import list_students, get_student
from report import build_finance_table, build_performance_table, build_dashboard_data


app = Flask(__name__)
app.secret_key = "dev-key-change-in-production"


@app.context_processor
def inject_globals():
    return {"current_term": "2026-T1"}


@app.route("/")
def home():
    term = "2026-T1"  # will become dynamic later
    from report import build_dashboard_data
    data = build_dashboard_data(term)
    return render_template("home.html", term=term, **data)


# --- Placeholders for Step 3 onward ---
# These routes exist so the nav doesn't 404. Each will be built in later steps.

@app.route("/students")
def students():
    return render_template("placeholder.html", page="Students")


@app.route("/students/new")
def add_student():
    return render_template("placeholder.html", page="Add Student")


@app.route("/payments/new")
def add_payment():
    return render_template("placeholder.html", page="Record Payment")


@app.route("/scores/new")
def add_score():
    return render_template("placeholder.html", page="Record Score")


@app.route("/reports")
def reports():
    return render_template("placeholder.html", page="Reports")


@app.route("/health")
def health():
    return {"status": "ok", "students": len(list_students())}


if __name__ == "__main__":
    app.run(debug=True, port=5000)