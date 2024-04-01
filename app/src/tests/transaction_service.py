import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import unittest
from src.transaction_state_service import TransactionStateService
from src.domain import Transaction
from unittest.mock import patch, MagicMock
from src.transaction_service import TransactionService
from src.gmail_service import GmailService
from src.transaction_state_service import TransactionStateService
import json

dirname = os.path.dirname(__file__)

def get_test_message():
    with open(os.path.join(dirname, "messages.json")) as f:
        return json.load(f)

class TestTransactionService(unittest.TestCase):
    def setUp(self):
        self.gmail_service = GmailService(gmail_client={})

        self.transactions_file = os.path.join(dirname, "test_transactions.json")
        self.history_id_file = os.path.join(dirname, "test_history_id.json")
        self.state_service = TransactionStateService(transactions_file=self.transactions_file, history_id_file=self.history_id_file)

        self.transaction_service = TransactionService(self.gmail_service, self.state_service)

    def tearDown(self):
        # Clean up by removing the test state files
        if os.path.exists(self.transactions_file):
            os.remove(self.transactions_file)
        if os.path.exists(self.history_id_file):
            os.remove(self.history_id_file)

    def test_add_transactions(self):
        # Prepare mock data and expectations
        existing_transactions = [
            Transaction(order_number="1", name="Test1", email="test1@example.com", amount=100, datetime="2023-04-01", transaction_description="Product1", invoice_number="12345"),
            Transaction(order_number="2", name="Test2", email="test2@example.com", amount=100, datetime="2023-04-01", transaction_description="Product2", invoice_number="12346")
        ]
        self.state_service.set_transaction_list(existing_transactions)

        new_transactions = [
            Transaction(order_number="3", name="Test3", email="test3@example.com", amount=200, datetime="2023-04-03", transaction_description="Product3", invoice_number="12347"),
        ]

        # Call the method under test
        updated_transactions = self.transaction_service.add_transactions(new_transactions, max_saved_limit=1)

        # Assertions
        self.assertEqual(len(updated_transactions), 1)
        self.assertEqual(updated_transactions[0].order_number, "3")

    def test_extract_transaction_data(self):
        with open(os.path.join(dirname, "messages.json")) as f:
            test_message = json.load(f)

        parsed = self.gmail_service.parse_mail(test_message)
        extracted = self.transaction_service.extract_email_info(parsed)

        print(extracted)

if __name__ == '__main__':
    unittest.main()


# class TestStateService(unittest.TestCase):
#     def setUp(self):
#         self.transactions_file = os.path.join(dirname, "test_transactions.json")
#         self.history_id_file = os.path.join(dirname, "test_history_id.json")
#         self.state_service = TransactionStateService(transactions_file=self.transactions_file, history_id_file=self.history_id_file)

#     def tearDown(self):
#         # Clean up by removing the test state files
#         if os.path.exists(self.transactions_file):
#             os.remove(self.transactions_file)
#         if os.path.exists(self.history_id_file):
#             os.remove(self.history_id_file)

#     def test_add_transactions(self):
#         # Prepare test data
#         new_transactions = [
#             Transaction(id="1", name="Test Transaction", email="email@example.com", amount=100, datetime="2023-04-01", product="Test Product")
#         ]
#         result = self.state_service.set_transaction_list(new_transactions)

#         # Assertions
#         self.assertEqual(result, new_transactions)

#     def test_set_last_processed_history_id(self):
#         # Prepare test data
#         history_id = "12345"
#         result = self.state_service.set_last_processed_history_id(history_id)

#         # Assertions
#         self.assertEqual(result, history_id)

# if __name__ == '__main__':
#     unittest.main()
