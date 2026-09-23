import pandas as pd
from storage import load_json, export_csv
from tracker import compute_balance, get_student


def _filter_students(students, class_filter=None, student_id=None):
    """Apply optional filters to a student list."""
    if student_id:
        return [s for s in students if s["id"] == student_id]
    if class_filter:
        return [s for s in students if s["class"] == class_filter]
    return students


def build_finance_table(term, students=None):
    """Return a DataFrame of balances for the given students."""
    students = students or load_json("students.json")
    rows = [compute_balance(s["id"], term) for s in students]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.sort_values("balance", ascending=False)


def build_performance_table(term, students=None):
    """
    Return a DataFrame of average scores and class rank.
    Ranking is always computed within each class, never across classes.
    """
    students = students or load_json("students.json")
    ids = {s["id"] for s in students}

    scores = load_json("scores.json")
    df = pd.DataFrame(scores)
    if df.empty:
        return pd.DataFrame()

    df = df[(df["term"] == term) & (df["student_id"].isin(ids))]
    if df.empty:
        return pd.DataFrame()

    df["pct"] = (df["score"] / df["out_of"]) * 100
    avg = df.groupby("student_id")["pct"].mean().reset_index()
    avg.columns = ["student_id", "average"]

    # Attach names and classes
    names = {s["id"]: s for s in students}
    avg["name"] = avg["student_id"].map(lambda i: names.get(i, {}).get("name", "?"))
    avg["class"] = avg["student_id"].map(lambda i: names.get(i, {}).get("class", "?"))

    # Rank within each class (not globally)
    avg["rank"] = (avg.groupby("class")["average"]
                      .rank(ascending=False, method="min")
                      .astype(int))

    return avg.sort_values(["class", "rank"]).reset_index(drop=True)


def build_student_scores(student_id, term):
    """Return a DataFrame of subject-by-subject scores for one student."""
    scores = load_json("scores.json")
    df = pd.DataFrame(scores)
    if df.empty:
        return pd.DataFrame()

    df = df[(df["term"] == term) & (df["student_id"] == student_id)]
    if df.empty:
        return pd.DataFrame()

    df["pct"] = (df["score"] / df["out_of"]) * 100
    return df[["subject", "score", "out_of", "pct"]].sort_values("subject")

def get_student_rank(student_id, term):
    """
    Return (rank, total_in_class) for a student, computed against their full class.
    Works correctly even when the student is the only one in the filtered set.
    """
    student = get_student(student_id)
    if not student:
        return None, None

    # Get the full class, regardless of any current filter
    all_students = load_json("students.json")
    classmates = [s for s in all_students if s["class"] == student["class"]]

    # Build the performance table for the full class
    class_perf = build_performance_table(term, classmates)
    if class_perf.empty:
        return None, len(classmates)

    match = class_perf[class_perf["student_id"] == student_id]
    if match.empty:
        return None, len(classmates)

    rank = int(match.iloc[0]["rank"])
    return rank, len(class_perf)

def _print_fees_section(term, students, W):
    print("\nSECTION: FEES & BALANCES\n")
    finance = build_finance_table(term, students)
    if finance.empty:
        print("  No students on record.")
        return finance

    # Column headers
    print(f"  {'Name':<20} {'Class':<8} "
          f"{'Due':>6} {'Paid':>10} {'Balance':>12}  {'Status'}")
    print(f"  {"-" * 70}")

    for _, row in finance.iterrows():
        status = "⚠ ARREARS" if row["in_arrears"] else "✓ CLEARED"
        print(f"  {row['name']:<20} {row['class']:<8} "
              f"{row['due']:>9,.0f} {row['paid']:>9,.0f} "
              f"{row['balance']:>9,.0f}  {status}")

    return finance


def _print_grades_section(term, students, W):
    print("\nSECTION: PERFORMANCE RANKING\n")
    perf = build_performance_table(term, students)
    if perf.empty:
        print("  No scores recorded for this term.")
        return perf

    print(f"  {'Rank':<5} {'Name':<20} {'Class':<8} {'Average':>8}")
    print(f"  {'-' * 44}")

    for _, row in perf.iterrows():
        print(f"  #{row['rank']:<4} {row['name']:<20} "
              f"{row['class']:<8} {row['average']:>7.1f}%")

    return perf


def _print_summary(finance, perf, W):
    print("\nSECTION: SUMMARY\n")
    if not finance.empty:
        total_due = finance["due"].sum()
        total_paid = finance["paid"].sum()
        total_bal = finance["balance"].sum()
        arrears = int(finance["in_arrears"].sum())
        print(f"  Total billed:    {total_due:>10,.0f}")
        print(f"  Total collected: {total_paid:>10,.0f}")
        print(f"  Outstanding:     {total_bal:>10,.0f}")
        print(f"  In arrears:      {arrears}/{len(finance)} students")
    if not perf.empty:
        print(f"  Class average:   {perf['average'].mean():>10.1f}%")
        print(f"  Top performer:   {perf.iloc[0]['name']} ({perf.iloc[0]['average']:.1f}%)")

def _print_class_summary(finance, perf, W):
    """Per-class summary — includes average and top performer."""
    print("\nSECTION: CLASS SUMMARY\n")
    if not finance.empty:
        total_due = finance["due"].sum()
        total_paid = finance["paid"].sum()
        total_bal = finance["balance"].sum()
        arrears = int(finance["in_arrears"].sum())
        print(f"  Total billed:    {total_due:>10,.0f}")
        print(f"  Total collected: {total_paid:>10,.0f}")
        print(f"  Outstanding:     {total_bal:>10,.0f}")
        print(f"  In arrears:      {arrears}/{len(finance)} students")
    if not perf.empty:
        print(f"  Class average:   {perf['average'].mean():>10.1f}%")
        top = perf.iloc[0]
        print(f"  Top performer:   {top['name']} ({top['average']:.1f}%)")


