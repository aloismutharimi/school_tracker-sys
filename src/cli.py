import argparse
import sys
from tracker import add_student, record_payment, record_score, list_students
from report import print_term_report, export_term_csv
from storage import import_students_csv


def cmd_add_student(args):
    try:
        s = add_student(args.id, args.name, args.student_class, args.phone)
        print(f"✓ Added {s['name']} ({s['id']}) — {s['class']}")
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_students(args):
    students = list_students()
    if not students:
        print("No students on record.")
        return
    print(f"{'ID':<10} {'Name':<22} {'Class':<10} {'Guardian Phone'}")
    print("-" * 58)
    for s in students:
        print(f"{s['id']:<10} {s['name']:<22} {s['class']:<10} {s.get('guardian_phone', '')}")


def cmd_record_payment(args):
    try:
        record_payment(args.id, args.term, args.amount, args.method)
        print(f"✓ Payment recorded: {args.id} — {args.amount:,.0f} ({args.term})")
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_record_score(args):
    try:
        record_score(args.id, args.term, args.subject, args.score)
        print(f"✓ Score recorded: {args.id} — {args.subject} {args.score}")
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_import_students(args):
    try:
        count = import_students_csv(args.csv)
        print(f"✓ Imported {count} students from {args.csv}")
    except FileNotFoundError:
        print(f"✗ CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"✗ Missing required column: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_report(args):
    print_term_report(args.term)
    if args.export_csv:
        try:
            path = export_term_csv(args.term)
            print(f"\n✓ CSV exported → {path}")
        except ValueError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="school-tracker",
        description="School Fees & Results Tracker — CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add-student
    p = sub.add_parser("add-student", help="Add a new student")
    p.add_argument("--id", required=True, help="Student ID (e.g. STU001)")
    p.add_argument("--name", required=True, help="Full name")
    p.add_argument("--class", dest="student_class", required=True, help="Class (e.g. Form 2)")
    p.add_argument("--phone", default="", help="Guardian phone (optional)")
    p.set_defaults(func=cmd_add_student)

    # list-students
    p = sub.add_parser("list-students", help="List all students")
    p.set_defaults(func=cmd_list_students)

    # record-payment
    p = sub.add_parser("record-payment", help="Record a fee payment")
    p.add_argument("--id", required=True)
    p.add_argument("--term", required=True, help="Term (e.g. 2026-T1)")
    p.add_argument("--amount", required=True, type=float)
    p.add_argument("--method", default="cash", help="cash / mpesa / bank")
    p.set_defaults(func=cmd_record_payment)

    # record-score
    p = sub.add_parser("record-score", help="Record an exam score")
    p.add_argument("--id", required=True)
    p.add_argument("--term", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--score", required=True, type=float)
    p.set_defaults(func=cmd_record_score)

    # import-students
    p = sub.add_parser("import-students", help="Bulk import students from CSV")
    p.add_argument("--csv", required=True, help="Path to CSV file")
    p.set_defaults(func=cmd_import_students)

    # report
    p = sub.add_parser("report", help="Print term report")
    p.add_argument("--term", required=True)
    p.add_argument("--export-csv", action="store_true", help="Also export to CSV")
    p.set_defaults(func=cmd_report)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()