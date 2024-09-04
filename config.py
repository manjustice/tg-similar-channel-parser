import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

from app.block import Position, Block, Size


load_dotenv()

os.environ["DISPLAY"] = ":1"
os.environ["XDG_SESSION_TYPE"] = "x11"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# TELEGRAM SETTINGS
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

# telegram measurement constants
TELEGRAM_WINDOW = Block(
    Position(112, 84),
    Size(800, 600)
)
CHANNELS_BLOCK = Block(
    Position(112, 140),
    Size(256, 546)
)
CHANNELS_SIZE = Size(256, 62)
CHANNELS_INFO_BUTTON = Block(
    Position(450, 90),
    Size(300, 40)
)
CHANNEL_INFO_WINDOW = Block(
    Position(317, 280),
    Size(390, 404)
)
CLOSE_INFO_BUTTON = Block(
    Position(675, 132),
    Size(12, 12)
)
BACK_TO_PROCESSING_CHANNEL_BUTTON = Block(
    Position(415, 90),
    Size(30, 40)
)
CHANNEL_NAME_POSITION = Position(425, 210)
CHANNEL_URL_POSITION = Position(392, 300)
SIMILAR_CHANNELS_BLOCK = Block(
    Position(320, 170),
    Size(380, 510)
)
PASSWORD_INPUT_POSITION = Position(370, 305)

# MONGODB SETTINGS
MONGODB_HOST = os.getenv("MONGO_HOST")
MONGODB_PORT = os.getenv("MONGO_PORT")
MONGODB_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGODB_NAME = os.getenv("MONGO_INITDB_DATABASE")
TG_ACCOUNTS_DB_NAME = os.getenv("TG_ACCOUNTS_DB_NAME")

# LOGGING SETTINGS
LOG_DIR = "logs"
LOG_FILE = "app.log"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file_path = os.path.join(LOG_DIR, LOG_FILE)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024, backupCount=30)
root_logger.addHandler(file_handler)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%d-%m-%Y %H:%M:%S")
file_handler.setFormatter(formatter)


# GOOGLE SHEET SETTINGS
GOOGLE_CRED_FILE_PATH = os.path.join(BASE_DIR, "creds.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
HOUR_TO_SEND = 5


# OTHER SETTINGS
SCREENSHOT_DIR = "screenshots"
SIMILAR_CHANNELS_BLOCK_IMAGE = os.path.join(SCREENSHOT_DIR, "similar_channels_block_white.png")
LOGIN_BUTTON_IMAGE = os.path.join(SCREENSHOT_DIR, "login_button.png")
WINDOW_CONTROLS_IMAGE = os.path.join(SCREENSHOT_DIR, "window_controls.png")
CLOUD_PASSWORD_IMAGE = os.path.join(SCREENSHOT_DIR, "cloud_password_check.png")
# this screenshot using to identify that you are logged in
SELECT_CHAT_AREA_IMAGE = os.path.join(SCREENSHOT_DIR, "select_chat_area.png")
