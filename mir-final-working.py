from flask import Flask, render_template_string, request, redirect, url_for
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import json
import os
import requests

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
VEGBOX_JSON_PATH = "/home/jay/vegbox.json"
KCONTAINER_JSON_PATH = "/home/jay/kcontainer.json"

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
        Temperature: {{ temperature }} °C<br>
        Humidity: {{ humidity }}% <span class="humidity-status" style="background-color: {{ humidity_color }};"></span><br><br>
        Soil is {{ soil_status }} <span class="soil-status" style="background-color: {{ soil_color }};"></span><br><br>
        Light is {{ light_status }} <span class="light-status {{ light_class }}"></span><br><br>
        Fans are {{ relay_2_status }}<br><br>
    </p>
    <div class="data-container">
        <div class="vegbox-data">
            <h3>VegBox Status</h3>
            {% if vegbox %}
                <p>Temperature: {{ vegbox.temperature }} °C</p>
                <p>Humidity: {{ vegbox.humidity }} %</p>
                <p>Timestamp: {{ vegbox.timestamp }}</p>
            {% else %}
                <p>No data available from vegbox.json.</p>
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
    vegbox_data = read_latest_vegbox_data()
    kcontainer_data = read_latest_kcontainer_data()

    return render_template_string(html_content, current_time=current_time, current_date=current_date,
                                  room_temperature=room_temperature, room_humidity=room_humidity,
                                  temperature=temperature, humidity=humidity, humidity_color=humidity_color,
                                  soil_status=soil_status, soil_color=soil_color, light_status=light_class,
                                  relay_2_status=relay_2_status, vegbox=vegbox_data, kcontainer=kcontainer_data)

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
