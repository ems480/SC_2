import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

@app.route("/moneyunify/account-lookup", methods=["POST"])
def account_lookup():
    data = request.get_json(force=True)
    phone_number = data.get("phone_number")

    if not phone_number:
        return jsonify({
            "isError": True,
            "message": "phone_number is required"
        }), 400

    if not MONEYUNIFY_AUTH_ID:
        return jsonify({
            "isError": True,
            "message": "Server auth_id not configured"
        }), 500

    payload = {
        "auth_id": MONEYUNIFY_AUTH_ID,
        "phone_number": phone_number
    }

    try:
        res = requests.post(
            "https://api.moneyunify.one/account/lookup",
            data=payload,
            timeout=30
        )
        return jsonify(res.json()), res.status_code

    except Exception as e:
        return jsonify({
            "isError": True,
            "message": str(e)
        }), 500



# import os
# import requests
# from flask import Flask, request, jsonify

# app = Flask(__name__)

# MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")
# BASE_URL = "https://api.moneyunify.one"


# @app.route("/moneyunify/account-lookup", methods=["POST"])
# def account_lookup():
#     data = request.get_json(force=True)
#     phone_number = data.get("phone_number")

#     if not phone_number:
#         return jsonify({"error": "phone_number required"}), 400

#     payload = {
#         "auth_id": MONEYUNIFY_AUTH_ID,
#         "phone_number": phone_number
#     }

#     response = requests.post(
#         f"{BASE_URL}/account/lookup",
#         data=payload,
#         timeout=30
#     )

#     return jsonify(response.json())



