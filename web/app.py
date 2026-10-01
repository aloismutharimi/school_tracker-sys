import _paths  # noqa: F401 — sets up sys.path before other imports

from flask import Flask, render_template, request, flash, redirect, url_for
from storage import load_json
from tracker import (
    list_students,
    get_student,
    compute_balance,
    add_student as add_student_record,
    record_payment as record_payment_record,
    record_score as record_score_record,
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
    defaults = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"]
    merged = sorted(set(classes) | set(defaults))
    return merged


@app.route("/payments/new", methods=["GET", "POST"])
def add_payment():
    term = "2026-T1"
    all_students = sorted(list_students(), key=lambda s: (s["class"], s["name"]))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        amount = request.form.get("amount", "").strip()
        method = request.form.get("method", "cash").strip()
        payment_date = request.form.get("date", "").strip() or None

        errors = []
        if not student_id:
            errors.append("Please select a student.")
        if not amount:
            errors.append("Amount is required.")
        else:
            try:
                amount_val = float(amount)
                if amount_val <= 0:
                    errors.append("Amount must be greater than zero.")
            except ValueError:
                errors.append("Amount must be a number.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "add_payment.html",
                students=all_students,
                form={"student_id": student_id, "amount": amount,
                      "method": method, "date": payment_date or ""},
                recent=_recent_payments(term),
                term=term,
            )

        try:
            record_payment_record(
                student_id, term, float(amount), method, payment_date
            )
            student = get_student(student_id)
            flash(f"Recorded {float(amount):,.0f} from {student['name']}",
                  "success")
            # Stay on the form — clear the amount so they can enter the next one
            return render_template(
                "add_payment.html",
                students=all_students,
                form={"student_id": "", "amount": "", "method": "cash", "date": ""},
                recent=_recent_payments(term),
                term=term,
            )
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "add_payment.html",
                students=all_students,
                form={"student_id": student_id, "amount": amount,
                      "method": method, "date": payment_date or ""},
                recent=_recent_payments(term),
                term=term,
            )

    # GET
    return render_template(
        "add_payment.html",
        students=all_students,
        form={"student_id": "", "amount": "", "method": "cash", "date": ""},
        recent=_recent_payments(term),
        term=term,
    )


@app.route("/scores/new", methods=["GET", "POST"])
def add_score():
    term = "2026-T1"
    all_students = sorted(list_students(), key=lambda s: (s["class"], s["name"]))
    subjects = ["Mathematics", "English", "Kiswahili", "Science", "Social Studies", "CRE"]

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        subject = request.form.get("subject", "").strip()
        score = request.form.get("score", "").strip()

        errors = []
        if not student_id:
            errors.append("Please select a student.")
        if not subject:
            errors.append("Subject is required.")
        if not score:
            errors.append("Score is required.")
        else:
            try:
                score_val = float(score)
                if score_val < 0 or score_val > 100:
                    errors.append("Score must be between 0 and 100.")
            except ValueError:
                errors.append("Score must be a number.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "add_score.html",
                students=all_students,
                subjects=subjects,
                form={"student_id": student_id, "subject": subject, "score": score},
                recent=_recent_scores(term),
                term=term,
            )

        try:
            record_score_record(student_id, term, subject, float(score))
            student = get_student(student_id)
            flash(f"Recorded {subject} {float(score):.0f} for {student['name']}",
                  "success")
            return render_template(
                "add_score.html",
                students=all_students,
                subjects=subjects,
                form={"student_id": "", "subject": "", "score": ""},
                recent=_recent_scores(term),
                term=term,
            )
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "add_score.html",
                students=all_students,
                subjects=subjects,
                form={"student_id": student_id, "subject": subject, "score": score},
                recent=_recent_scores(term),
                term=term,
            )

    # GET
    return render_template(
        "add_score.html",
        students=all_students,
        subjects=subjects,
        form={"student_id": "", "subject": "", "score": ""},
        recent=_recent_scores(term),
        term=term,
    )


