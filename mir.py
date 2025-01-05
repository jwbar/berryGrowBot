from flask import Flask, render_template_string, request, redirect, url_for
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import json
import os
import requests
import logging
import threading  # Add this import
import time


app = Flask(__name__)



# Define the sensor type and the GPIO pins
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 2  # GPIO pin for DHT11 sensor
DHT_SENSOR_2 = Adafruit_DHT.DHT11
DHT_PIN_2 = 10  # GPIO pin for the second DHT11 sensor

SOIL_SENSOR_PIN = 3  # GPIO pin for the soil moisture sensor

# Relay GPIO pins
RELAY_1_PIN = 4  # Relay channel 1 (Lights)
RELAY_2_PIN = 17  # Relay channel 2 (Fans)
RELAY_3_PIN = 27  # Relay channel 3 (Dehumidifier)
RELAY_4_PIN = 22  # Relay channel 4 (Water Pump)

# Path to the vegbox.json and kcontainer.json files
VEGBOX_JSON_PATH = "/home/jay/veggibox.json"
KCONTAINER_JSON_PATH = "/home/jay/kcontainer.json"
PWS_JSON_PATH = "/home/jay/pws.json"

# Admin password
ADMIN_PASSWORD = "admin123"

# Telegram bot token and chat ID
BOT_TOKEN = '7536315323:AAFsYEuyhDIv6_UP_8DhbDrUtks9gcNwm_Q'
CHAT_ID = '6732532260'



