import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.domain import Email
import base64

def get_gmail_client(SCOPES):
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  return build("gmail", "v1", credentials=creds)

class GmailService:
    def __init__(self, gmail_client=None):
        if gmail_client is None:
            self.gmail = get_gmail_client(SCOPES=["https://www.googleapis.com/auth/gmail.readonly"])
        else:
            self.gmail = gmail_client

    def get_partial_history(self, start_id):
        history = self.gmail.users().history().list(userId='me', startHistoryId=start_id, historyTypes='messageAdded').execute()

        return history

    def get_history(self, start_id):
        history = self.gmail.users().history().list(userId='me', startHistoryId=start_id, historyTypes='messageAdded').execute()
        return history 

    def initial_gmail_sync(self, max_results):
        pageToken = None
        messages_left = True
        messages = []

        email_ids = []

        # Get messages
        while messages_left:
            resp = self.gmail.users().messages().list(userId="me", pageToken=pageToken, q="label:tidypay-order").execute()

            pageToken = resp.get('nextPageToken')
            messages = resp.get('messages', [])

            print("RAW MESSAGES", messages)

            email_ids.extend([message['id'] for message in messages])

            if not pageToken:
                messages_left = False


        # only fetch last 'max_results' emails
        # >>> test = [1, 2, 3, 4, 5]
        # >>> test[-2:]
        # [4, 5]
        result = []
        for email_id in email_ids[-max_results:]:
            msg = self.get_message(email_id)
            result.append(msg)
                
        return result
                
    def decode_email_body_text_plain(self, msg):
        return base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8")

    def decode_email_body_multipart(self, msg):
        for p in msg["payload"]["parts"]:
            if p["mimeType"] in ["text/plain", "text/html"]:
                data = base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8")
                return data

    def get_message(self, message_id):
        message = self.gmail.users().messages().get(userId='me', id=message_id, format="full").execute()
        
        if "payload" not in message:
            raise ValueError("Payload not found in message")
        
        if message['payload']['mimeType'] == "text/plain":
            body = self.decode_email_body_text_plain(message)
        else:
            body = self.decode_email_body_multipart(message)

        return {**message, **{"email_body": body}}

    def parse_mail(self, data) -> Email:
        print("parsing mail: ", data)
        # Initialize an empty dictionary to hold the extracted information
        extracted_info = {}

        # Extracting the 'headers' section from the email data
        headers = data.get('payload', {}).get('headers', [])
        
        # Define the keys of interest and ensure each is found
        keys_of_interest = ['Date', 'From', 'To', 'Subject']
        found_keys = {key: False for key in keys_of_interest}

        # Loop through each header and extract information if the header name is in our keys of interest
        for header in headers:
            if header.get('name') in keys_of_interest:
                extracted_info[header.get('name')] = header.get('value')
                found_keys[header.get('name')] = True

        # Check if all required keys were found
        if not all(found_keys.values()):
            raise ValueError(f"Missing keys: {found_keys}")

        snippet = data.get('snippet')
        if snippet is None:
            raise ValueError("Snippet not found")

        extracted_info['Snippet'] = snippet

        if not "email_body" in data:
            raise ValueError("Email body not found")

        # check if any of the required keys are missing
        if not extracted_info['Date'] or not extracted_info['From'] or not extracted_info['To'] or not extracted_info['Subject'] or not data["email_body"]:
            raise ValueError("Missing required fields in email")

        if not "TidypayGO kundeordre" in extracted_info['Subject']:
            raise ValueError(f"Email with subject {extracted_info['Subject']} is not a TidypayGO order email, missing 'TidypayGO kundeordre' in subject")

        if not 'historyId' in data:
            raise ValueError("Missing historyId")

        return Email(
            date=extracted_info['Date'],
            reciever=extracted_info['To'],
            sender=extracted_info['From'],
            subject=extracted_info['Subject'],
            body=data["email_body"],
            history_id=data['historyId']
        )
