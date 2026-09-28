import _paths  # noqa: F401 — sets up sys.path before other imports

from flask import Flask, render_template, request, flash, redirect, url_for
from storage import load_json
from tracker import (
    list_students,
    get_student,
    compute_balance,
    add_student as add_student_record,
)
from report import (
    build_finance_table,
    build_performance_table,
    build_dashboard_data,
)


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
    term = "2026-T1"
    all_students = list_students()

    # Attach fee status for each student
    rows = []
    for s in all_students:
        balance = compute_balance(s["id"], term)
        rows.append({
            "id": s["id"],
            "name": s["name"],
            "class": s["class"],
            "guardian_phone": s.get("guardian_phone", ""),
            "balance": balance["balance"],
            "in_arrears": balance["in_arrears"],
        })

    # Sort by class, then name
    rows.sort(key=lambda r: (r["class"], r["name"]))

    return render_template("students.html", students=rows, term=term)


@app.route("/students/new", methods=["GET", "POST"])
def add_student_view():
    if request.method == "POST":
        student_id = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        student_class = request.form.get("class", "").strip()
        phone = request.form.get("phone", "").strip()

        # Validate
        errors = []
        if not student_id:
            errors.append("Student ID is required.")
        if not name:
            errors.append("Name is required.")
        if not student_class:
            errors.append("Class is required.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "add_student.html",
                form={"id": student_id, "name": name,
                      "class": student_class, "phone": phone},
                classes=_known_classes(),
            )

        # Save
        try:
            add_student_record(student_id, name, student_class, phone)
            flash(f"Added {name} ({student_id})", "success")
            return redirect(url_for("students"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "add_student.html",
                form={"id": student_id, "name": name,
                      "class": student_class, "phone": phone},
                classes=_known_classes(),
            )

    # GET — show the form
    return render_template(
        "add_student.html",
        form={"id": "", "name": "", "class": "", "phone": ""},
        classes=_known_classes(),
    )


def _known_classes():
    """Return a sorted list of class names already in use, for the dropdown."""
    students = list_students()
    classes = sorted({s["class"] for s in students})
    # Always offer common defaults even if no students yet
    defaults = ["Form 1", "Form 2", "Form 3", "Form 4"]
    merged = sorted(set(classes) | set(defaults))
    return merged


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