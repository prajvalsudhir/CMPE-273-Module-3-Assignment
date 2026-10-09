"""Order Service (REST version).

Accepts POST /order with JSON {"item_id": ..., "quantity": ...},
checks the Inventory Service over HTTP, and places or rejects the order.

The call to the Inventory Service has a timeout (INVENTORY_TIMEOUT,
default 2s). A slow inventory fails the order (504) but the Order
Service keeps running.
"""
import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://localhost:5001")
INVENTORY_TIMEOUT = float(os.environ.get("INVENTORY_TIMEOUT", "2"))

orders = []


@app.post("/order")
def place_order():
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    try:
        resp = requests.post(
            f"{INVENTORY_URL}/inventory/check",
            json={"item_id": item_id, "quantity": quantity},
            timeout=INVENTORY_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        return jsonify({"error": "inventory service timed out",
                        "item_id": item_id}), 504

    if resp.status_code == 200:
        order = {"order_id": len(orders) + 1, "item_id": item_id,
                 "quantity": quantity, "status": "placed"}
        orders.append(order)
        return jsonify(order), 201

    return (
        jsonify({"status": "rejected", "item_id": item_id,
                 "reason": resp.json()}),
        resp.status_code,
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