# Function to send Telegram message
def send_telegram_message(message):
    """Send a message to a Telegram chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Message sent successfully")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOIL_SENSOR_PIN, GPIO.IN)
GPIO.setup(RELAY_1_PIN, GPIO.OUT)
GPIO.setup(RELAY_2_PIN, GPIO.OUT)
GPIO.setup(RELAY_3_PIN, GPIO.OUT)
GPIO.setup(RELAY_4_PIN, GPIO.OUT)

# Initialize relays to off state
GPIO.output(RELAY_1_PIN, GPIO.HIGH)
GPIO.output(RELAY_2_PIN, GPIO.HIGH)
GPIO.output(RELAY_3_PIN, GPIO.HIGH)
GPIO.output(RELAY_4_PIN, GPIO.HIGH)

# Define previous relay states globally
previous_relay_states = {
    'relay_1': GPIO.HIGH,
    'relay_2': GPIO.HIGH,
    'relay_3': GPIO.HIGH,
    'relay_4': GPIO.HIGH
}

# Setup logging
logging.basicConfig(level=logging.DEBUG)


# Relay control logic with state tracking
def control_relays():
    global previous_relay_states  # Access the global dictionary
    while True:
        current_hour = int(time.strftime("%H"))
        logging.debug(f"Current Hour: {current_hour}")

        # Relay 1 and Relay 2: Turn on from 21:00 to 09:00
        if 21 <= current_hour or current_hour < 9:
            if previous_relay_states['relay_1'] != GPIO.LOW:
                GPIO.output(RELAY_1_PIN, GPIO.LOW)  # Turn on Relay 1 (Lights)
                send_telegram_message("Relay 1 (Lights) turned on for night cycle.")
                previous_relay_states['relay_1'] = GPIO.LOW

            if previous_relay_states['relay_2'] != GPIO.LOW:
                GPIO.output(RELAY_2_PIN, GPIO.LOW)  # Turn on Relay 2 (Fans)
                send_telegram_message("Relay 2 (Fans) turned on for night cycle.")
                previous_relay_states['relay_2'] = GPIO.LOW
        else:
            if previous_relay_states['relay_1'] != GPIO.HIGH:
                GPIO.output(RELAY_1_PIN, GPIO.HIGH)  # Turn off Relay 1
                send_telegram_message("Relay 1 (Lights) turned off for day cycle.")
                previous_relay_states['relay_1'] = GPIO.HIGH

            # Relay 2: Turn on if temperature is above 30°C when Relay 1 is off
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if temperature is not None and temperature > 30:
                if previous_relay_states['relay_2'] != GPIO.LOW:
                    GPIO.output(RELAY_2_PIN, GPIO.LOW)  # Turn on Relay 2 (Fans)
                    send_telegram_message("Relay 2 (Fans) turned on due to high temperature.")
                    previous_relay_states['relay_2'] = GPIO.LOW
            else:
                if previous_relay_states['relay_2'] != GPIO.HIGH:
                    GPIO.output(RELAY_2_PIN, GPIO.HIGH)  # Turn off Relay 2
                    send_telegram_message("Relay 2 (Fans) turned off.")
                    previous_relay_states['relay_2'] = GPIO.HIGH

        # Relay 3: Turn on if humidity is above 70%
        humidity, _ = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
        if humidity is not None and humidity > 70:
            if previous_relay_states['relay_3'] != GPIO.LOW:
                GPIO.output(RELAY_3_PIN, GPIO.LOW)  # Turn on Relay 3 (Dehumidifier)
                send_telegram_message("Relay 3 (Dehumidifier) turned on due to high humidity.")
                previous_relay_states['relay_3'] = GPIO.LOW
        else:
            if previous_relay_states['relay_3'] != GPIO.HIGH:
                GPIO.output(RELAY_3_PIN, GPIO.HIGH)  # Turn off Relay 3
                send_telegram_message("Relay 3 (Dehumidifier) turned off.")
                previous_relay_states['relay_3'] = GPIO.HIGH

        # Relay 4: Turn on for 5 minutes when soil is dry
        if GPIO.input(SOIL_SENSOR_PIN) == GPIO.HIGH:  # Dry soil
            if previous_relay_states['relay_4'] != GPIO.LOW:
                GPIO.output(RELAY_4_PIN, GPIO.LOW)  # Turn on Water Pump
                send_telegram_message("Relay 4 (Water Pump) turned on due to dry soil.")
                logging.debug("Relay 4 turned ON due to dry soil.")
                time.sleep(300)  # Keep the pump on for 5 minutes
                GPIO.output(RELAY_4_PIN, GPIO.HIGH)  # Turn off Water Pump
                send_telegram_message("Relay 4 (Water Pump) turned off after watering.")
                previous_relay_states['relay_4'] = GPIO.HIGH

        # Sleep for 1 minute before checking conditions again
        time.sleep(60)

# Start the relay control in a separate thread
threading.Thread(target=control_relays).start()

# Function to read the latest data from pws_data.json
def read_latest_pws_data():
    if os.path.exists(PWS_JSON_PATH):
        with open(PWS_JSON_PATH, 'r') as f:
            data = json.load(f)
            if data:
                return data[-1]  # Get the latest (last) entry
    return None
# Function to read the latest data from vegbox.json
def read_latest_vegbox_data():
    if os.path.exists(VEGBOX_JSON_PATH):
        with open(VEGBOX_JSON_PATH, 'r') as f:
            data = json.load(f)
            if data:
                return data[-1]  # Get the latest (last) entry
    return None

# Function to read the latest data from kcontainer.json
def read_latest_kcontainer_data():
    if os.path.exists(KCONTAINER_JSON_PATH):
        with open(KCONTAINER_JSON_PATH, 'r') as f:
            data = json.load(f)
            if data:
                return data[-1]  # Get the latest (last) entry
    return None

# CSS for all pages
style = """
<style>
    body {
        background-color: #1a1a1a;
        color: #f1f1f1;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100vh;
    }
    h2 {
        color: #27ae60;
        margin-bottom: 20px;
    }
    .ascii-art {
        font-size: 12px;
        line-height: 1;
        margin-bottom: 20px;
    }
    a {
        color: orange;
       }

    .details {
        font-size: 16px;
        color: #7f8c8d;
    }
    .humidity-status, .soil-status, .light-status {
        width: 20px;
        height: 20px;
        display: inline-block;
    }
    .light-off {
        border: 2px solid black;
    }
    .light-on {
        background-color: yellow;
    }
    .data-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    .vegbox-data, .kcontainer-data {
        font-size: 14px;
        border: 1px solid #f1f1f1;
        padding: 10px;
        width: 45%;
        margin: 10px;
    }
    @media (min-width: 768px) {
        .data-container {
            flex-direction: row;
            justify-content: space-around;
        }
    }
    input {
        padding: 5px;
        margin: 5px;
    }
