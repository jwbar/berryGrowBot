import RPi.GPIO as GPIO
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set up GPIO
GPIO.setwarnings(False)  # Disable warnings about pins already in use
GPIO.setmode(GPIO.BCM)

# Define the GPIO pins for the 4 relays (Adjust the names and pin numbers as necessary)
relay_pins = {
    "Light": 4,          # Light
    "Fan": 17,           # Fan
    "Dehumidify": 27,    # Dehumidifier
    "Water": 22          # Water Pump
}

# Set up the GPIO pins
for pin in relay_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # Turn off relay initially (assuming active-low relay)

# Command to turn on a relay
async def turn_on(update: Update, context) -> None:
    try:
        relay_name = context.args[0]
        if relay_name in relay_pins:
            GPIO.output(relay_pins[relay_name], GPIO.LOW)  # Turn on relay (active-low)
            await update.message.reply_text(f'{relay_name} is ON.')
        else:
            await update.message.reply_text('Invalid relay name.')
    except IndexError:
        await update.message.reply_text('Please provide a valid relay name (Light, Fan, Dehumidify, Water).')
    except Exception as e:
        logger.error(f"Error in turn_on: {e}")
        await update.message.reply_text('An error occurred while turning on the relay.')

# Command to turn off a relay
async def turn_off(update: Update, context) -> None:
    try:
        relay_name = context.args[0]
        if relay_name in relay_pins:
            GPIO.output(relay_pins[relay_name], GPIO.HIGH)  # Turn off relay (active-low)
            await update.message.reply_text(f'{relay_name} is OFF.')
        else:
            await update.message.reply_text('Invalid relay name.')
    except IndexError:
        await update.message.reply_text('Please provide a valid relay name (Light, Fan, Dehumidify, Water).')
    except Exception as e:
        logger.error(f"Error in turn_off: {e}")
        await update.message.reply_text('An error occurred while turning off the relay.')

# Start command
async def start(update: Update, context) -> None:
    await update.message.reply_text('Welcome! Use /on <relay_name> to turn on a relay and /off <relay_name> to turn off a relay. Example: /on Light, Fan, Dehumidify, Water.')

# Main function to start the bot
async def main():
    try:
        # Replace 'YOUR_BOT_TOKEN' with your actual bot token
        application = Application.builder().token("7536315323:AAFsYEuyhDIv6_UP_8DhbDrUtks9gcNwm_Q").build()

        # Initialize the application
        await application.initialize()

        # Register the commands
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("on", turn_on))
        application.add_handler(CommandHandler("off", turn_off))

        # Start the bot
        await application.start()

        # Run the bot until you press Ctrl-C
        await application.stop()

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    finally:
        # Cleanup GPIO on exit
        GPIO.cleanup()
#how to launch
#gunicorn --chdir /home/jay/growhub --workers 4 --bind 0.0.0.0:5000 mir:app
#sudo mv growhub.service /etc/systemd/system/growhub.service
#sudo systemctl restart  growhub.service 
#sudo journalctl -u growhub
#sudo systemctl daemon-reload 
#sudo systemctl restart  growhub.service 