import os
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

    def get_history(self, start_id):
        if start_id is None:
            return self.gmail.users().history().list(userId='me', historyTypes='messageAdded', startHistoryId=None, maxResults=10).execute()

        history = self.gmail.users().history().list(userId='me', startHistoryId=start_id, historyTypes='messageAdded').execute()
        return history 

    def initial_gmail_sync(self):
        pageToken = None
        messages_left = True
        messages = []

        # Get messages
        while messages_left:
            messages = self.gmail.users().messages().list(userId="me", pageToken=pageToken, q="label:tidypay-order").execute()
            # messages = self.gmail.users().messages().list(userId="me", pageToken=pageToken, labelIds=['tidypay-order']).execute()
            pageToken = messages.get('nextPageToken')
            # do something with the messages! Importing them to your database for example

            result = []
            for message in messages.get('messages', []):
                email_id = message['id']
                msg = self.get_message(email_id)

                result.append(msg)

            if not pageToken:
                messages_left = False
                
        return result
                

    def decode_email_body(self, msg):
        for p in msg["payload"]["parts"]:
            if p["mimeType"] in ["text/plain", "text/html"]:
                data = base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8")
                return data

    def get_message(self, message_id):
        message = self.gmail.users().messages().get(userId='me', id=message_id).execute()
        body = self.decode_email_body(message)

        return {**message, **{"email_body": body}}

    def parse_mail(self, data) -> Email:
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

        return Email(
            date=extracted_info['Date'],
            reciever=extracted_info['To'],
            sender=extracted_info['From'],
            subject=extracted_info['Subject'],
            body=data["email_body"],
        )

# def parse_mail(data) -> Email:
#     # Initialize an empty dictionary to hold the extracted information
#     extracted_info = {}

#     # Extracting the 'headers' section from the email data
#     headers = data.get('payload', {}).get('headers', [])
    
#     # Define the keys of interest and ensure each is found
#     keys_of_interest = ['Date', 'From', 'To', 'Subject']
#     found_keys = {key: False for key in keys_of_interest}

#     # Loop through each header and extract information if the header name is in our keys of interest
#     for header in headers:
#         if header.get('name') in keys_of_interest:
#             extracted_info[header.get('name')] = header.get('value')
#             found_keys[header.get('name')] = True

#     # Check if all required keys were found
#     if not all(found_keys.values()):
#         raise ValueError(f"Missing keys: {found_keys}")

#     snippet = data.get('snippet')
#     if snippet is None:
#         raise ValueError("Snippet not found")

#     extracted_info['Snippet'] = snippet

#     return Email(
#         date=extracted_info['Date'],
#         reciever=extracted_info['To'],
#         sender=extracted_info['From'],
#         subject=extracted_info['Subject'],
#         snippet=extracted_info['Snippet']
#     )



# def get_history(startId):
#     try:
#         messages = gmail.users().history().list(userId='me', startHistoryId=startId, historyTypes='messageAdded').execute()
#         return messages 
#     except Exception as e:
#         print(e)
#         return None

# def get_message(message_id):
#     try:
#         message = gmail.users().messages().get(userId='me', id=message_id).execute()
#         return message
#     except Exception as e:
#         print(e)
#         return None
