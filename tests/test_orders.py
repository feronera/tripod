import unittest

from app import orders


class OrderStatusTest(unittest.TestCase):
    def test_get_order_returns_copy(self):
        order = orders.get_order("A1001")
        self.assertEqual(order["customer_id"], "C001")
        order["items"].append("x")
        self.assertNotIn("x", orders.get_order("A1001")["items"])

    def test_get_order_missing(self):
        self.assertIsNone(orders.get_order("NOPE"))

    def test_status_for_owner(self):
        result = orders.status_for_customer("C001", "A1001")
        self.assertEqual(result, {"order_id": "A1001", "status": "shipped", "label": "จัดส่งแล้ว"})

    def test_other_customer_order_is_hidden(self):
        with self.assertRaises(orders.OrderNotFound) as other:
            orders.status_for_customer("C002", "A1001")
        with self.assertRaises(orders.OrderNotFound) as missing:
            orders.status_for_customer("C002", "NOPE")
        self.assertEqual(str(other.exception), str(missing.exception))

    def test_thai_labels(self):
        self.assertEqual(orders.status_label("pending"), "รอชำระเงิน")
        self.assertEqual(orders.status_label("unknown"), "unknown")

    def test_orders_for_customer(self):
        ids = [o["order_id"] for o in orders.orders_for_customer("C001")]
        self.assertEqual(ids, ["A1001", "A1002"])
        self.assertEqual(orders.orders_for_customer("C999"), [])


if __name__ == "__main__":
    unittest.main()
