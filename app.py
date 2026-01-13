from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# -------------------------------------------------
# ENV SETUP
# -------------------------------------------------
load_dotenv()

MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")  # REQUIRED
MONEYUNIFY_BASE_URL = "https://api.moneyunify.one"

app = Flask(__name__)

# -------------------------------------------------
# SIMPLE IN-MEMORY PAYMENT STORE
# phone_number -> PENDING | SUCCESS | FAILED
# -------------------------------------------------
payments = {}

# -------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "StudyCraft server running", 200

# -------------------------------------------------
# 1️⃣ REQUEST PAYMENT (called by Kivy app)
# -------------------------------------------------
@app.route("/request_payment", methods=["POST"])
def request_payment():
    data = request.get_json(force=True)

    phone = data.get("phone_number")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({
            "isError": True,
            "message": "phone_number and amount are required"
        }), 400

    # Register payment as pending
    payments[phone] = "PENDING"

    payload = {
        "from_payer": phone,
        "amount": amount,
        "auth_id": MONEYUNIFY_AUTH_ID
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        response = requests.post(
            f"{MONEYUNIFY_BASE_URL}/payments/request",
            data=payload,
            headers=headers,
            timeout=30
        )
        return jsonify(response.json()), response.status_code

    except Exception as e:
        payments[phone] = "FAILED"
        return jsonify({
            "isError": True,
            "message": str(e)
        }), 500

# -------------------------------------------------
# 2️⃣ MONEYUNIFY WEBHOOK (CALLBACK)
# -------------------------------------------------
@app.route("/webhook/moneyunify", methods=["POST"])
def moneyunify_webhook():
    payload = request.get_json(force=True)

    print("📥 MoneyUnify webhook received:", payload)

    phone = payload.get("from_payer")
    status = payload.get("status")

    if not phone or not status:
        return jsonify({"message": "Invalid webhook payload"}), 400

    status = status.upper()

    if status in ("SUCCESS", "COMPLETED"):
        payments[phone] = "SUCCESS"
    elif status in ("FAILED", "REJECTED"):
        payments[phone] = "FAILED"

    return jsonify({"message": "Webhook processed"}), 200

# -------------------------------------------------
# 3️⃣ PAYMENT STATUS CHECK (polled by Kivy)
# -------------------------------------------------
@app.route("/payment_status", methods=["GET"])
def payment_status():
    phone = request.args.get("phone")

    if not phone:
        return jsonify({"error": "phone parameter required"}), 400

    status = payments.get(phone, "UNKNOWN")

    return jsonify({"status": status}), 200

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    app.run()


# from flask import Flask, request, jsonify
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)

# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")
# MONEYUNIFY_BASE_URL = "https://api.moneyunify.one"

# # ---------------------------------------------------
# # 1️⃣ REQUEST PAYMENT (called by Kivy app)
# # ---------------------------------------------------
# @app.route("/request_payment", methods=["POST"])
# def request_payment():
#     data = request.get_json(force=True)

#     phone = data.get("phone_number")
#     amount = data.get("amount")

#     if not phone or not amount:
#         return jsonify({"error": "Missing phone or amount"}), 400

#     payload = {
#         "from_payer": phone,
#         "amount": amount,
#         "auth_id": MONEYUNIFY_AUTH_ID
#     }

#     headers = {
#         "Accept": "application/json",
#         "Content-Type": "application/x-www-form-urlencoded"
#     }

#     response = requests.post(
#         f"{MONEYUNIFY_BASE_URL}/payments/request",
#         data=payload,
#         headers=headers,
#         timeout=30
#     )

#     return jsonify(response.json()), response.status_code


# # ---------------------------------------------------
# # 2️⃣ MONEYUNIFY CALLBACK (WEBHOOK)
# # ---------------------------------------------------
# @app.route("/webhook/moneyunify", methods=["POST"])
# def moneyunify_webhook():
#     payload = request.get_json(force=True)

#     # Example fields (depends on MoneyUnify)
#     transaction_id = payload.get("transaction_id")
#     status = payload.get("status")
#     phone = payload.get("from_payer")
#     amount = payload.get("amount")

#     print("📥 CALLBACK RECEIVED:", payload)

#     # TODO:
#     # - Save to database
#     # - Mark user as paid
#     # - Unlock StudyCraft content

#     return jsonify({"message": "Webhook received"}), 200


# @app.route("/", methods=["GET"])
# def health():
#     return "StudyCraft server running", 200


# if __name__ == "__main__":
#     app.run()


