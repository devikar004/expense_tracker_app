# Personal Expense Tracker

A simple local web application for tracking personal expenses. Users can add, view, edit, and delete expenses, filter them by category/date/title, and see a monthly spending summary.

## Features

- Add an expense with:
  - Title
  - Amount
  - Category: Food, Transport, Shopping, Bills, Entertainment, or Other
  - Date, defaulting to today
  - Optional note
- View all expenses sorted by date, with the most recent expense first.
- Edit or delete any existing expense.
- View a summary for the current month:
  - Total amount spent
  - Number of expenses
  - Breakdown by category
- Filter expenses by:
  - Category
  - Date range (`from` and `to`)
  - Partial title match, case-insensitive
- Handle empty states when no expenses or no matching expenses exist.
- Validate user input on the backend.
- Persist data locally in an SQLite database.

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python + Flask | Lightweight, easy to run locally, and sufficient for a small REST API |
| Database | SQLite | File-based, requires no separate database server, and is ideal for a local single-user app |
| Frontend | HTML, CSS, vanilla JavaScript | Simple, dependency-free UI; avoids unnecessary frontend framework complexity |
| Styling | Plain CSS | Minimal, readable interface without adding a CSS framework |

## Project Structure

```text
expense-tracker/
├── app.py                  # Flask backend, REST API, database setup
├── requirements.txt        # Python dependencies
├── README.md
├── expenses.db             # SQLite database; created automatically
└── static/
    ├── index.html          # Main UI
    ├── app.js              # Frontend logic and API calls
    └── style.css           # Basic styling
```

## How to Run

### 1. Create and activate a virtual environment

From the project root:

```bash
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

The SQLite database file, `expenses.db`, is created automatically on first run.

### Optional: run with Flask CLI

```bash
flask --app app run --debug
```

This enables Flask’s development reloader and debugger. Debug mode is intended only for local development, not production deployment. [28][29]

## How to Use

1. Open `http://127.0.0.1:5000/` in a browser.
2. Enter an expense title, amount, category, date, and optional note.
3. Click **Add expense**.
4. The expense appears in the list, sorted by date with the newest first.
5. Use **Edit** to load an expense into the form, change its values, and save.
6. Use **Delete** to remove an expense after confirmation.
7. Use the filters to narrow the list by title, category, or date range.
8. Check the **Current month summary** section for total spend and category-wise totals.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/expenses` | List expenses; supports filters |
| `POST` | `/api/expenses` | Create an expense |
| `PUT` | `/api/expenses/<id>` | Update an expense |
| `DELETE` | `/api/expenses/<id>` | Delete an expense |
| `GET` | `/api/summary?month=YYYY-MM` | Monthly total and category breakdown |

### Query parameters for listing expenses

| Parameter | Description | Example |
|---|---|---|
| `q` | Partial, case-insensitive title search | `?q=coffee` |
| `category` | Exact category filter | `?category=Food` |
| `from` | Inclusive start date, `YYYY-MM-DD` | `?from=2026-11-01` |
| `to` | Inclusive end date, `YYYY-MM-DD` | `?to=2026-11-30` |

Example:

```text
GET /api/expenses?category=Food&from=2026-11-01&to=2026-11-30&q=coffee
```

### Create an expense

```bash
curl -X POST http://127.0.0.1:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Coffee at Starbucks",
    "amount": 320,
    "category": "Food",
    "date": "2026-11-10",
    "note": "Morning coffee"
  }'
```

### Update an expense

```bash
curl -X PUT http://127.0.0.1:5000/api/expenses/1 \
  -H "Content-Type: application/json" \
  -d '{"amount": 350}'
```

### Delete an expense

```bash
curl -X DELETE http://127.0.0.1:5000/api/expenses/1
```

### Get current month summary

```bash
curl "http://127.0.0.1:5000/api/summary?month=2026-11"
```

## Data Model

The application uses one SQLite table:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    category TEXT NOT NULL,
    expense_date TEXT NOT NULL,
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Dates are stored as ISO-formatted strings in `YYYY-MM-DD` format. This makes sorting, date-range filtering, and monthly aggregation straightforward.

SQLite queries use parameterized `?` placeholders rather than string interpolation, reducing SQL injection risk. [14]

## Validation and Edge Cases

The backend validates:

- Title is non-empty and at most 200 characters.
- Amount is numeric and greater than zero.
- Category is one of the six allowed values.
- Date is a valid ISO date in `YYYY-MM-DD` format.
- Date-range filters are valid dates.
- A `from` date cannot be later than a `to` date.
- Updates can be partial; omitted fields retain their previous values.
- Requests for nonexistent expense IDs return `404`.
- Invalid filters or payloads return `400` with a descriptive error.

The frontend also uses HTML input constraints, such as required fields and a positive numeric amount, but backend validation remains the source of truth.

## What Is Done

- Complete expense CRUD functionality.
- All requested fields and category options.
- Date-default behavior in the browser.
- Date-sorted expense listing.
- Monthly total and category-wise breakdown.
- Category, date-range, and partial-title filters.
- Empty-state messaging.
- Input validation and clear error messages.
- SQLite persistence across app restarts.
- Basic responsive layout using plain CSS.

## What Is Skipped

- **Authentication and multi-user support:** Explicitly out of scope; the app is designed as a personal local tracker.
- **Deployment:** The app is intended to run locally only.
- **Automated tests:** Not required for this task; manual end-to-end testing was performed.
- **Charts and advanced analytics:** Not requested; the summary uses totals and category breakdowns.
- **Multi-currency support:** Not requested; one local currency is assumed.
- **Pixel-perfect UI:** Basic clean styling was implemented, but visual polish was not a priority.

## Known Rough Edges

- The UI formats currency as INR by default. Change the `currency` value in `formatMoney()` inside `static/app.js` if a different currency is needed.
- SQLite stores amounts as `REAL`. For production-grade financial systems, storing minor currency units as integers would avoid floating-point precision concerns.
- The monthly summary endpoint accepts any `YYYY-MM` month, even future months; it returns zero totals if no expenses exist.
- The app uses Flask’s development server and debug mode, which are not suitable for public production deployment. [30]
- There is no pagination; the app is designed for a small personal dataset.

## Manual Test Checklist

The following scenarios were tested:

- Add an expense with all fields.
- Add an expense without a note.
- Confirm that the date field defaults to today.
- Edit an expense and verify that changes persist.
- Delete an expense and verify that it disappears.
- Filter by category.
- Filter by partial title text.
- Filter by a valid date range.
- Confirm that a reversed date range returns an error.
- Confirm that invalid amount, blank title, invalid category, and invalid date inputs are rejected.
- Verify that the monthly total and category breakdown update after adding, editing, or deleting expenses.
- Restart the app and verify that existing expenses remain available.