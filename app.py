from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# Temporary in-memory storage (replace with DB in production)
payments = {}

# Replace with your MoneyUnify public key
MONEYUNIFY_AUTH_ID = "YOUR_MONEYUNIFY_PUBLIC_KEY"

@app.route("/request_payment", methods=["POST"])
def request_payment():
    data = request.get_json(force=True)
    phone = data.get("phone") or data.get("phone_number")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone and amount are required"}), 400

    tx_id = str(uuid.uuid4())
    payments[tx_id] = {"phone": phone, "amount": amount, "status": "PENDING"}

    # Call MoneyUnify API
    import requests
    payload = {
        "from_payer": phone,
        "amount": str(amount),
        "auth_id": MONEYUNIFY_AUTH_ID,
        "reference": tx_id
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        r = requests.post("https://api.moneyunify.one/payments/request", data=payload, headers=headers)
        resp_json = r.json()
    except Exception as e:
        resp_json = {"error": str(e)}

    return jsonify({
        "transaction_id": tx_id,
        "moneyunify_response": resp_json
    })


@app.route("/payment_status", methods=["GET"])
def payment_status():
    tx_id = request.args.get("transaction_id")
    if not tx_id:
        return jsonify({"error": "transaction_id is required"}), 400

    if tx_id not in payments:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({
        "transaction_id": tx_id,
        "status": payments[tx_id]["status"]
    })


@app.route("/moneyunify_webhook", methods=["POST"])
def moneyunify_webhook():
    data = request.get_json(force=True)
    ref = data.get("reference")
    status = data.get("status")  # "successful" or "failed"

    if ref and ref in payments:
        payments[ref]["status"] = status

    return jsonify({"message": "Webhook received"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)


# from flask import Flask, request, jsonify
# import requests
# import sqlite3
# import uuid
# import os

# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")
# BASE_URL = "https://api.moneyunify.one"

# app = Flask(__name__)

# # -----------------------------------------
# # DATABASE
# # -----------------------------------------
# def db():
#     conn = sqlite3.connect("payments.db")
#     conn.row_factory = sqlite3.Row
#     return conn

# with db() as conn:
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS payments (
#             id TEXT PRIMARY KEY,
#             phone TEXT,
#             amount REAL,
#             status TEXT
#         )
#     """)

# # -----------------------------------------
# # REQUEST PAYMENT
# # -----------------------------------------
# @app.route("/request_payment", methods=["POST"])
# def request_payment():
#     data = request.get_json(force=True)  # force=True ensures JSON is parsed
#     # accept either "phone" or "phone_number"
#     phone = data.get("phone") or data.get("phone_number")
#     amount = data.get("amount")

#     if not phone or not amount:
#         return {"error": "phone and amount are required"}, 400

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

# # @app.route("/request_payment", methods=["POST"])
# # def request_payment():
# #     data = request.get_json()
# #     phone = data["phone"]
# #     amount = data["amount"]

# #     tx_id = str(uuid.uuid4())

# #     with db() as conn:
# #         conn.execute(
# #             "INSERT INTO payments VALUES (?, ?, ?, ?)",
# #             (tx_id, phone, amount, "PENDING")
# #         )

# #     payload = {
# #         "from_payer": phone,
# #         "amount": amount,
# #         "auth_id": MONEYUNIFY_AUTH_ID,
# #         "reference": tx_id
# #     }

# #     r = requests.post(
# #         f"{BASE_URL}/payments/request",
# #         data=payload,
# #         headers={"Content-Type": "application/x-www-form-urlencoded"}
# #     )

# #     return jsonify({
# #         "transaction_id": tx_id,
# #         "moneyunify": r.json()
# #     })

# # -----------------------------------------
# # WEBHOOK
# # -----------------------------------------
# @app.route("/webhook/moneyunify", methods=["POST"])
# def webhook():
#     payload = request.get_json()
#     print("WEBHOOK:", payload)

#     tx_id = payload.get("reference")
#     status = payload.get("status")

#     if not tx_id:
#         return "ignored", 200

#     with db() as conn:
#         conn.execute(
#             "UPDATE payments SET status=? WHERE id=?",
#             (status.upper(), tx_id)
#         )

#     return "ok", 200

# # -----------------------------------------
# # STATUS CHECK
# # -----------------------------------------
# @app.route("/payment_status/<tx_id>")
# def payment_status(tx_id):
#     with db() as conn:
#         row = conn.execute(
#             "SELECT status FROM payments WHERE id=?",
#             (tx_id,)
#         ).fetchone()

#     if not row:
#         return jsonify({"status": "UNKNOWN"})

#     return jsonify({"status": row["status"]})

# if __name__ == "__main__":
#     app.run()
