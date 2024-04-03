import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

from src.transaction_service import TransactionService
from src.gmail_service import GmailService
from src.transaction_state_service import TransactionStateService
from src.pubsub_service import PubSubService
from src.sound_service import SoundService

import traceback

# dotenv
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder=os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

pubsub_service = PubSubService()

gmail_service = GmailService()
sound_service = SoundService()

filedir = os.path.dirname(os.path.realpath(__file__))

state_folder = "../state"

if not os.path.exists(state_folder):
    os.makedirs(state_folder)

transactions_file = os.path.join(filedir, f"{state_folder}/transactions.json")
history_id_file = os.path.join(filedir, f"{state_folder}/history_id.txt")

state_service = TransactionStateService(
    transactions_file=transactions_file, 
    history_id_file=history_id_file)

transaction_service = TransactionService(
    gmail_service=gmail_service,
    state_service=state_service,
    sound_service=sound_service,
    max_saved_limit=10
    )

def emit_update(transactions):
    transactions = [transaction.__dict__ for transaction in transactions]
    socketio.emit('update', {'payload': transactions}, namespace='/test')

@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
    try:
        incoming_history_id = pubsub_service.get_history_id(request)
        updated = transaction_service.handle_gmail_push(incoming_history_id)
        emit_update(updated)
    except Exception as e:
        print(traceback.format_exc())
        print("Returning 200 to prevent redelivery", e)

    # Acknowledge the message to prevent redelivery
    return jsonify(success=True)

@app.route('/admin')
def admin():
    return render_template("admin.html")

@socketio.on('connect', namespace='/test')
def test_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

@socketio.on('fullsync', namespace='/test')
def full_sync():
    print("Full sync requested")
    updated = transaction_service.full_sync()
    emit_update(updated)

@app.route('/')
def index():
    transactions = state_service.get_transaction_list()
    return render_template("index.html", transactions=transactions)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080)
