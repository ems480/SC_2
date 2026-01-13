from flask import Flask, request, jsonify
import requests
import sqlite3
import uuid
import os

MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")
BASE_URL = "https://api.moneyunify.one"

app = Flask(__name__)

# -----------------------------------------
# DATABASE
# -----------------------------------------
def db():
    conn = sqlite3.connect("payments.db")
    conn.row_factory = sqlite3.Row
    return conn

with db() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            phone TEXT,
            amount REAL,
            status TEXT
        )
    """)

# -----------------------------------------
# REQUEST PAYMENT
# -----------------------------------------
@app.route("/request_payment", methods=["POST"])
def request_payment():
    data = request.get_json(force=True)  # force=True ensures JSON is parsed
    # accept either "phone" or "phone_number"
    phone = data.get("phone") or data.get("phone_number")
    amount = data.get("amount")

    if not phone or not amount:
        return {"error": "phone and amount are required"}, 400

    tx_id = str(uuid.uuid4())

    with db() as conn:
        conn.execute(
            "INSERT INTO payments VALUES (?, ?, ?, ?)",
            (tx_id, phone, amount, "PENDING")
        )

    payload = {
        "from_payer": phone,
        "amount": amount,
        "auth_id": MONEYUNIFY_AUTH_ID,
        "reference": tx_id
    }

    r = requests.post(
        f"{BASE_URL}/payments/request",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    return jsonify({
        "transaction_id": tx_id,
        "moneyunify": r.json()
    })

# @app.route("/request_payment", methods=["POST"])
# def request_payment():
#     data = request.get_json()
#     phone = data["phone"]
#     amount = data["amount"]

#     tx_id = str(uuid.uuid4())

#     with db() as conn:
#         conn.execute(
#             "INSERT INTO payments VALUES (?, ?, ?, ?)",
#             (tx_id, phone, amount, "PENDING")
#         )

#     payload = {
#         "from_payer": phone,
#         "amount": amount,
#         "auth_id": MONEYUNIFY_AUTH_ID,
#         "reference": tx_id
#     }

#     r = requests.post(
#         f"{BASE_URL}/payments/request",
#         data=payload,
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )

#     return jsonify({
#         "transaction_id": tx_id,
#         "moneyunify": r.json()
#     })

# -----------------------------------------
# WEBHOOK
# -----------------------------------------
@app.route("/webhook/moneyunify", methods=["POST"])
def webhook():
    payload = request.get_json()
    print("WEBHOOK:", payload)

    tx_id = payload.get("reference")
    status = payload.get("status")

    if not tx_id:
        return "ignored", 200

    with db() as conn:
        conn.execute(
            "UPDATE payments SET status=? WHERE id=?",
            (status.upper(), tx_id)
        )

    return "ok", 200

# -----------------------------------------
# STATUS CHECK
# -----------------------------------------
@app.route("/payment_status/<tx_id>")
def payment_status(tx_id):
    with db() as conn:
        row = conn.execute(
            "SELECT status FROM payments WHERE id=?",
            (tx_id,)
        ).fetchone()

    if not row:
        return jsonify({"status": "UNKNOWN"})

    return jsonify({"status": row["status"]})

if __name__ == "__main__":
    app.run()


# from flask import Flask, request, jsonify
# import requests
# import os
# from dotenv import load_dotenv

# # -------------------------------------------------
# # ENV SETUP
# # -------------------------------------------------
# load_dotenv()

# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")  # REQUIRED
# MONEYUNIFY_BASE_URL = "https://api.moneyunify.one"

# app = Flask(__name__)

# # -------------------------------------------------
# # SIMPLE IN-MEMORY PAYMENT STORE
# # phone_number -> PENDING | SUCCESS | FAILED
# # -------------------------------------------------
# payments = {}

# # -------------------------------------------------
# # HEALTH CHECK
# # -------------------------------------------------
# @app.route("/", methods=["GET"])
# def home():
#     return "StudyCraft server running", 200

# # -------------------------------------------------
# # 1️⃣ REQUEST PAYMENT (called by Kivy app)
# # -------------------------------------------------
# @app.route("/request_payment", methods=["POST"])
# def request_payment():
#     data = request.get_json(force=True)

#     phone = data.get("phone_number")
#     amount = data.get("amount")

#     if not phone or not amount:
#         return jsonify({
#             "isError": True,
#             "message": "phone_number and amount are required"
#         }), 400

#     # Register payment as pending
#     payments[phone] = "PENDING"

#     payload = {
#         "from_payer": phone,
#         "amount": amount,
#         "auth_id": MONEYUNIFY_AUTH_ID
#     }

#     headers = {
#         "Accept": "application/json",
#         "Content-Type": "application/x-www-form-urlencoded"
#     }

#     try:
#         response = requests.post(
#             f"{MONEYUNIFY_BASE_URL}/payments/request",
#             data=payload,
#             headers=headers,
#             timeout=30
#         )
#         return jsonify(response.json()), response.status_code

#     except Exception as e:
#         payments[phone] = "FAILED"
#         return jsonify({
#             "isError": True,
#             "message": str(e)
#         }), 500

# # -------------------------------------------------
# # 2️⃣ MONEYUNIFY WEBHOOK (CALLBACK)
# # -------------------------------------------------
# @app.route("/webhook/moneyunify", methods=["POST"])
# def moneyunify_webhook():
#     payload = request.get_json(force=True)

#     print("📥 MoneyUnify webhook received:", payload)

#     phone = payload.get("from_payer")
#     status = payload.get("status")

#     if not phone or not status:
#         return jsonify({"message": "Invalid webhook payload"}), 400

#     status = status.upper()

#     if status in ("SUCCESS", "COMPLETED"):
#         payments[phone] = "SUCCESS"
#     elif status in ("FAILED", "REJECTED"):
#         payments[phone] = "FAILED"

#     return jsonify({"message": "Webhook processed"}), 200

# # -------------------------------------------------
# # 3️⃣ PAYMENT STATUS CHECK (polled by Kivy)
# # -------------------------------------------------
# @app.route("/payment_status", methods=["GET"])
# def payment_status():
#     phone = request.args.get("phone")

#     if not phone:
#         return jsonify({"error": "phone parameter required"}), 400

#     status = payments.get(phone, "UNKNOWN")

#     return jsonify({"status": status}), 200

# # -------------------------------------------------
# # ENTRY POINT
# # -------------------------------------------------
# if __name__ == "__main__":
#     app.run()

