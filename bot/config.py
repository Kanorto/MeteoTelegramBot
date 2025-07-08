import os

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Default update time for weather and magnetic storm notifications
DEFAULT_NOTIFY_TIME = "09:00"

# Path to user settings storage
USERS_FILE = os.path.join(os.path.dirname(__file__), '../data/users.json')

# Default region code for X-RAS magnetic storm forecast
DEFAULT_MAGNETIC_REGION = "RAL5"
