from dataclasses import dataclass, asdict

@dataclass
class Transaction:
    order_number: str
    name: str
    email: str
    amount: int
    datetime: str
    transaction_description: str
    invoice_number: str
    history_id: str
    email_id: str

@dataclass
class Email:
    date: str
    reciever: str
    sender: str
    subject: str
    body: str
    history_id: str
    email_id: str

