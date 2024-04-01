from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import time
import threading
import base64
import json
import pprint

import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# dotenv
from dotenv import load_dotenv
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
project_id = os.getenv("TF_VAR_project_id")

def parse_mail(data):
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

    return extracted_info

def get_gmail_client():
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


def get_history(startId):
    try:
        messages = gmail.users().history().list(userId='me', startHistoryId=startId, historyTypes='messageAdded').execute()
        return messages 
    except Exception as e:
        print(e)
        return None

def get_message(message_id):
    try:
        message = gmail.users().messages().get(userId='me', id=message_id).execute()
        return message
    except Exception as e:
        print(e)
        return None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
gmail = get_gmail_client()
latest_history_id = "2109362"

def handle_new_message(_history_id):
    global latest_history_id

    history_id = latest_history_id
    latest_history_id = _history_id

    history = get_history(history_id)

    pprint.pprint(history)

    if history is None or 'history' not in history:
        raise ValueError("No history found")

    for history in history['history']:
        if 'messagesAdded' not in history:
            continue

        for message in history['messagesAdded']:
            if 'INBOX' in message['message']['labelIds']:
                id = message['message']['id']
                print(f"New message: {id}")

                message = get_message(id)

                if message is None:
                    continue

                pprint.pprint(message)

                email = parse_mail(message)

                socketio.emit('new_message', {'message_id': id, "body": email}, namespace='/test')

@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
    # Parse the incoming JSON
    envelope = request.get_json(silent=True)
    if not envelope:
        print("No message received")
        return "No message", 400

    # Extract the message if present
    message = envelope.get('message')
    if not message:
        print("No message found in envelope")
        return "No message found", 400
    
    # Your logic to handle the message goes here
    # For example, printing the message ID and data:
    message_id = message.get('messageId')
    message_data = message.get('data')
    if message_data:
        # Decode the message data from base64
        message_data = base64.b64decode(message_data).decode('utf-8')
        print(f"Received message {message_id} with data: {message_data}")
    else:
        print(f"Received message {message_id} without data")

    # Parse the JSON string to a Python dictionary
    message_data = json.loads(message_data)

    # Now you can correctly access 'historyId'
    history_id = message_data['historyId']

    try:
        handle_new_message(history_id)
    except Exception as e:
        print(f"Error handling message: {e}")

    # Acknowledge the message to prevent redelivery
    return jsonify(success=True)



def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(1)  # Sleep for 1 second
        count += 1
        socketio.emit('newnumber', {'number': count}, namespace='/test')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    threading.Thread(target=background_thread).start()
    socketio.run(app, debug=True, port=8080)