</style>
"""

# HTML content for the home page
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to the Grow Hub</title>
    """ + style + """
</head>
<body>
    <div class="ascii-art">
        <pre>
            Welcome to the Machine!

             |
            |.|
            |.|
           |\\./|
           |\\./|
.           |\\./|               .
\\^.\        |\\\\.//|          /.^/
\\--.|\\      |\\\\.//|       /|.--/
\\--.| \\     |\\\\.//|    / |.--/
\\---.|\\     |\\./|    /|.---/
   \\--.|\\  |\\./|  /|.--/
      \\ .\\  |.|  /. /
_ -_^_^_^_-  \\ \\\\ // /  -_^_^_^_- _
- -/_/_/- ^ ^  |  ^ ^ -\\_\\_\\- -

In the garden of existence,
Harmony blooms with each mindful touch,
Tending to the earth, we nurture the soul.
        </pre>
    </div>
    <h2>Welcome to the Grow Hub</h2>
       <p class="details">
        Time: {{ current_time }}<br>
        Date: {{ current_date }}<br>
        Room Temperature: {{ room_temperature }} °C<br>
        Room Humidity: {{ room_humidity }}%<br><br>
    </p>
        <h3>BloomBox</h3>
    <p class="details">
        Temperature: {{ temperature }} °C<br>
        Humidity: {{ humidity }}% <span class="humidity-status" style="background-color: {{ humidity_color }};"></span><br><br>
        Soil is {{ soil_status }} <span class="soil-status" style="background-color: {{ soil_color }};"></span><br><br>
        Light is {{ light_status }} <span class="light-status {{ light_class }}"></span><br><br>
        Fans are {{ relay_2_status }}<br><br>
    </p>

    <div class="data-container">
    <div class="pws_data">
        <h3>OutsideTemps</h3>
        {% if pws_data %}
            <p>Temperature: {{ pws_data.temp }} °C</p>
            <p>Humidity: {{ pws_data.humidity }} %</p>
            <p>Timestamp: {{ pws_data.dt }}</p>
        {% else %}
            <p>No data available from the weather station.</p>
        {% endif %}
    </div>
</div>

    <div class="data-container">
        <div class="vegbox-data">
            <h3>VegBox Status</h3>
            {% if vegbox %}
                <p>Temperature: {{ vegbox.temperature }} °C</p>
                <p>Humidity: {{ vegbox.humidity }} %</p>
                <p>Soil 1: {{ vegbox.soil1 }} </p>
                <p>Soil 2: {{ vegbox.soil2 }} </p>
                <p>Timestamp: {{ vegbox.timestamp }}</p>
            {% else %}
                <p>No data available from veggibox.json.</p>
            {% endif %}
        </div>

        <div class="kcontainer-data">
            <h3>Katari Farms - Container</h3>
            {% if kcontainer %}
                <p>Temperature: {{ kcontainer.temperature }} °C</p>
                <p>Humidity: {{ kcontainer.humidity }} %</p>
                <p>Timestamp: {{ kcontainer.timestamp }}</p>
            {% else %}
                <p>No data available from kcontainer.json.</p>
            {% endif %}
        </div>
    </div>
    <a href="/login">Admin Control</a>
</body>
</html>
"""
@app.route('/vegbox', methods=['GET'])
def vegbox():
    # Replace with the ESP32's local IP and port if needed
    esp32_url = 'http://192.168.2.177'  # Internal IP of the ESP32
    
    # Forward GET request to ESP32
    if request.method == 'GET':
        esp32_response = requests.get(esp32_url)
        return esp32_response.content, esp32_response.status_code, esp32_response.headers.items()

