"""Inventory Service (gRPC version).

Implements the InventoryService contract from inventory.proto.
Set INVENTORY_DELAY (seconds) to simulate a slow inventory service.
"""
import os
import time
from concurrent import futures

import grpc

import inventory_pb2
import inventory_pb2_grpc

# item_id -> units in stock
INVENTORY = {"widget": 100, "gadget": 50, "gizmo": 0}

DELAY = float(os.environ.get("INVENTORY_DELAY", "0"))


class InventoryServicer(inventory_pb2_grpc.InventoryServiceServicer):
    def CheckInventory(self, request, context):
        time.sleep(DELAY)  # simulate a slow inventory service
        item_id, quantity = request.item_id, request.quantity

        if item_id not in INVENTORY:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"item not found: {item_id}")
            return inventory_pb2.CheckResponse()

        stock = INVENTORY[item_id]
        if stock < quantity:
            context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
            context.set_details(
                f"insufficient stock for {item_id}: "
                f"requested {quantity}, have {stock}"
            )
            return inventory_pb2.CheckResponse()

        return inventory_pb2.CheckResponse(available=True, stock=stock)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryServicer(), server
    )
    server.add_insecure_port("0.0.0.0:50051")
    server.start()
    print("gRPC Inventory Service listening on :50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
