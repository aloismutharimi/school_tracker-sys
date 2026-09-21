from datetime import date
from storage import load_json, save_json


def add_student(student_id, name, student_class, guardian_phone=""):
    """Add a new student. Raises if ID already exists."""
    students = load_json("students.json")
    if any(s["id"] == student_id for s in students):
        raise ValueError(f"Student {student_id} already exists")

    students.append({
        "id": student_id,
        "name": name,
        "class": student_class,
        "guardian_phone": guardian_phone,
    })
    save_json("students.json", students)
    return students[-1]


def get_student(student_id):
    """Return a student dict, or None if not found."""
    students = load_json("students.json")
    return next((s for s in students if s["id"] == student_id), None)


def list_students():
    """Return all students."""
    return load_json("students.json")


def record_payment(student_id, term, amount, method="cash", payment_date=None):
    """Record a fee payment for a student."""
    if not get_student(student_id):
        raise ValueError(f"Unknown student {student_id}")

    payments = load_json("payments.json")
    payments.append({
        "student_id": student_id,
        "term": term,
        "amount": float(amount),
        "date": payment_date or date.today().isoformat(),
        "method": method,
    })
    save_json("payments.json", payments)


def record_score(student_id, term, subject, score, out_of=100):
    """Record an exam score for a student."""
    if not get_student(student_id):
        raise ValueError(f"Unknown student {student_id}")

    scores = load_json("scores.json")
    scores.append({
        "student_id": student_id,
        "term": term,
        "subject": subject,
        "score": float(score),
        "out_of": float(out_of),
    })
    save_json("scores.json", scores)


def get_term_fee(student_class, term):
    """Look up the fee due for a class in a term. Returns 0 if not found."""
    fees = load_json("fees.json")
    for entry in fees:
        if entry["class"] == student_class and entry["term"] == term:
            return float(entry["amount"])
    return 0.0


def compute_balance(student_id, term):
    """Return fee due, paid, balance, and arrears status for a student."""
    student = get_student(student_id)
    if not student:
        raise ValueError(f"Unknown student {student_id}")

    payments = load_json("payments.json")
    due = get_term_fee(student["class"], term)
    paid = sum(
        p["amount"] for p in payments
        if p["student_id"] == student_id and p["term"] == term
    )

    return {
        "student_id": student_id,
        "name": student["name"],
        "class": student["class"],
        "term": term,
        "due": due,
        "paid": paid,
        "balance": due - paid,
        "in_arrears": paid < due,
    }