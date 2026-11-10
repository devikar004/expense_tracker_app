import os
import sqlite3
from datetime import date
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")

CATEGORIES = {
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Other",
}

app = Flask(__name__, static_folder="static", static_url_path="")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)"
    )
    conn.commit()
    conn.close()


def expense_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "amount": row["amount"],
        "category": row["category"],
        "date": row["expense_date"],
        "note": row["note"] or "",
        "created_at": row["created_at"],
    }


def validate_expense(data, partial=False):
    errors = {}

    if "title" in data or not partial:
        title = str(data.get("title") or "").strip()
        if not title:
            errors["title"] = "Title is required."
        elif len(title) > 200:
            errors["title"] = "Title must be 200 characters or fewer."

    if "amount" in data or not partial:
        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            errors["amount"] = "Amount must be a number."
        else:
            if amount <= 0:
                errors["amount"] = "Amount must be greater than zero."
            elif amount > 1_000_000_000:
                errors["amount"] = "Amount is too large."

    if "category" in data or not partial:
        category = str(data.get("category") or "").strip()
        if category not in CATEGORIES:
            errors["category"] = "Category is invalid."

    if "date" in data or not partial:
        expense_date = str(data.get("date") or "").strip()
        try:
            date.fromisoformat(expense_date)
        except ValueError:
            errors["date"] = "Date must be in YYYY-MM-DD format."

    if errors:
        return None, errors

    return {
        "title": str(data.get("title")).strip(),
        "amount": round(float(data.get("amount")), 2),
        "category": str(data.get("category")).strip(),
        "date": str(data.get("date")).strip(),
        "note": str(data.get("note") or "").strip(),
    }, None


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/expenses")
def list_expenses():
    category = request.args.get("category", "").strip()
    date_from = request.args.get("from", "").strip()
    date_to = request.args.get("to", "").strip()
    title_query = request.args.get("q", "").strip()

    filters = []
    params = []

    if category:
        if category not in CATEGORIES:
            return jsonify({"error": "Invalid category filter."}), 400
        filters.append("category = ?")
        params.append(category)

    if date_from:
        try:
            date.fromisoformat(date_from)
        except ValueError:
            return jsonify({"error": "Invalid 'from' date. Use YYYY-MM-DD."}), 400
        filters.append("expense_date >= ?")
        params.append(date_from)

    if date_to:
        try:
            date.fromisoformat(date_to)
        except ValueError:
            return jsonify({"error": "Invalid 'to' date. Use YYYY-MM-DD."}), 400
        filters.append("expense_date <= ?")
        params.append(date_to)

    if date_from and date_to and date_from > date_to:
        return jsonify({"error": "'From' date cannot be after 'to' date."}), 400

    if title_query:
        filters.append("LOWER(title) LIKE ?")
        params.append(f"%{title_query.lower()}%")

    sql = "SELECT * FROM expenses"
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY expense_date DESC, id DESC"

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return jsonify({"expenses": [expense_to_dict(row) for row in rows]})


@app.post("/api/expenses")
def create_expense():
    data = request.get_json(silent=True) or {}
    cleaned, errors = validate_expense(data)

    if errors:
        return jsonify({"errors": errors}), 400

    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO expenses (title, amount, category, expense_date, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            cleaned["title"],
            cleaned["amount"],
            cleaned["category"],
            cleaned["date"],
            cleaned["note"],
        ),
    )
    expense_id = cursor.lastrowid
    conn.commit()

    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    conn.close()

    return jsonify({"expense": expense_to_dict(row)}), 201


@app.put("/api/expenses/<int:expense_id>")
def update_expense(expense_id):
    data = request.get_json(silent=True) or {}
    cleaned, errors = validate_expense(data, partial=True)

    if errors:
        return jsonify({"errors": errors}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if not existing:
        conn.close()
        return jsonify({"error": "Expense not found."}), 404

    updated = {
        "title": cleaned.get("title", existing["title"]),
        "amount": cleaned.get("amount", existing["amount"]),
        "category": cleaned.get("category", existing["category"]),
        "date": cleaned.get("date", existing["expense_date"]),
        "note": cleaned.get("note", existing["note"] or ""),
    }

    conn.execute(
        """
        UPDATE expenses
        SET title = ?, amount = ?, category = ?, expense_date = ?, note = ?
        WHERE id = ?
        """,
        (
            updated["title"],
            updated["amount"],
            updated["category"],
            updated["date"],
            updated["note"],
            expense_id,
        ),
    )
    conn.commit()

    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    conn.close()

    return jsonify({"expense": expense_to_dict(row)})


@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id):
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM expenses WHERE id = ?", (expense_id,)
    )
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Expense not found."}), 404

    return jsonify({"message": "Expense deleted."})


@app.get("/api/summary")
def monthly_summary():
    month = request.args.get("month", date.today().strftime("%Y-%m")).strip()

    try:
        year, month_number = map(int, month.split("-"))
        if not 1 <= month_number <= 12:
            raise ValueError
    except (ValueError, AttributeError):
        return jsonify({"error": "Month must be in YYYY-MM format."}), 400

    start = f"{year:04d}-{month_number:02d}-01"
    if month_number == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month_number + 1
    end = f"{next_year:04d}-{next_month:02d}-01"

    conn = get_db()

    total_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
        FROM expenses
        WHERE expense_date >= ? AND expense_date < ?
        """,
        (start, end),
    ).fetchone()

    category_rows = conn.execute(
        """
        SELECT category, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
        FROM expenses
        WHERE expense_date >= ? AND expense_date < ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (start, end),
    ).fetchall()
    conn.close()

    return jsonify(
        {
            "month": month,
            "total": round(total_row["total"], 2),
            "expense_count": total_row["count"],
            "by_category": [
                {
                    "category": row["category"],
                    "total": round(row["total"], 2),
                    "count": row["count"],
                }
                for row in category_rows
            ],
        }
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found."}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Unexpected server error."}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)