"""Order Service (gRPC version).

Accepts POST /order with JSON {"item_id": ..., "quantity": ...},
checks the Inventory Service over gRPC, and places or rejects the order.

The gRPC call has a deadline (INVENTORY_DEADLINE, default 2s). A slow
inventory fails the order (504) but the Order Service keeps running.
"""
import os

import grpc
from flask import Flask, jsonify, request

import inventory_pb2
import inventory_pb2_grpc

app = Flask(__name__)

INVENTORY_TARGET = os.environ.get("INVENTORY_TARGET", "localhost:50051")
INVENTORY_DEADLINE = float(os.environ.get("INVENTORY_DEADLINE", "2"))

channel = grpc.insecure_channel(INVENTORY_TARGET)
stub = inventory_pb2_grpc.InventoryServiceStub(channel)

orders = []


@app.post("/order")
def place_order():
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    try:
        resp = stub.CheckInventory(
            inventory_pb2.CheckRequest(item_id=item_id, quantity=quantity),
            timeout=INVENTORY_DEADLINE,
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            return jsonify({"error": "inventory deadline exceeded",
                            "item_id": item_id}), 504
        return (
            jsonify({"status": "rejected", "item_id": item_id,
                     "reason": e.details()}),
            502,
        )

    order = {"order_id": len(orders) + 1, "item_id": item_id,
             "quantity": quantity, "status": "placed",
             "available": resp.available, "stock": resp.stock}
    orders.append(order)
    return jsonify(order), 201


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
