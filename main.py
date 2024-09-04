from app.db_connector import get_db
from app.telegram_automation import Telegram
from app.telethon_client import TelethonClient

from config import (
    TELEGRAM_WINDOW,
    CHANNELS_BLOCK,
    CHANNELS_SIZE,
    CHANNELS_INFO_BUTTON,
    CHANNEL_INFO_WINDOW,
    CLOSE_INFO_BUTTON,
    BACK_TO_PROCESSING_CHANNEL_BUTTON,
    CHANNEL_NAME_POSITION,
    CHANNEL_URL_POSITION,
    SIMILAR_CHANNELS_BLOCK,
    SIMILAR_CHANNELS_BLOCK_IMAGE,
    LOGIN_BUTTON_IMAGE,
    WINDOW_CONTROLS_IMAGE,
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TG_ACCOUNTS_DB_NAME,
    MONGODB_NAME,
    MONGODB_HOST,
    MONGODB_PORT,
    MONGODB_USER,
    MONGODB_PASSWORD,
    CLOUD_PASSWORD_IMAGE,
    SELECT_CHAT_AREA_IMAGE,
    PASSWORD_INPUT_POSITION
)
from app.utils import launch_telegram_desktop


def main():
    telegram_pid = launch_telegram_desktop()

    db = get_db()

    telethon_client = TelethonClient(
        api_hash=TELEGRAM_API_HASH,
        api_id=TELEGRAM_API_ID,
        accounts_db_name=TG_ACCOUNTS_DB_NAME,
        parser_db_name=MONGODB_NAME,
        host=MONGODB_HOST,
        port=MONGODB_PORT,
        username=MONGODB_USER,
        password=MONGODB_PASSWORD
    )

    tg = Telegram(
        db=db,
        telethon_client=telethon_client,
        telegram_pid=telegram_pid,
        telegram_window=TELEGRAM_WINDOW,
        channels_block=CHANNELS_BLOCK,
        channel_size=CHANNELS_SIZE,
        channel_info_button=CHANNELS_INFO_BUTTON,
        channel_info_window=CHANNEL_INFO_WINDOW,
        close_info_button=CLOSE_INFO_BUTTON,
        back_to_processing_channel_button=BACK_TO_PROCESSING_CHANNEL_BUTTON,
        channel_name_position=CHANNEL_NAME_POSITION,
        channel_url_position=CHANNEL_URL_POSITION,
        password_input_position=PASSWORD_INPUT_POSITION,
        similar_channels_block=SIMILAR_CHANNELS_BLOCK,
        similar_channels_screenshot=SIMILAR_CHANNELS_BLOCK_IMAGE,
        login_button_screenshot=LOGIN_BUTTON_IMAGE,
        window_controls_screenshot=WINDOW_CONTROLS_IMAGE,
        cloud_password_screenshot=CLOUD_PASSWORD_IMAGE,
        select_chat_area_screenshot=SELECT_CHAT_AREA_IMAGE
    )

    tg.run_parser()


if __name__ == "__main__":
    main()
