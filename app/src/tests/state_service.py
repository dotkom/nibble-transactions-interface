import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import unittest
import os
from src.transaction_state_service import TransactionStateService
from src.domain import Transaction

dirname = os.path.dirname(__file__)

class TestStateService(unittest.TestCase):
    def setUp(self):
        self.transactions_file = os.path.join(dirname, "test_transactions.json")
        self.history_id_file = os.path.join(dirname, "test_history_id.json")
        self.state_service = TransactionStateService(transactions_file=self.transactions_file, history_id_file=self.history_id_file)

    def tearDown(self):
        # Clean up by removing the test state files
        if os.path.exists(self.transactions_file):
            os.remove(self.transactions_file)
        if os.path.exists(self.history_id_file):
            os.remove(self.history_id_file)

    def test_add_transactions(self):
        # Prepare test data
        new_transactions = [
            Transaction(id="1", name="Test Transaction", email="email@example.com", amount=100, datetime="2023-04-01", transaction_description="Test Product")
        ]
        result = self.state_service.set_transaction_list(new_transactions)

        # Assertions
        self.assertEqual(result, new_transactions)

    def test_set_last_processed_history_id(self):
        # Prepare test data
        history_id = "12345"
        result = self.state_service.set_last_processed_history_id(history_id)

        # Assertions
        self.assertEqual(result, history_id)

if __name__ == '__main__':
    unittest.main()
