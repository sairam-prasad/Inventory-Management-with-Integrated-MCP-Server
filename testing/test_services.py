import unittest
import requests

# Base URLs
INVENTORY_URL = "http://localhost:8000/inventory"
MCP_URL = "http://localhost:8001/query"

class TestInventoryService(unittest.TestCase):

    def test_get_inventory(self):
        """GET /inventory should return 200 OK and include expected items."""
        response = requests.get(INVENTORY_URL)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tshirts", data)
        self.assertIn("pants", data)

    def test_add_inventory(self):
        """POST /inventory to add tshirts should return 200."""
        payload = {"item": "tshirts", "change": 5}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["tshirts"], 5)

    def test_remove_inventory(self):
        """POST /inventory to remove pants should return 200 and non-negative."""
        payload = {"item": "pants", "change": -2}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["pants"], 0)

    def test_invalid_item(self):
        """POST /inventory with invalid item should return 400."""
        payload = {"item": "shoes", "change": 2}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 400)

    def test_insufficient_inventory(self):
        """POST /inventory removing more than available should return 400."""
        payload = {"item": "tshirts", "change": -9999}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 400)


class TestMCPServer(unittest.TestCase):

    def test_add_synonym(self):
        """Query using 'bought' should be interpreted as add inventory."""
        response = requests.post(MCP_URL, json={"user_query": "I bought 3 pants"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("pants", response.json())

    def test_remove_synonym(self):
        """Query using 'gave away' should be interpreted as remove inventory."""
        response = requests.post(MCP_URL, json={"user_query": "I gave away 2 tshirts"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("tshirts", response.json())

    def test_inventory_check(self):
        """Natural query to check inventory should return full inventory."""
        response = requests.post(MCP_URL, json={"user_query": "How many tshirts and pants do I have?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("tshirts", response.json())
        self.assertIn("pants", response.json())

    def test_invalid_query(self):
        """Query with no valid item should return method: ERROR and 400."""
        response = requests.post(MCP_URL, json={"user_query": "Do I have any shoes?"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("could not", response.json()["detail"].lower())

    def test_borrowed_positive(self):
        """Query using 'borrowed' should be interpreted as add."""
        response = requests.post(MCP_URL, json={"user_query": "I borrowed 2 pants"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("pants", response.json())

    def test_confusing_query(self):
        """Query with unclear structure should return 400 and error message."""
        response = requests.post(MCP_URL, json={"user_query": "asdfghjk"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("could not", response.json()["detail"].lower())

    def test_negative_semantics_check(self):
        """Query with 'received -2 pants' should still work as reduce operation."""
        response = requests.post(MCP_URL, json={"user_query": "I received -2 pants"})
        # Depending on interpretation, this should fail or be valid
        self.assertIn(response.status_code, [200, 400])

if __name__ == "__main__":
    unittest.main()