# Route for the home page
@app.route('/')
def home():
    current_time = time.strftime("%H:%M:%S")
    current_date = time.strftime("%Y-%m-%d")
    
    # Read sensor data from the DHT sensor on pin 2
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    room_humidity, room_temperature = Adafruit_DHT.read(DHT_SENSOR_2, DHT_PIN_2)

    # Process temperature and humidity from pin 2 (main sensor)
    if humidity is None or temperature is None:
        humidity = "N/A"
        temperature = "N/A"
        humidity_color = "#7f8c8d"
    else:
        humidity_color = "#27ae60" if humidity < 65 else "#f39c12" if 65 <= humidity <= 70 else "#e74c3c"
        temperature = f"{temperature:.2f}"
        humidity = f"{humidity:.2f}"

    # Read room temperature and humidity for comparison (from pin 10)
    if room_humidity is None or room_temperature is None:
        room_humidity = "N/A"
        room_temperature = "N/A"
    else:
        room_humidity = f"{room_humidity:.2f}"
        room_temperature = f"{room_temperature:.2f}"

    # Read the soil sensor status
    soil_status = "wet" if GPIO.input(SOIL_SENSOR_PIN) == GPIO.LOW else "dry"
    soil_color = "#27ae60" if soil_status == "wet" else "#e74c3c"

    # Relay status (Lights, Fans)
    light_class = "light-on" if GPIO.input(RELAY_1_PIN) == GPIO.LOW else "light-off"
    relay_2_status = "on" if GPIO.input(RELAY_2_PIN) == GPIO.LOW else "off"

    # Read latest data from vegbox and kcontainer JSON files
    pws_data = read_latest_pws_data()
    vegbox_data = read_latest_vegbox_data()
    kcontainer_data = read_latest_kcontainer_data()

    return render_template_string(html_content, current_time=current_time, current_date=current_date,
                                  room_temperature=room_temperature, room_humidity=room_humidity,
                                  temperature=temperature, humidity=humidity, humidity_color=humidity_color,
                                  soil_status=soil_status, soil_color=soil_color, light_status=light_class,
                                  relay_2_status=relay_2_status,pws_data=pws_data, vegbox=vegbox_data, kcontainer=kcontainer_data)

# HTML content for the admin page
admin_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Control Panel</title>
    """ + style + """
</head>
<body>
    <h2>Admin Control Panel</h2>
    <form method="post">
        <button name="relay_1" value="Turn On">Turn On Lights</button>
        <button name="relay_1" value="Turn Off">Turn Off Lights</button><br><br>
        <button name="relay_2" value="Turn On">Turn On Fans</button>
        <button name="relay_2" value="Turn Off">Turn Off Fans</button><br><br>
        <button name="relay_3" value="Turn On">Turn On Dehumidifier</button>
        <button name="relay_3" value="Turn Off">Turn Off Dehumidifier</button><br><br>
        <button name="relay_4" value="Turn On">Turn On Water Pump</button>
        <button name="relay_4" value="Turn Off">Turn Off Water Pump</button><br><br>
    </form>
    <div class="data-container">
     <a href="http://mir1.hopto.org:5050">VegBox-Control</a>
      <a href="http://mir1.hopto.org:5000"> MainPage</a>
      </div>
</body>
</html>
"""

# Route for the admin control page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'relay_1' in request.form:
            state = "on" if request.form['relay_1'] == 'Turn On' else "off"
            GPIO.output(RELAY_1_PIN, GPIO.LOW if state == "on" else GPIO.HIGH)
            send_telegram_message(f"Relay 1 (Lights) turned {state}.")
        if 'relay_2' in request.form:
            state = "on" if request.form['relay_2'] == 'Turn On' else "off"
            GPIO.output(RELAY_2_PIN, GPIO.LOW if state == "on" else GPIO.HIGH)
            send_telegram_message(f"Relay 2 (Fans) turned {state}.")
        if 'relay_3' in request.form:
            state = "on" if request.form['relay_3'] == 'Turn On' else "off"
            GPIO.output(RELAY_3_PIN, GPIO.LOW if state == "on" else GPIO.HIGH)
            send_telegram_message(f"Relay 3 (Dehumidifier) turned {state}.")
        if 'relay_4' in request.form:
            state = "on" if request.form['relay_4'] == 'Turn On' else "off"
            GPIO.output(RELAY_4_PIN, GPIO.LOW if state == "on" else GPIO.HIGH)
            send_telegram_message(f"Relay 4 (Water Pump) turned {state}.")

    return render_template_string(admin_html)

# HTML content for the login page
login_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    """ + style + """
</head>
<body>
    <h2>Admin Login</h2>
    <form method="post">
        <label for="password">Password:</label>
        <input type="password" id="password" name="password">
        <input type="submit" value="Login">
    </form>
</body>
</html>
"""

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            return redirect(url_for('admin'))
        else:
            return "Incorrect password!", 403
    return render_template_string(login_html)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()
