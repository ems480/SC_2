import os
import sqlite3
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# MoneyUnify auth ID (from environment variable)
MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

# Simple SQLite DB for storing payment info
DB_PATH = "payments.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE,
            payment_url TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return jsonify({"status": "running"})

@app.route("/create_payment_link", methods=["POST"])
def create_payment_link():
    # Accept JSON from client
    data = request.get_json(force=True)
    if not data:
        return {"error": "JSON body required"}, 400

    phone = data.get("phone_number")
    amount = data.get("amount")
    description = data.get("description", "StudyCraft Payment")

    if not amount:
        return {"error": "amount is required"}, 400

    # MoneyUnify expects form-encoded POST
    payload = {
        "auth_id": os.getenv("MONEYUNIFY_AUTH_ID"),
        "amount": str(amount),
        "description": description,
        "is_fixed_amount": "true",
        "is_once_off": "true"
    }
    if phone:
        payload["phone_number"] = phone

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    import requests
    r = requests.post("https://api.moneyunify.one/links/create", data=payload, headers=headers)
    try:
        result = r.json()
    except:
        return {"error": "Invalid response from MoneyUnify", "raw": r.text}, 500

    if not result.get("isError"):
        return {
            "reference": result["data"].get("unique_id"),
            "payment_url": result["data"].get("payment_url")
        }

    return result, 400

@app.route("/verify_payment/<reference>", methods=["GET"])
def verify_payment(reference):
    # Lookup DB record first
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT status FROM payments WHERE reference=?", (reference,))
    row = cur.fetchone()
    conn.close()

    if row and row[0] == "successful":
        return jsonify({"status": "successful"})

    # Call MoneyUnify verify API
    payload = {
        "auth_id": MONEYUNIFY_AUTH_ID,
        "transaction_id": reference
    }
    r = requests.post("https://api.moneyunify.one/payments/verify", data=payload)
    result = r.json()

    if not result.get("isError"):
        status = result["data"]["status"]
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE payments SET status=? WHERE reference=?", (status, reference)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": status})

    return jsonify(result), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)




# import os
# import sqlite3
# import requests
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # Load your MoneyUnify auth_id securely
# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

# # Simple SQLite DB for payments
# DB_PATH = "payments.db"

# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     conn.execute("""
#     CREATE TABLE IF NOT EXISTS payments (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         reference TEXT UNIQUE,
#         payment_url TEXT,
#         status TEXT DEFAULT 'PENDING'
#     )""")
#     conn.commit()
#     conn.close()

# init_db()


# @app.route("/")
# def home():
#     return jsonify({"status": "running"})

# @app.route("/create_payment_link", methods=["POST"])
# def create_payment_link():
#     data = request.json
#     phone = data.get("phone_number")
#     amount = data.get("amount")
#     description = data.get("description", "StudyCraft Payment")

#     if not amount:
#         return jsonify({"error": "amount is required"}), 400

#     # Form-encoded payload
#     payload = {
#         "auth_id": MONEYUNIFY_AUTH_ID,
#         "amount": str(amount),             # must be string
#         "description": description,
#         "is_fixed_amount": "true",         # string, NOT boolean
#         "is_once_off": "true"              # string, NOT boolean
#     }

#     if phone:
#         payload["phone_number"] = phone

#     # Use data=payload, not json=payload
#     r = requests.post(
#         "https://api.moneyunify.one/links/create",
#         data=payload
#     )

#     result = r.json()

#     if not result.get("isError"):
#         payment_url = result["data"]["payment_url"]
#         reference = result["data"].get("unique_id")

#         # Save to SQLite
#         conn = sqlite3.connect(DB_PATH)
#         conn.execute(
#             "INSERT OR IGNORE INTO payments (reference, payment_url) VALUES (?, ?)",
#             (reference, payment_url)
#         )
#         conn.commit()
#         conn.close()

#         return jsonify({
#             "reference": reference,
#             "payment_url": payment_url
#         })

#     return jsonify(result), 400



# @app.route("/verify_payment/<reference>", methods=["GET"])
# def verify_payment(reference):
#     """
#     Verifies payment via MoneyUnify /payments/verify
#     """
#     # Lookup DB record
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.execute(
#         "SELECT status FROM payments WHERE reference=?", (reference,)
#     )
#     row = cur.fetchone()
#     conn.close()

#     # If already marked success locally
#     if row and row[0] == "successful":
#         return jsonify({"status": "successful"})

#     # Call MoneyUnify verify API
#     payload = {
#         "auth_id": MONEYUNIFY_AUTH_ID,
#         "transaction_id": reference
#     }
#     r = requests.post(
#         "https://api.moneyunify.one/payments/verify",
#         data=payload
#     )
#     result = r.json()

#     if not result.get("isError"):
#         status = result["data"]["status"]  # e.g. "successful"
#         # Update our DB
#         conn = sqlite3.connect(DB_PATH)
#         conn.execute(
#             "UPDATE payments SET status=? WHERE reference=?", (status, reference)
#         )
#         conn.commit()
#         conn.close()

#         return jsonify({"status": status})

#     return jsonify(result), 400



