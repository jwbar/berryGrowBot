from flask import Flask, render_template_string
import Adafruit_DHT
import RPi.GPIO as GPIO
import time

app = Flask(__name__)


# Define the sensor type and the GPIO pins
DHT_SENSOR = Adafruit_DHT.DHT11  # Existing DHT sensor for the tent
DHT_PIN = 2  # GPIO pin for the existing DHT sensor

# New second DHT sensor for general room temperature
DHT_SENSOR_2 = Adafruit_DHT.DHT11
DHT_PIN_2 = 10  # GPIO pin for the second DHT sensor (use an unused GPIO pin)

SOIL_SENSOR_PIN = 3  # GPIO pin for the soil moisture sensor

# Set up the GPIO pin for the soil moisture sensor (Digital output)
SOIL_SENSOR_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOIL_SENSOR_PIN, GPIO.IN)

# HTML content
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to the Grow Hub</title>
    <style>
        body {
            background-color: #1a1a1a; /* Dark background */
            color: #f1f1f1; /* Light text color */
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
            color: #27ae60; /* Green color for the header */
            margin-bottom: 20px;
        }
        .ascii-art {
            font-size: 12px;
            line-height: 1;
            margin-bottom: 20px;
        }
        .details {
            font-size: 16px;
            color: #7f8c8d; /* Light gray color for the details */
        }
        .humidity-status, .soil-status {
            width: 20px;
            height: 20px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="ascii-art">
        <pre>
            Welcome to the Machine!
            |
            |.|
            |.|
           |\./|
           |\./|
.           |\./|               .
\^.\        |\\.//|          /.^/
\--.|\      |\\.//|       /|.--/
\--.| \     |\\.//|    / |.--/
\---.|\     |\./|    /|.---/
   \--.|\  |\./|  /|.--/
      \ .\  |.|  /. /
_ -_^_^_^_-  \ \\ // /  -_^_^_^_- _
- -/_/_/- ^ ^  |  ^ ^ -\_\_\- -


In the garden of existence,
Harmony blooms with each mindful touch,
Tending to the earth, we nurture the soul.
        </pre>
    </div>
    <h2>Welcome to the Grow Hub</h2>
    <p class="details">
        Time: {{ current_time }}<br>
        Date: {{ current_date }}<br>
        Temperature: {{ temperature }} °C<br>
        Humidity: {{ humidity }}% <span class="humidity-status" style="background-color: {{ humidity_color }};"></span><br><br>
        Soil is {{ soil_status }} <span class="soil-status" style="background-color: {{ soil_color }};"></span>
    </p>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        # Get the current time and date
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%Y-%m-%d")

        # Read the temperature and humidity from the DHT sensor
        humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)

        if humidity is None or temperature is None:
            humidity = "N/A"
            temperature = "N/A"
            humidity_color = "#7f8c8d"  # Gray color for N/A
        else:
            # Determine the color based on humidity levels
            if humidity < 65:
                humidity_color = "#27ae60"  # Green
            elif 65 <= humidity <= 70:
                humidity_color = "#f39c12"  # Orange
            else:
                humidity_color = "#e74c3c"  # Red

            # Format temperature and humidity to 2 decimal places
            temperature = f"{temperature:.2f}"
            humidity = f"{humidity:.2f}"

        # Read the digital value from the soil moisture sensor (Inverted logic)
        if GPIO.input(SOIL_SENSOR_PIN) == GPIO.LOW:
            soil_status = "wet"
            soil_color = "#27ae60"  # Green
        else:
            soil_status = "dry"
            soil_color = "#e74c3c"  # Red

        return render_template_string(html_content, current_time=current_time, current_date=current_date,
                                      temperature=temperature, humidity=humidity, humidity_color=humidity_color,
                                      soil_status=soil_status, soil_color=soil_color)
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()  # Clean up GPIO on exit
#this one