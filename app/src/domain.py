from dataclasses import dataclass

@dataclass
class Transaction:
    order_number: str
    name: str
    email: str
    amount: int
    datetime: str
    transaction_description: str
    invoice_number: str = None


@dataclass
class Email:
    date: str
    reciever: str
    sender: str
    subject: str
    body: str