import pandas as pd
from storage import load_json, export_csv
from tracker import compute_balance


def build_finance_table(term):
    """Return a DataFrame of balances for all students in a term."""
    students = load_json("students.json")
    rows = [compute_balance(s["id"], term) for s in students]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.sort_values("balance", ascending=False)


def build_performance_table(term):
    """Return a DataFrame of average scores and class rank for a term."""
    students = load_json("students.json")
    scores = load_json("scores.json")

    df = pd.DataFrame(scores)
    if df.empty:
        return pd.DataFrame()

    df = df[df["term"] == term]
    if df.empty:
        return pd.DataFrame()

    # Convert each score to a percentage
    df["pct"] = (df["score"] / df["out_of"]) * 100

    # Average per student
    avg = df.groupby("student_id")["pct"].mean().reset_index()
    avg.columns = ["student_id", "average"]

    # Rank: 1 = highest average
    avg["rank"] = avg["average"].rank(ascending=False, method="min").astype(int)

    # Attach names and classes
    names = {s["id"]: s for s in students}
    avg["name"] = avg["student_id"].map(lambda i: names.get(i, {}).get("name", "?"))
    avg["class"] = avg["student_id"].map(lambda i: names.get(i, {}).get("class", "?"))

    return avg.sort_values("rank").reset_index(drop=True)


def print_term_report(term):
    """Print a formatted term report to the terminal."""
    W = 64
    print("=" * W)
    print(f"  TERM REPORT — {term}")
    print("=" * W)

    # Section 1 — Fees
    print("\nSECTION 1: FEES & BALANCES\n")
    finance = build_finance_table(term)
    if finance.empty:
        print("  No students on record.")
    else:
        for _, row in finance.iterrows():
            flag = "  ⚠ ARREARS" if row["in_arrears"] else ""
            print(f"  {row['name']:<20} {row['class']:<8} "
                  f"Due {row['due']:>8,.0f}  Paid {row['paid']:>8,.0f}  "
                  f"Bal {row['balance']:>8,.0f}{flag}")

    # Section 2 — Performance
    print("\nSECTION 2: PERFORMANCE RANKING\n")
    perf = build_performance_table(term)
    if perf.empty:
        print("  No scores recorded for this term.")
    else:
        for _, row in perf.iterrows():
            print(f"  #{row['rank']:<3} {row['name']:<20} "
                  f"{row['class']:<8} Avg {row['average']:.1f}%")

    # Section 3 — Summary
    print("\nSECTION 3: SUMMARY\n")
    if not finance.empty:
        total_due = finance["due"].sum()
        total_paid = finance["paid"].sum()
        total_bal = finance["balance"].sum()
        arrears_count = int(finance["in_arrears"].sum())
        print(f"  Total billed:    {total_due:>10,.0f}")
        print(f"  Total collected: {total_paid:>10,.0f}")
        print(f"  Outstanding:     {total_bal:>10,.0f}")
        print(f"  In arrears:      {arrears_count}/{len(finance)} students")

    print("\n" + "=" * W)


def export_term_csv(term):
    """Export the term report as a CSV in reports/. Returns the path."""
    finance = build_finance_table(term)
    perf = build_performance_table(term)

    if finance.empty:
        raise ValueError(f"No data to export for {term}")

    if perf.empty:
        merged = finance.copy()
        merged["average"] = None
        merged["rank"] = None
    else:
        merged = finance.merge(
            perf[["student_id", "average", "rank"]],
            on="student_id", how="left"
        )

    rows = merged.to_dict(orient="records")
    path = export_csv(
        f"{term}-term-report.csv",
        rows,
        fieldnames=[
            "student_id", "name", "class", "term",
            "due", "paid", "balance", "in_arrears",
            "average", "rank",
        ],
    )
    return path