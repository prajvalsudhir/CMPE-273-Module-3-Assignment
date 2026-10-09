"""Inventory Service (REST version).

Exposes POST /inventory/check, which takes JSON
{"item_id": ..., "quantity": ...} and reports availability.

Set INVENTORY_DELAY (seconds) to simulate a slow inventory service.
"""
import os
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

# item_id -> units in stock
INVENTORY = {"widget": 100, "gadget": 50, "gizmo": 0}

DELAY = float(os.environ.get("INVENTORY_DELAY", "0"))


@app.post("/inventory/check")
def check_inventory():
    time.sleep(DELAY)
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("item_id")
    quantity = data.get("quantity", 0)

    if not item_id or item_id not in INVENTORY:
        return jsonify({"error": "item not found", "item_id": item_id}), 404

    stock = INVENTORY[item_id]
    if stock < quantity:
        return (
            jsonify(
                {"error": "insufficient stock", "item_id": item_id, "stock": stock}
            ),
            409,
        )

    return jsonify({"item_id": item_id, "available": True, "stock": stock}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
