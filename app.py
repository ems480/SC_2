from flask import Flask, request, jsonify
import requests
import uuid

app = Flask(__name__)

MONEYUNIFY_AUTH_ID = "YOUR_MONEYUNIFY_PUBLIC_KEY"  # replace with your key

# Store local transactions (in-memory for demo; can use DB)
transactions = {}

@app.route("/request_payment", methods=["POST"])
def request_payment():
    data = request.get_json(force=True)
    phone = data.get("phone") or data.get("phone_number")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone and amount are required"}), 400

    tx_id = str(uuid.uuid4())

    payload = f"from_payer={phone}&amount={amount}&auth_id={MONEYUNIFY_AUTH_ID}&reference={tx_id}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        r = requests.post("https://api.moneyunify.one/payments/request", data=payload, headers=headers)
        resp_json = r.json()
        # Save transaction locally
        transactions[tx_id] = {"phone": phone, "amount": amount, "status": "PENDING"}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"transaction_id": tx_id, "moneyunify_response": resp_json})


@app.route("/payment_status", methods=["GET"])
def payment_status():
    tx_id = request.args.get("transaction_id")
    if not tx_id:
        return jsonify({"error": "transaction_id is required"}), 400

    payload = f"auth_id={MONEYUNIFY_AUTH_ID}&transaction_id={tx_id}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        r = requests.post("https://api.moneyunify.one/payments/verify", data=payload, headers=headers)
        resp_json = r.json()
        status = resp_json.get("data", {}).get("status", "PENDING")
        transactions[tx_id]["status"] = status
    except Exception as e:
        status = f"error: {e}"

    return jsonify({"transaction_id": tx_id, "status": status})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
