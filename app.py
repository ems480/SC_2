import os
import sqlite3
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load your MoneyUnify auth_id securely
MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

# Simple SQLite DB for payments
DB_PATH = "payments.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference TEXT UNIQUE,
        payment_url TEXT,
        status TEXT DEFAULT 'PENDING'
    )""")
    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return jsonify({"status": "running"})


@app.route("/create_payment_link", methods=["POST"])
def create_payment_link():
    """
    Creates a MoneyUnify payment link via /links/create
    """
    data = request.json
    phone = data.get("phone_number")  # optional: link can be generic
    amount = data.get("amount")
    description = data.get("description", "StudyCraft Payment")

    if not amount:
        return jsonify({"error": "amount is required"}), 400

    payload = {
    "auth_id": MONEYUNIFY_AUTH_ID,
    "amount": amount,
    "description": description,
    "is_fixed_amount": True,   # <-- boolean
    "is_once_off": True,       # <-- boolean
    }

    # payload = {
    #     "auth_id": MONEYUNIFY_AUTH_ID,
    #     "amount": amount,
    #     "description": description,
    #     "is_fixed_amount": "true",
    #     "is_once_off": "true",
    # }

    # Send to MoneyUnify
    r = requests.post(
        "https://api.moneyunify.one/links/create",
        data=payload
    )
    result = r.json()

    # If MoneyUnify succeeded
    if not result.get("isError"):
        payment_url = result["data"]["payment_url"]
        # Use unique_id or reference
        reference = result["data"].get("unique_id")

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR IGNORE INTO payments (reference, payment_url) VALUES (?, ?)",
            (reference, payment_url)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "reference": reference,
            "payment_url": payment_url
        })

    return jsonify(result), 400


@app.route("/verify_payment/<reference>", methods=["GET"])
def verify_payment(reference):
    """
    Verifies payment via MoneyUnify /payments/verify
    """
    # Lookup DB record
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT status FROM payments WHERE reference=?", (reference,)
    )
    row = cur.fetchone()
    conn.close()

    # If already marked success locally
    if row and row[0] == "successful":
        return jsonify({"status": "successful"})

    # Call MoneyUnify verify API
    payload = {
        "auth_id": MONEYUNIFY_AUTH_ID,
        "transaction_id": reference
    }
    r = requests.post(
        "https://api.moneyunify.one/payments/verify",
        data=payload
    )
    result = r.json()

    if not result.get("isError"):
        status = result["data"]["status"]  # e.g. "successful"
        # Update our DB
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE payments SET status=? WHERE reference=?", (status, reference)
        )
        conn.commit()
        conn.close()

        return jsonify({"status": status})

    return jsonify(result), 400



# import os
# import requests
# from flask import Flask, request, jsonify

# app = Flask(__name__)

# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

# @app.route("/moneyunify/account-lookup", methods=["POST"])
# def account_lookup():
#     data = request.get_json(force=True)
#     phone_number = data.get("phone_number")

#     if not phone_number:
#         return jsonify({
#             "isError": True,
#             "message": "phone_number is required"
#         }), 400

#     if not MONEYUNIFY_AUTH_ID:
#         return jsonify({
#             "isError": True,
#             "message": "Server auth_id not configured"
#         }), 500

#     payload = {
#         "auth_id": MONEYUNIFY_AUTH_ID,
#         "phone_number": phone_number
#     }

#     try:
#         res = requests.post(
#             "https://api.moneyunify.one/account/lookup",
#             data=payload,
#             timeout=30
#         )
#         return jsonify(res.json()), res.status_code

#     except Exception as e:
#         return jsonify({
#             "isError": True,
#             "message": str(e)
#         }), 500


