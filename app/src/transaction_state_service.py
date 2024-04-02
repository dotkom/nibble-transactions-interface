import json
import os
from src.domain import Transaction

class TransactionStateService:
    def __init__(self, transactions_file, history_id_file):
        self.transactions_file = transactions_file
        self.history_id_file = history_id_file

        if not os.path.exists(transactions_file):
            with open(transactions_file, "w") as transactions:
                json.dump({"data": []}, transactions)

        if not os.path.exists(history_id_file):
            with open(history_id_file, "w") as history_id_file:
                history_id_file.write("")

    def get_transaction_list(self) -> list[Transaction]:
        with open(self.transactions_file, "r") as transactions:
            data = json.load(transactions)
            return [Transaction(**transaction) for transaction in data['data']]

    def set_transaction_list(self, transactions: list[Transaction]) -> list[Transaction]:
        with open(self.transactions_file, "w") as transactions_file:
            json.dump({"data": [transaction.__dict__ for transaction in transactions]}, transactions_file)

        return self.get_transaction_list()

    def get_last_processed_history_id(self) -> str:
        if not os.path.exists(self.history_id_file):
            return None
        
        with open(self.history_id_file, "r") as history_id_file:
            result = history_id_file.read()

            if result == "0" or result == "" or result == 0:
                return None

            return result
    
    def set_last_processed_history_id(self, history_id: str) -> str:
        with open(self.history_id_file, "w") as history_id_file:
            history_id_file.write(history_id)

        return self.get_last_processed_history_id()