def _recent_payments(term, limit=5):
    """Return the last N payments for the given term, newest first."""
    payments = load_json("payments.json")
    filtered = [p for p in payments if p["term"] == term]
    filtered = filtered[-limit:]
    filtered.reverse()
    students = {s["id"]: s for s in list_students()}
    return [
        {
            "student_name": students.get(p["student_id"], {}).get("name", "?"),
            "amount": p["amount"],
            "method": p["method"],
            "date": p["date"],
        }
        for p in filtered
    ]


def _recent_scores(term, limit=5):
    """Return the last N scores for the given term, newest first."""
    scores = load_json("scores.json")
    filtered = [s for s in scores if s["term"] == term]
    filtered = filtered[-limit:]
    filtered.reverse()
    students = {s["id"]: s for s in list_students()}
    return [
        {
            "student_name": students.get(s["student_id"], {}).get("name", "?"),
            "subject": s["subject"],
            "score": s["score"],
            "out_of": s["out_of"],
        }
        for s in filtered
    ]

@app.route("/reports", methods=["GET", "POST"])
def reports():
    term = "2026-T1"
    all_students = list_students()

    # Available filters for the dropdowns
    classes = sorted({s["class"] for s in all_students})
    students_sorted = sorted(all_students, key=lambda s: (s["class"], s["name"]))

    # Default form state
    form = {
        "mode": "full",
        "class_filter": "",
        "student_id": "",
    }

    report_data = None

    if request.method == "POST":
        form["mode"] = request.form.get("mode", "full")
        form["class_filter"] = request.form.get("class_filter", "").strip()
        form["student_id"] = request.form.get("student_id", "").strip()

        # Determine which students the report covers
        if form["student_id"]:
            target_students = [s for s in all_students if s["id"] == form["student_id"]]
        elif form["class_filter"]:
            target_students = [s for s in all_students if s["class"] == form["class_filter"]]
        else:
            target_students = all_students

        if not target_students:
            flash("No students match the given filters.", "error")
        else:
            report_data = _build_report_view(
                term, form["mode"], target_students,
                student_id=form["student_id"] or None,
                class_filter=form["class_filter"] or None,
            )

    return render_template(
        "reports.html",
        term=term,
        classes=classes,
        students=students_sorted,
        form=form,
        report=report_data,
    )

def _build_report_view(term, mode, students, student_id=None, class_filter=None):
    """
    Build the data structure the reports template renders.
    Uses the same builders as the CLI so numbers always match.
    """
    from report import (
        build_finance_table,
        build_performance_table,
        build_student_scores,
        get_student_rank,
    )

    result = {
        "mode": mode,
        "student_id": student_id,
        "class_filter": class_filter,
        "fees": None,
        "performance": None,
        "scores": None,
        "student_meta": None,
        "title": "Report",
    }

    # Solo student report
    if student_id:
        s = get_student(student_id)
        result["student_meta"] = {"name": s["name"], "class": s["class"], "id": s["id"]}
        result["title"] = f"Student Report — {s['name']}"

        if mode in ("fees", "full"):
            df = build_finance_table(term, students)
            if not df.empty:
                result["fees"] = df.to_dict(orient="records")

        if mode in ("grades", "full"):
            rank, total = get_student_rank(student_id, term)
            result["rank"] = rank
            result["rank_total"] = total

            perf_df = build_performance_table(term, students)
            if not perf_df.empty:
                result["performance"] = perf_df.to_dict(orient="records")

            scores_df = build_student_scores(student_id, term)
            if not scores_df.empty:
                result["scores"] = scores_df.to_dict(orient="records")

        return result

    # Class or full report
    if mode in ("fees", "full"):
        df = build_finance_table(term, students)
        if not df.empty:
            result["fees"] = df.to_dict(orient="records")

    if mode in ("grades", "full"):
        df = build_performance_table(term, students)
        if not df.empty:
            result["performance"] = df.to_dict(orient="records")

    # Title reflects scope
    if class_filter:
        result["title"] = f"Class Report — {class_filter}"
    else:
        result["title"] = "Full School Report"

    return result

@app.route("/health")
def health():
    return {"status": "ok", "students": len(list_students())}


if __name__ == "__main__":
    app.run(debug=True, port=5000)