def _print_school_summary(finance, W):
    """Whole-school summary — fees only, no averages or top performer."""
    print("\n" + "=" * W)
    print("  SCHOOL SUMMARY")
    print("=" * W + "\n")
    if finance.empty:
        print("  No data available.")
        return
    total_due = finance["due"].sum()
    total_paid = finance["paid"].sum()
    total_bal = finance["balance"].sum()
    arrears = int(finance["in_arrears"].sum())
    print(f"  Total billed:    {total_due:>10,.0f}")
    print(f"  Total collected: {total_paid:>10,.0f}")
    print(f"  Outstanding:     {total_bal:>10,.0f}")
    print(f"  In arrears:      {arrears}/{len(finance)} students")

def _group_by_class(students):
    """Return {class_name: [students]} sorted alphabetically."""
    groups = {}
    for s in students:
        groups.setdefault(s["class"], []).append(s)
    return dict(sorted(groups.items()))

def print_term_report(term, mode="full", class_filter=None, student_id=None):
    students = load_json("students.json")
    students = _filter_students(students, class_filter, student_id)

    if not students:
        print("No students match the given filters.")
        return

    W = 76
    title = f"TERM REPORT — {term}"
    if student_id:
        s = get_student(student_id)
        title = f"STUDENT REPORT — {s['name']} ({student_id}) — {term}"
    elif class_filter:
        title = f"CLASS REPORT — {class_filter} — {term}"

    print("=" * W)
    print(f"  {title}")
    print("=" * W)

    # ---- Solo student ----
    if student_id:
        finance = pd.DataFrame()
        if mode in ("fees", "full"):
            finance = _print_fees_section(term, students, W)
        if mode in ("grades", "full"):
            rank, total = get_student_rank(student_id, term)
            perf = build_performance_table(term, students)
            print("\nSECTION: PERFORMANCE\n")
            if perf.empty:
                print("  No scores recorded for this term.")
            else:
                avg = perf.iloc[0]["average"]
                if rank:
                    print(f"  Rank in class:    #{rank} of {total}")
                print(f"  Class average:    {avg:.1f}%")

            print("\nSUBJECT BREAKDOWN\n")
            subjects = build_student_scores(student_id, term)
            if subjects.empty:
                print("  No scores recorded.")
            else:
                print(f"  {'Subject':<15} {'Score':>10}  {'Percentage':>10}")
                print(f"  {'-' * 15} {'-' * 10}  {'-' * 10}")
                for _, row in subjects.iterrows():
                    print(f"  {row['subject']:<15} {row['score']:>4.0f}/{row['out_of']:<4.0f}"
                          f"  {row['pct']:>9.1f}%")
        print("\n" + "=" * W)
        return

    # ---- Class-only report ----
    if class_filter:
        finance = pd.DataFrame()
        perf = pd.DataFrame()
        if mode in ("fees", "full"):
            finance = _print_fees_section(term, students, W)
        if mode in ("grades", "full"):
            perf = _print_grades_section(term, students, W)
        if mode == "full":
            _print_class_summary(finance, perf, W)
        print("\n" + "=" * W)
        return

    # ---- Whole-school report, broken down by class ----
    groups = _group_by_class(students)
    all_finance = []

    for class_name, class_students in groups.items():
        print(f"\n{'=' * W}")
        print(f"  {class_name.upper()}")
        print(f"{'=' * W}")

        finance = pd.DataFrame()
        perf = pd.DataFrame()

        if mode in ("fees", "full"):
            finance = _print_fees_section(term, class_students, W)
        if mode in ("grades", "full"):
            perf = _print_grades_section(term, class_students, W)
        if mode == "full":
            _print_class_summary(finance, perf, W)

        if not finance.empty:
            all_finance.append(finance)

    # School-wide summary (fees only)
    if mode == "full" and all_finance:
        combined = pd.concat(all_finance, ignore_index=True)
        _print_school_summary(combined, W)

    print("\n" + "=" * W)


def export_term_csv(term, mode="full", class_filter=None, student_id=None):
    """Export the term report as CSV. Filename reflects filters."""
    students = load_json("students.json")
    students = _filter_students(students, class_filter, student_id)
    if not students:
        raise ValueError("No students match the given filters.")

    finance = build_finance_table(term, students)
    perf = build_performance_table(term, students)

    if finance.empty and perf.empty:
        raise ValueError(f"No data to export for {term}")

    if finance.empty:
        merged = perf.copy()
    elif perf.empty:
        merged = finance.copy()
        merged["average"] = None
        merged["rank"] = None
    else:
        merged = finance.merge(
            perf[["student_id", "average", "rank"]],
            on="student_id", how="left"
        )

    # Build a filename that reflects the report scope
    parts = [term]
    if student_id:
        parts.append(student_id)
    elif class_filter:
        parts.append(class_filter.replace(" ", "-"))
    parts.append(mode)
    filename = "-".join(parts) + ".csv"

    rows = merged.to_dict(orient="records")
    fieldnames = [c for c in ["student_id", "name", "class", "term",
                               "due", "paid", "balance", "in_arrears",
                               "average", "rank"] if c in merged.columns]

    return export_csv(filename, rows, fieldnames)