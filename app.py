import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")
BASE_URL = "https://api.moneyunify.one"


@app.route("/moneyunify/account-lookup", methods=["POST"])
def account_lookup():
    data = request.get_json(force=True)
    phone_number = data.get("phone_number")

    if not phone_number:
        return jsonify({"error": "phone_number required"}), 400

    payload = {
        "auth_id": MONEYUNIFY_AUTH_ID,
        "phone_number": phone_number
    }

    response = requests.post(
        f"{BASE_URL}/account/lookup",
        data=payload,
        timeout=30
    )

    return jsonify(response.json())



# from flask import Flask, request, jsonify, g
# import os, sqlite3, requests, uuid
# from dotenv import load_dotenv
# from flask_cors import CORS

# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # ------------------------------
# # DATABASE SETUP
# # ------------------------------
# DB_PATH = "transactions.db"

# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS payments (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             reference TEXT UNIQUE,
#             amount REAL,
#             status TEXT,
#             created_at TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()

# def get_db():
#     db = getattr(g, "_database", None)
#     if db is None:
#         db = g._database = sqlite3.connect(DB_PATH)
#         db.row_factory = sqlite3.Row
#     return db

# # Initialize DB safely
# with app.app_context():
#     init_db()

# # ------------------------------
# # API KEYS
# # ------------------------------
# MONEYUNIFY_API_KEY = os.getenv("MONEYUNIFY_API_KEY")
# BASE_URL = "https://moneyunify.one/api"

# # ------------------------------
# # CREATE PAYMENT
# # ------------------------------
# @app.route("/create-payment", methods=["POST"])
# def create_payment():
#     data = request.json
#     amount = data.get("amount")
#     reference = str(uuid.uuid4())

#     # Save locally as PENDING
#     conn = get_db()
#     cur = conn.cursor()
#     cur.execute("INSERT INTO payments (reference, amount, status, created_at) VALUES (?, ?, ?, datetime('now'))",
#                 (reference, amount, "PENDING"))
#     conn.commit()

#     # Call MoneyUnify API
#     headers = {"Authorization": f"Bearer {MONEYUNIFY_API_KEY}", "Content-Type": "application/json"}
#     payload = {
#         "amount": amount,
#         "currency": "ZMW",
#         "reference": reference,
#         "description": "StudyCraft Payment"
#     }
#     r = requests.post(f"{BASE_URL}/payments", json=payload, headers=headers)
#     response = r.json()
#     response["reference"] = reference  # return reference to app

#     return jsonify(response)

# # ------------------------------
# # WEBHOOK FROM MONEYUNIFY
# # ------------------------------
# @app.route("/webhook", methods=["POST"])
# def webhook():
#     event = request.json
#     reference = event.get("reference")
#     status = event.get("status", "PENDING")

#     conn = get_db()
#     cur = conn.cursor()
#     cur.execute("UPDATE payments SET status = ? WHERE reference = ?", (status, reference))
#     conn.commit()
#     return jsonify({"status": "ok"})

# # ------------------------------
# # CHECK PAYMENT STATUS
# # ------------------------------
# @app.route("/check-payment/<reference>", methods=["GET"])
# def check_payment(reference):
#     conn = get_db()
#     cur = conn.cursor()
#     cur.execute("SELECT status FROM payments WHERE reference = ?", (reference,))
#     row = cur.fetchone()
#     return jsonify({"status": row["status"] if row else "NOT_FOUND"})

# # ------------------------------
# # CLEANUP DB ON REQUEST TEARDOWN
# # ------------------------------
# @app.teardown_appcontext
# def close_connection(exception):
#     db = getattr(g, "_database", None)
#     if db is not None:
#         db.close()

# if __name__ == "__main__":
#     app.run()

# # from flask import Flask, request, jsonify
# # import sqlite3
# # import uuid
# # import requests
# # import os

# # app = Flask(__name__)
# # DB = "payments.db"

# # MONEYUNIFY_MUID = os.getenv("MONEYUNIFY_MUID")
# # MONEYUNIFY_API = "https://api.moneyunify.com/v2"


# # def init_db():
# #     conn = sqlite3.connect(DB)
# #     c = conn.cursor()
# #     c.execute("""
# #         CREATE TABLE IF NOT EXISTS payments (
# #             user_id TEXT PRIMARY KEY,
# #             reference TEXT UNIQUE,
# #             paid INTEGER DEFAULT 0
# #         )
# #     """)
# #     conn.commit()
# #     conn.close()


# # @app.before_first_request
# # def startup():
# #     init_db()


# # @app.route("/create-payment", methods=["POST"])
# # def create_payment():
# #     data = request.json
# #     phone = data.get("phone_number")
# #     amount = data.get("amount")

# #     if not phone or not amount:
# #         return jsonify({"error": "phone_number and amount required"}), 400

# #     user_id = str(uuid.uuid4())

# #     response = requests.post(
# #         f"{MONEYUNIFY_API}/request_payment",
# #         json={
# #             "muid": MONEYUNIFY_MUID,
# #             "phone_number": phone,
# #             "amount": amount
# #         }
# #     )

# #     result = response.json()
# #     reference = result.get("reference")

# #     conn = sqlite3.connect(DB)
# #     c = conn.cursor()
# #     c.execute(
# #         "INSERT INTO payments (user_id, reference) VALUES (?, ?)",
# #         (user_id, reference)
# #     )
# #     conn.commit()
# #     conn.close()

# #     return jsonify({
# #         "user_id": user_id,
# #         "payment_url": f"https://moneyunify.one/pay/{reference}"
# #     })


# # @app.route("/moneyunify-webhook", methods=["POST"])
# # def moneyunify_webhook():
# #     data = request.json
# #     reference = data.get("reference")
# #     status = data.get("status")

# #     if status == "successful":
# #         conn = sqlite3.connect(DB)
# #         c = conn.cursor()
# #         c.execute(
# #             "UPDATE payments SET paid = 1 WHERE reference = ?",
# #             (reference,)
# #         )
# #         conn.commit()
# #         conn.close()

# #     return jsonify({"ok": True})


# # @app.route("/payment-status/<user_id>", methods=["GET"])
# # def payment_status(user_id):
# #     conn = sqlite3.connect(DB)
# #     c = conn.cursor()
# #     c.execute("SELECT paid FROM payments WHERE user_id = ?", (user_id,))
# #     row = c.fetchone()
# #     conn.close()

# #     return jsonify({"paid": bool(row and row[0])})


# # if __name__ == "__main__":
# #     app.run()


