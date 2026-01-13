from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")
MONEYUNIFY_BASE_URL = "https://api.moneyunify.one"

# ---------------------------------------------------
# 1️⃣ REQUEST PAYMENT (called by Kivy app)
# ---------------------------------------------------
@app.route("/request_payment", methods=["POST"])
def request_payment():
    data = request.get_json(force=True)

    phone = data.get("phone_number")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "Missing phone or amount"}), 400

    payload = {
        "from_payer": phone,
        "amount": amount,
        "auth_id": MONEYUNIFY_AUTH_ID
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(
        f"{MONEYUNIFY_BASE_URL}/payments/request",
        data=payload,
        headers=headers,
        timeout=30
    )

    return jsonify(response.json()), response.status_code


# ---------------------------------------------------
# 2️⃣ MONEYUNIFY CALLBACK (WEBHOOK)
# ---------------------------------------------------
@app.route("/webhook/moneyunify", methods=["POST"])
def moneyunify_webhook():
    payload = request.get_json(force=True)

    # Example fields (depends on MoneyUnify)
    transaction_id = payload.get("transaction_id")
    status = payload.get("status")
    phone = payload.get("from_payer")
    amount = payload.get("amount")

    print("📥 CALLBACK RECEIVED:", payload)

    # TODO:
    # - Save to database
    # - Mark user as paid
    # - Unlock StudyCraft content

    return jsonify({"message": "Webhook received"}), 200


@app.route("/", methods=["GET"])
def health():
    return "StudyCraft server running", 200


if __name__ == "__main__":
    app.run()


# import os
# import sqlite3
# import requests
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # MoneyUnify auth ID (from environment variable)
# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

# # Simple SQLite DB for storing payment info
# DB_PATH = "payments.db"

# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS payments (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             reference TEXT UNIQUE,
#             payment_url TEXT,
#             status TEXT DEFAULT 'PENDING'
#         )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# @app.route("/")
# def home():
#     return jsonify({"status": "running"})

# @app.route("/create_payment_link", methods=["POST"])
# def create_payment_link():
#     # Accept JSON from client
#     data = request.get_json(force=True)
#     if not data:
#         return {"error": "JSON body required"}, 400

#     phone = data.get("phone_number")
#     amount = data.get("amount")
#     description = data.get("description", "StudyCraft Payment")

#     if not amount:
#         return {"error": "amount is required"}, 400

#     # MoneyUnify expects form-encoded POST
#     payload = {
#         "auth_id": os.getenv("MONEYUNIFY_AUTH_ID"),
#         "amount": str(amount),
#         "description": description,
#         "is_fixed_amount": "false",
#         "is_once_off": "false"
#     }
#     if phone:
#         payload["phone_number"] = phone

#     headers = {"Content-Type": "application/x-www-form-urlencoded"}

#     import requests
#     r = requests.post("https://api.moneyunify.one/links/create", data=payload, headers=headers)
#     try:
#         result = r.json()
#     except:
#         return {"error": "Invalid response from MoneyUnify", "raw": r.text}, 500

#     if not result.get("isError"):
#         return {
#             "reference": result["data"].get("unique_id"),
#             "payment_url": result["data"].get("payment_url")
#         }

#     return result, 400

# @app.route("/verify_payment/<reference>", methods=["GET"])
# def verify_payment(reference):
#     # Lookup DB record first
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.execute("SELECT status FROM payments WHERE reference=?", (reference,))
#     row = cur.fetchone()
#     conn.close()

#     if row and row[0] == "successful":
#         return jsonify({"status": "successful"})

#     # Call MoneyUnify verify API
#     payload = {
#         "auth_id": MONEYUNIFY_AUTH_ID,
#         "transaction_id": reference
#     }
#     r = requests.post("https://api.moneyunify.one/payments/verify", data=payload)
#     result = r.json()

#     if not result.get("isError"):
#         status = result["data"]["status"]
#         conn = sqlite3.connect(DB_PATH)
#         conn.execute(
#             "UPDATE payments SET status=? WHERE reference=?", (status, reference)
#         )
#         conn.commit()
#         conn.close()
#         return jsonify({"status": status})

#     return jsonify(result), 400

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

