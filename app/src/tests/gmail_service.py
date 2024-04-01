import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import unittest
from src.gmail_service import GmailService
import json

dirname = os.path.dirname(__file__)

def get_test_message():
    with open(os.path.join(dirname, "messages.json")) as f:
        return json.load(f)

class TestTransactionService(unittest.TestCase):
    def setUp(self):
        self.gmail_service = GmailService(gmail_client={})

    def test_parse_mail(self):
        # return of get_email
        test_email = get_test_message()

        parsed = self.gmail_service.parse_mail(test_email)

        print(parsed)


if __name__ == '__main__':
    unittest.main()
