import sys
import json
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pprint import pprint
from src.domain import Transaction, Email
from src.gmail_service import GmailService
from src.transaction_state_service import TransactionStateService
from src.sound_service import SoundService
import re
import traceback

class TransactionService:
    def __init__(self, gmail_service: GmailService, state_service: TransactionStateService, sound_service: SoundService, max_saved_limit: int = 10):
        self.gmail_service = gmail_service
        self.state_service = state_service
        self.sound_service = sound_service
        self.max_saved_limit = max_saved_limit

    def add_transactions(self, incoming: list[Transaction], max_saved_limit: int) -> list[Transaction]:
        transactions = self.state_service.get_transaction_list()

        added_transactions = False

        for transaction in incoming:
            if transaction.order_number in [t.order_number for t in transactions]:
                # TODO: Send notification on slack/discord that something went wrong. this should not happen
                print(f"Transaction with id {transaction.order_number} already exists \n {transaction.name}-{transaction.transaction_description}-{transaction.datetime} not added")
                continue

            transactions.append(transaction)
            added_transactions = True

        transactions = transactions[-max_saved_limit:]

        updated = self.state_service.set_transaction_list(transactions)

        if added_transactions:
            self.sound_service.play()

        return updated

    def extract_added_emails(self, history: dict) -> list[dict]:
        res = []
        for h in history:
            if 'messagesAdded' not in h:
                continue

            for message in h['messagesAdded']:
                if 'Label_661192541137989669' in message['message']['labelIds']:
                    res.append(message)
        return res

    def extract_email_info(self, email: Email) -> Transaction:
        print("Extracting email info", email)
        order_number = re.search(r'Ordrenummer:\s+(\d+)', email.body).group(1)
        invoice_number = re.search(r'Fakturanummer:\s+(\d+)', email.body).group(1)
        datetime = re.search(r'Dato og tid:\s+([-\d:\s]+)', email.body).group(1)
        name_email_match = re.search(r'Kunde:\s+(.*?)\s+\(\s*(.*?)\s*/', email.body)
        name, email_addr = name_email_match.group(1), name_email_match.group(2)
        amount = int(float(re.search(r'Sum ordre ink MVA kr\s+(\d+.\d+)', email.body).group(1)))
        product_description = re.search(r'(\d+ stk [^\=]+=\s+kr\s+\d+.\d+)', email.body).group(1)
        return Transaction(order_number=order_number, name=name, email=email_addr, amount=amount, datetime=datetime, transaction_description=product_description, invoice_number=invoice_number, history_id=email.history_id)

    def fetch_detailed_emails(self, added_emails) -> list[dict]:
        emails = []
        for message in added_emails:
            id = message['message']['id']
            try:
                message = self.gmail_service.get_message(id)
                print(f"Message {id} fetched", message)
                emails.append(message)
            except Exception as e:
                print(f"Failed to fetch email {id}")
                print(traceback.format_exc())
                # write email to file with email name
                with open(f"email_{id}.json", "w") as f:
                    json.dump(message, f)

                continue

        return emails

    def parse_emails(self, raw_emails) -> list[Email]:
        emails = []
        for m in raw_emails:
            try:
                email = self.gmail_service.parse_mail(m)
            except Exception as e:
                print(f"Failed to parse email {m}")
                print(traceback.format_exc())
                continue


            emails.append(email)

        return emails

    def get_parsed_emails(self, unprocessed_history):
        print("Unprocessed history", unprocessed_history)
        if 'history' not in unprocessed_history:
            raw_added_emails = [] # No new emails
        else:
            raw_added_emails = self.extract_added_emails(unprocessed_history['history'])

        new_emails = self.fetch_detailed_emails(raw_added_emails)
        parsed_emails = list(map(lambda email: self.parse_emails(email), new_emails))
        
        return parsed_emails

    def handle_gmail_push(self, new_history_id: str) -> list[Transaction]:
        last_processed_history_id = self.state_service.get_last_processed_history_id()

        print(f"Last processed history id: {last_processed_history_id}")

        if last_processed_history_id is None:
            return self.full_sync()

        unprocessed_history = self.gmail_service.get_history(last_processed_history_id)

        print("Unprocessed history", unprocessed_history)
        parsed_emails = self.get_parsed_emails(unprocessed_history)
        print("emails", parsed_emails)

        transactions = self.extract_emails(parsed_emails)
        updated_transactions = self.add_transactions(transactions, self.max_saved_limit)

        self.state_service.set_last_processed_history_id(f"{new_history_id}")

        return updated_transactions

    def extract_emails(self, emails: list[Email]) -> list[Transaction]:
        transactions = []
        for email in emails:
            try:
                transaction = self.extract_email_info(email)
                transactions.append(transaction)
            except Exception as e:
                print(f"Failed to extract email info from email {email}")
                print(traceback.format_exc())
                continue
        return transactions

    def full_sync(self):
        detailed_emails = self.gmail_service.initial_gmail_sync(max_results=self.max_saved_limit)
        print(f"Initial sync found {len(detailed_emails)} emails")
        parsed_emails = list(map(lambda email: self.gmail_service.parse_mail(email), detailed_emails))
        print(f"Initial sync parsed {len(parsed_emails)} emails")
        transactions = self.extract_emails(parsed_emails)
        print(f"Initial sync extracted {len(transactions)} transactions from emails")

        # clear out existing transactions
        self.state_service.set_transaction_list([])

        updated_transactions = self.add_transactions(transactions, self.max_saved_limit)
        print(f"Initial sync updated {len(updated_transactions)} transactions from file")

        self.state_service.set_last_processed_history_id(updated_transactions[-1].history_id)

        return updated_transactions


if __name__ == '__main__':
    import os
    dirname = os.path.dirname(__file__)
    gmail_service = GmailService()
    transactions_file = os.path.join(dirname, "transactions.json")
    history_id_file = os.path.join(dirname, "history_id.txt")

    state_service = TransactionStateService(transactions_file=transactions_file, history_id_file=history_id_file)

    transaction_service = TransactionService(gmail_service, state_service, max_saved_limit=10)

    # detailed_emails = gmail_service.initial_gmail_sync()
    # parsed_emails = list(map(lambda email: gmail_service.parse_mail(email), detailed_emails))
    # transactions = list(map(lambda email: transaction_service.extract_email_info(email), parsed_emails))
    # updated_transactions = transaction_service.add_transactions(transactions, transaction_service.max_saved_limit)

    # transaction_service.state_service.set_last_processed_history_id(detailed_emails[0]['historyId'])

    updated = transaction_service.full_sync()
    print(updated)