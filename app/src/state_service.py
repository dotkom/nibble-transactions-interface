import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from src.domain import Transaction

class StateService:
    def __init__(self, state_file):
        self.state_file = state_file

        if not os.path.exists(state_file):
            with open(state_file, "w") as state_file_fp:
                json.dump({"transactions": [], "last_history_id": None, "processed_email_ids": []}, state_file_fp)

        # check if file is corrupted, if so, recreate it
        try:
            self.get_transaction_list()
        except Exception as e:
            print(f"State file {state_file} is corrupted, recreating it")
            with open(state_file, "w") as state_file_fp:
                json.dump({"transactions": [], "last_history_id": None, "processed_email_ids": []}, state_file_fp)

    
    def _get_full_file(self):
        with open(self.state_file, "r") as state_file_fp:
            return json.load(state_file_fp)

    def _get_property(self, property_name: str):
        with open(self.state_file, "r") as fp:
            data = json.load(fp)
            return data[property_name]

    def _update_property(self, property_name: str, value):
        contents = self._get_full_file()
        contents.update({property_name: value})
        print(f"Updating {property_name} to {value}")
        with open(self.state_file, "w") as transactions_file:
            json.dump(contents, transactions_file, indent=4)
        
        return self._get_property(property_name)

    def get_transaction_list(self) -> list[Transaction]:
        transactions = self._get_property("transactions")
        return [Transaction(**transaction) for transaction in transactions]

    def set_transaction_list(self, transactions: list[Transaction]) -> list[Transaction]:
        updated =  self._update_property("transactions", [transaction.__dict__ for transaction in transactions])
        return [Transaction(**transaction) for transaction in updated]

    def get_last_processed_history_id(self) -> str:
        return self._get_property("last_history_id")
    
    def set_last_processed_history_id(self, history_id: str) -> str:
        return self._update_property("last_history_id", history_id)
    
    def get_processed_email_ids(self) -> list[str]:
        return self._get_property("processed_email_ids")
        
    def set_processed_email_ids(self, email_ids: list[str]):
        return self._update_property("processed_email_ids", email_ids)


dir = os.path.dirname(__file__)

if __name__ == "__main__":
    state_service = StateService("test_state.json")

    transaction = Transaction(name="Test Transaction", email="test@gmail.com" , amount=100, datetime="2023-04-01", transaction_description="Test Product", history_id="12345", invoice_number="12345", order_number="12345")

    state_service.set_transaction_list([transaction])

    print(state_service.get_transaction_list())

    last_history_id = state_service.get_last_processed_history_id()

    print(f"Last history id: {last_history_id}")

    state_service.set_last_processed_history_id("12345")

    print(state_service.get_last_processed_history_id())

    state_service.set_processed_email_ids(["12345", "67890"])

    print(state_service.get_processed_email_ids())




