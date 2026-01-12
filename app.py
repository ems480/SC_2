from flask import Flask, request, jsonify
import sqlite3
import uuid
import requests
import os

app = Flask(__name__)
DB = "payments.db"

MONEYUNIFY_MUID = os.getenv("MONEYUNIFY_MUID")
MONEYUNIFY_API = "https://api.moneyunify.com/v2"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            user_id TEXT PRIMARY KEY,
            reference TEXT UNIQUE,
            paid INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


@app.before_first_request
def startup():
    init_db()


@app.route("/create-payment", methods=["POST"])
def create_payment():
    data = request.json
    phone = data.get("phone_number")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone_number and amount required"}), 400

    user_id = str(uuid.uuid4())

    response = requests.post(
        f"{MONEYUNIFY_API}/request_payment",
        json={
            "muid": MONEYUNIFY_MUID,
            "phone_number": phone,
            "amount": amount
        }
    )

    result = response.json()
    reference = result.get("reference")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO payments (user_id, reference) VALUES (?, ?)",
        (user_id, reference)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "user_id": user_id,
        "payment_url": f"https://moneyunify.one/pay/{reference}"
    })


@app.route("/moneyunify-webhook", methods=["POST"])
def moneyunify_webhook():
    data = request.json
    reference = data.get("reference")
    status = data.get("status")

    if status == "successful":
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(
            "UPDATE payments SET paid = 1 WHERE reference = ?",
            (reference,)
        )
        conn.commit()
        conn.close()

    return jsonify({"ok": True})


@app.route("/payment-status/<user_id>", methods=["GET"])
def payment_status(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT paid FROM payments WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    return jsonify({"paid": bool(row and row[0])})


if __name__ == "__main__":
    app.run()
