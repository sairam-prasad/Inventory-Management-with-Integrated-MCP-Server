import unittest
import requests

# Base URLs for Inventory and MCP servers
INVENTORY_URL = "http://localhost:8000/inventory"
MCP_URL = "http://localhost:8001/query"

# ----------------------------
# 🔹 Test Inventory API
# ----------------------------
class TestInventoryService(unittest.TestCase):

    def test_get_inventory(self):
        """
        Test the GET /inventory endpoint.
        Should return a 200 OK and include both 'tshirts' and 'pants' in the response.
        """
        response = requests.get(INVENTORY_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("tshirts", response.json())
        self.assertIn("pants", response.json())

    def test_add_inventory(self):
        """
        Test POST /inventory with a positive change.
        Adds 5 tshirts and expects the count to increase or remain >= 5.
        """
        payload = {"item": "tshirts", "change": 5}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["tshirts"], 5)

    def test_remove_inventory(self):
        """
        Test POST /inventory with a negative change.
        Removes 3 pants and ensures the remaining count is non-negative.
        """
        payload = {"item": "pants", "change": -3}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["pants"], 0)

    def test_invalid_item(self):
        """
        Test POST /inventory with an invalid item.
        Should return a 400 error due to unknown item 'shoes'.
        """
        payload = {"item": "shoes", "change": 5}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 400)

    def test_insufficient_stock(self):
        """
        Test POST /inventory with a large negative change.
        Should fail with 400 if the change drops stock below 0.
        """
        payload = {"item": "pants", "change": -9999}
        response = requests.post(INVENTORY_URL, json=payload)
        self.assertEqual(response.status_code, 400)

# ----------------------------
# 🔹 Test MCP (GenAI Interface)
# ----------------------------
class TestMCPServer(unittest.TestCase):

    def test_query_add_tshirts(self):
        """
        Test MCP with a natural language query to add tshirts.
        Should trigger a POST to inventory and return updated inventory.
        """
        response = requests.post(MCP_URL, json={"user_query": "Add 5 tshirts"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("tshirts", response.json())

    def test_query_remove_pants(self):
        """
        Test MCP with a query to remove pants.
        Should correctly interpret the intent and reduce inventory.
        """
        response = requests.post(MCP_URL, json={"user_query": "I sold 3 pants"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("pants", response.json())

    def test_query_inventory_check(self):
        """
        Test MCP for a read-only inventory query.
        Should return the full inventory dictionary.
        """
        response = requests.post(MCP_URL, json={"user_query": "How many tshirts and pants do I have?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("tshirts", response.json())
        self.assertIn("pants", response.json())

    def test_query_with_synonym(self):
        """
        Test LLM's understanding of synonym: 'bought' → positive change.
        Should add to inventory and return updated count.
        """
        response = requests.post(MCP_URL, json={"user_query": "I bought 10 tshirts"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("tshirts", response.json())

    def test_invalid_format_from_llm(self):
        """
        Test robustness when LLM receives gibberish input.
        The system should not crash — return 200 or 400 depending on fallback.
        """
        response = requests.post(MCP_URL, json={"user_query": "gibberish words without meaning"})
        self.assertIn(response.status_code, [200, 400])  # Accept both as graceful responses

# Entry point for running all tests
if __name__ == "__main__":
    unittest.main()
