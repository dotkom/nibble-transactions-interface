import base64
import json

class PubSubService:
    def get_history_id(self, request):
        # Parse the incoming JSON
        envelope = request.get_json(silent=True)
        if not envelope:
            print("No message received")
            raise ValueError("No message received")

        # Extract the message if present
        message = envelope.get('message')
        if not message:
            print("No message found in envelope")
            raise ValueError("No message found in envelope")
        
        message_data = message.get('data')
        if message_data:
            # Decode the message data from base64
            message_data = base64.b64decode(message_data).decode('utf-8')
            message_data = json.loads(message_data)

        history_id = message_data['historyId']

        return history_id