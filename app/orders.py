"""Order status lookup for customers (sample domain, in-memory data)."""

STATUS_LABELS = {
    "pending": "รอชำระเงิน",
    "paid": "ชำระเงินแล้ว",
    "packing": "กำลังเตรียมสินค้า",
    "shipped": "จัดส่งแล้ว",
    "delivered": "ได้รับสินค้าแล้ว",
    "cancelled": "ยกเลิกแล้ว",
}

_ORDERS = {
    "A1001": {"customer_id": "C001", "status": "shipped", "items": ["เสื้อยืด", "หมวก"]},
    "A1002": {"customer_id": "C001", "status": "delivered", "items": ["รองเท้า"]},
    "A1003": {"customer_id": "C002", "status": "pending", "items": ["กระเป๋า"]},
    "A1004": {"customer_id": "C003", "status": "cancelled", "items": ["นาฬิกา"]},
}


class OrderNotFound(LookupError):
    """Raised when an order does not exist or does not belong to the customer."""


def get_order(order_id):
    """Return a copy of the order, or None when it does not exist (internal use)."""
    order = _ORDERS.get(order_id)
    if order is None:
        return None
    return {"order_id": order_id, **order, "items": list(order["items"])}


def status_label(status):
    """Thai label for a status code; unknown codes are shown as-is."""
    return STATUS_LABELS.get(status, status)


def status_for_customer(customer_id, order_id):
    """Status of one order for the customer who owns it.

    Another customer's order raises the same error as a missing order,
    so the response never reveals that the order exists.
    """
    order = get_order(order_id)
    if order is None or order["customer_id"] != customer_id:
        raise OrderNotFound("ไม่พบคำสั่งซื้อ")
    return {
        "order_id": order_id,
        "status": order["status"],
        "label": status_label(order["status"]),
    }


def orders_for_customer(customer_id):
    """All orders of one customer, sorted by order id."""
    return [
        status_for_customer(customer_id, order_id)
        for order_id in sorted(_ORDERS)
        if _ORDERS[order_id]["customer_id"] == customer_id
    ]
