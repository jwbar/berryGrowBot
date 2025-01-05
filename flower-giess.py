import RPi.GPIO as GPIO
import time

# GPIO setup
relay_pin = 22  # Change this to the GPIO pin number you want to control
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin, GPIO.OUT)

def run_relay():
    for i in range(5):  # Repeat the process 5 times
        print(f"Cycle {i+1}: Turning on the relay")
        GPIO.output(relay_pin, GPIO.HIGH)  # Turn the GPIO on
        time.sleep(60)  # Keep it on for 1 minute (60 seconds)
        
        print(f"Cycle {i+1}: Turning off the relay")
        GPIO.output(relay_pin, GPIO.LOW)  # Turn the GPIO off
        time.sleep(120)  # Wait for 2 minutes (120 seconds)

try:
    run_relay()
finally:
    GPIO.cleanup()  # Clean up the GPIO pins when the program finishes
    print("GPIO cleanup done.")
