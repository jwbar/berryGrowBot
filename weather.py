import requests
import json
import os
import time
import threading
from datetime import datetime

def fetch_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)

        data = response.json()

        # Extracting required fields
        timestamp = data["current"]["dt"]
        formatted_time = datetime.utcfromtimestamp(timestamp).isoformat() + 'Z'  # Convert to ISO 8601 format
        current_data = {
            "temp": data["current"]["temp"],
            "humidity": data["current"]["humidity"],
            "dt": formatted_time,  # Use the formatted time here
        }

        # Check if pws.json exists, if not create it
        if not os.path.exists('pws.json'):
            weather_data_list = []  # Initialize an empty list if the file doesn't exist
        else:
            # Read existing data
            with open('pws.json', 'r') as json_file:
                weather_data_list = json.load(json_file)  # Load the existing data

        # Append the new data
        weather_data_list.append(current_data)

        # Write the updated list back to pws.json
        with open('pws.json', 'w') as json_file:
            json.dump(weather_data_list, json_file, indent=4)

        print("Weather data successfully saved to pws.json")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
    except KeyError as e:
        print(f"Error parsing data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def start_weather_thread(lat, lon, api_key):
    while True:
        fetch_weather_data(lat, lon, api_key)
        time.sleep(1800)  # Sleep for 30 minutes (1800 seconds)

if __name__ == "__main__":
    # Replace these values with your actual latitude, longitude, and API key
    latitude = 52.5200  # Latitude for Berlin
    longitude = 13.4050  # Longitude for Berlin
    api_key = "ce9bc1f8412f08ad0a2bf261b331bc95"  # Your OpenWeatherMap API key

    # Start the weather fetching thread
    weather_thread = threading.Thread(target=start_weather_thread, args=(latitude, longitude, api_key))
    weather_thread.daemon = True  # Daemonize thread
    weather_thread.start()

    # Keep the main program running while the thread does its job
    try:
        while True:
            time.sleep(1)  # Sleep to keep the main thread alive
    except KeyboardInterrupt:
        print("Program terminated by user.")
