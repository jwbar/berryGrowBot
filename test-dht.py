import Adafruit_DHT

# Define the sensor type (DHT11 or DHT22)
sensor = Adafruit_DHT.DHT11  # Change to DHT11 if you're using a DHT11 sensor

# GPIO pin assignments
inside_pin = 2
outside_pin = 10

def read_sensor_data(pin):
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        print("Failed to retrieve data from sensor")
        return None, None

def main():
    while True:
        choice = input("Enter 'inside' to read from inside sensor (GPIO 2) or 'outside' to read from outside sensor (GPIO 10): ").strip().lower()
        
        if choice == 'inside':
            pin = inside_pin
        elif choice == 'outside':
            pin = outside_pin
        else:
            print("Invalid choice. Please enter 'inside' or 'outside'.")
            continue
        
        temperature, humidity = read_sensor_data(pin)
        
        if temperature is not None and humidity is not None:
            print(f"Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%")
        
        # Continue reading or exit
        another = input("Do you want to read from another sensor? (yes/no): ").strip().lower()
        if another != 'yes':
            break

if __name__ == "__main__":
    main()
