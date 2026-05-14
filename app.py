from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS


print("LOADING FILE...")

app = Flask(__name__)
CORS(app)

DB = "budgetAppDB.db"

def get_db():
    conn = sqlite3.connect(DB, timeout = 10)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("frontend", path)

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO User (email, username, password, date)
    VALUES (?, ?, ?, datetime('now'))
""", (
    data["email"],
    data["username"],
    data["password"]
))

    conn.commit()
    conn.close()

    return jsonify({"message": "User registered"})

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM User
        WHERE email = ? AND password = ?
    """, (
        data["email"],
        data["password"]
    ))

    user = cursor.fetchone()

    conn.close()

    if user:
        return jsonify({
            "message": "Login successful",
            "user_id": user["user_id"]
        })

    return jsonify({
        "message": "Invalid email or password"
    }), 401


@app.route("/add", methods=["POST"])
def add_transaction():

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO "Transaction"
        (user_id, category_id, amount, type, description, date)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
   """, (
        data["user_id"],
        data["category_id"],
        data["amount"],
        data["type"],
        data["description"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction added"})
  
@app.route("/")
def home():
    return send_from_directory("frontend", "login.html")

@app.route("/test")
def test():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    conn.close()
    return jsonify([dict(row) for row in tables])

@app.route("/transactions/<int:user_id>")
def get_transactions(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.*, c.name as category_name
        FROM "Transaction" t
        JOIN Category c
        ON t.category_id = c.category_id
        WHERE t.user_id = ?
        ORDER BY t.date DESC
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])

@app.route("/add-recurring", methods=["POST"])
def add_recurring():

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO RecurringTransaction
        (
            user_id,
            category_id,
            amount,
            type,
            description,
            frequency,
            next_date
        )
        VALUES (?, ?, ?, ?, ?, ?, date('now'))
    """, (
        data["user_id"],
        data["category_id"],
        data["amount"],
        data["type"],
        data["description"],
        data["frequency"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Recurring transaction added"
    })
@app.route("/recurring-transactions/<int:user_id>")
def get_recurring_transactions(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM RecurringTransaction 
        WHERE user_id = ?
    """,(user_id,))

    rows = cursor.fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])

@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):

    conn = get_db()
    cursor = conn.cursor()

    # income
    cursor.execute("""
        SELECT SUM(amount)
        FROM "Transaction"
        WHERE type = 'income'
        AND user_id = ?
    """, (user_id,))
    income = cursor.fetchone()[0] or 0

    # expenses
    cursor.execute("""
        SELECT SUM(amount)
        FROM "Transaction"
        WHERE type = 'expense'
        AND user_id = ?
    """, (user_id,))
    expenses = cursor.fetchone()[0] or 0

    balance = income - expenses

    # chart data
    cursor.execute("""
        SELECT c.name, SUM(t.amount)
        FROM "Transaction" t
        JOIN Category c
        ON t.category_id = c.category_id
        WHERE t.type = 'expense'
        AND t.user_id = ?
        GROUP BY c.name
    """, (user_id,))
    data = cursor.fetchall()

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    # graph data
    cursor.execute("""
        SELECT 
            strftime('%m', date) as month,
            SUM(amount) as total
        FROM "Transaction"
        WHERE type = 'expense'
        AND user_id = ?
        GROUP BY month
        ORDER BY month
    """, (user_id,))
    monthly_data = cursor.fetchall()

    months = []
    monthly_totals = []

    month_names = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }

    for row in monthly_data:
        months.append(month_names[row["month"]])
        monthly_totals.append(row["total"])

    conn.close()

    return jsonify({
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "categories": categories,
        "amounts": amounts,
        "months": months,
        "monthly_totals": monthly_totals
    })
@app.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT category_id, name FROM Category")
    rows = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(row) for row in rows
    ])
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_transaction(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM "Transaction"
        WHERE transaction_id = ?
    """, (id,))

    print("Rows deleted:", cursor.rowcount)

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction deleted"})

@app.route("/update/<int:id>", methods=["PUT"])
def update_transaction(id):

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE "Transaction"
        SET amount = ?, description = ?
        WHERE transaction_id = ?
    """, (
        data["amount"],
        data["description"],
        id
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction updated"})

print("ROUTES LOADED")

if __name__ == "__main__":
    app.run(debug=True)