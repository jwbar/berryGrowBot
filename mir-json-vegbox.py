from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Path to save the JSON file
VEGGIBOX_FILE_PATH = "../veggibox.json"

@app.route('/veggibox', methods=['POST'])
def update_veggibox_data():
    if request.is_json:
        # Parse the incoming JSON data
        data = request.get_json()

        # Add timestamp to the data
        data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Access specific data (for example: temperature, humidity, soil moisture)
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        soil1 = data.get('soil1')
        soil2 = data.get('soil2')

        # Log the received data
        print(f"Received data: Temperature: {temperature}, Humidity: {humidity}, Soil Moisture 1: {soil1}, Soil Moisture 2: {soil2}")

        # Save the data to a JSON file
        try:
            # If file doesn't exist, create it; otherwise, append the new data
            if not os.path.exists(VEGGIBOX_FILE_PATH):
                with open(VEGGIBOX_FILE_PATH, 'w') as f:
                    json.dump([data], f, indent=4)
            else:
                with open(VEGGIBOX_FILE_PATH, 'r+') as f:
                    file_data = json.load(f)
                    file_data.append(data)
                    f.seek(0)
                    json.dump(file_data, f, indent=4)
        except Exception as e:
            print(f"Error saving data to file: {e}")

        # Optionally, send a response back to the client
        response = {
            "status": "success",
            "message": "Data received and saved successfully"
        }
        return jsonify(response), 200
    else:
        # If the request does not contain JSON data
        response = {
            "status": "error",
            "message": "Invalid data format. Expected JSON."
        }
        return jsonify(response), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
