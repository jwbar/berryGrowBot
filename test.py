import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
relay_pin = 4
GPIO.setup(relay_pin, GPIO.OUT)

def control_relay():
    while True:
        command = input("Enter 'on' to turn the relay on or 'off' to turn the relay off (type 'exit' to quit): ").strip().lower()
        if command == 'on':
            GPIO.output(relay_pin, GPIO.HIGH)
            print("Relay turned ON")
        elif command == 'off':
            GPIO.output(relay_pin, GPIO.LOW)
            print("Relay turned OFF")
        elif command == 'exit':
            print("Exiting...")
            break
        else:
            print("Invalid command. Please enter 'on' or 'off'.")
        time.sleep(1)

try:
    control_relay()
finally:
    GPIO.cleanup()
    print("GPIO cleanup done.")
