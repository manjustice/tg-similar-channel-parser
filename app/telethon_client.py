import re
import time

import pymongo
from telethon.sync import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest

from app.custom_exeptions import NoAccountError
from app.data import TgAccount, StatusType, Channel
from app.db_connector import DBConnector
from config import root_logger


class TelethonClient:
    def __init__(
            self,
            api_id: int,
            api_hash: str,
            accounts_db_name: str,
            parser_db_name: str,
            host: str = "localhost",
            port: int = 27017,
            username: str = None,
            password: str = None,
    ):
        self.parser_db_name = parser_db_name

        self.api_id = api_id
        self.api_hash = api_hash

        self.accounts_db_name = accounts_db_name
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.account_db = self._get_db_client()[self.accounts_db_name]
        self.account_data: TgAccount | None = None

        self.client: TelegramClient | None = None

        self.update_client()

    def _get_db_client(self) -> pymongo.MongoClient:
        if self.username and self.password:
            mongo_url = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
        else:
            mongo_url = f"mongodb://{self.host}:{self.port}/"

        client = pymongo.MongoClient(mongo_url)

        return client

    def _check_client(self):
        if not self.client.is_connected():
            self.client.connect()

    def update_client(self) -> TelegramClient:
        account = client = None

        attempts = 10

        while account is None:
            if self.client is not None:
                try:
                    self.client.disconnect()
                except Exception:
                    pass

            account_doc = self.account_db["accounts"].find_one(
                {"$or": [{"status": None}, {"status": "waiting"}, {"status": "parser_using"}]}
            )

            if attempts <= 0:
                raise NoAccountError("Can't find account for parsing")

            attempts -= 1

            if account_doc is None:
                continue

            account_doc_id = account_doc.get("_id")

            try:
                account = TgAccount.from_dict(account_doc)
            except ValueError as e:
                root_logger.error(f"{str(e)}. Document id {account_doc_id}")
                continue

            client = TelegramClient(
                StringSession(account.session_data),
                self.api_id,
                self.api_hash
            )

            if not client.is_connected():
                client.connect()

            if not client.is_user_authorized():
                self.account_db["accounts"].update_one(
                    {"_id": account_doc_id},
                    {"$set": {"status": StatusType.NOT_WORKING.value}}
                )
                continue

            self.account_data = account

            if self.account_data is not None:
                self.client = client
                self.update_account_status(self.parser_db_name)

        return client

    def get_verification_code(self) -> str | None:
        dialogs = self.client.get_dialogs()

        for dialog in dialogs:
            if dialog.name == "Telegram":
                message_obj = self.client.get_messages(dialog.id, limit=1)[0]
                message_text = message_obj.message
                match = re.search(r'\d+\.\d+|\d+', message_text)
                return match.group()

    def update_account_status(self, status: str):
        self.account_db["accounts"].update_one(
            {"session_data": self.account_data.session_data},
            {"$set": {"status": status}}
        )

    def subscribe_to_channels(
            self,
            db: DBConnector,
            limit: int,
            channels: list[Channel] | None = None
    ):
        if not limit:
            limit = 20

        self._check_client()

        if channels is None:
            main_channels = db.get_main_channels_not_processed()
            limit = limit - len(main_channels)

            if limit > 0:
                channels = db.get_channels_to_subscribe(limit)
                channels.extend(main_channels)

        if channels is None:
            channels = db.get_first_channels_and_restart()

        for channel in channels:
            try:
                self.client(JoinChannelRequest(channel.url))
                root_logger.info(f"Subscribed to {channel.url}")
            except errors.FloodWaitError as fe:
                optimal_time_to_wait = 50000
                if fe.seconds < optimal_time_to_wait:
                    root_logger.info(f"FloodWaitError waiting {fe.seconds} seconds")
                    time.sleep(fe.seconds)
                else:
                    root_logger.error(f"FloodWaitError too much to wait {fe.seconds} seconds")
                    break

            except Exception as e:
                root_logger.critical(f"Error subscribing to {channel.url}: {e}", exc_info=True)

            db.update_known_channel_is_new(channel)

            time.sleep(10)

    def unsubscribe_from_channels(self) -> int:
        self._check_client()

        channels = self.client.get_dialogs()

        for channel in channels:
            if not channel.is_channel:
                continue
            try:
                self.client(LeaveChannelRequest(channel.id))
                root_logger.info(f"Unsubscribed from {channel.name}")
            except errors.FloodWaitError as fe:
                optimal_time_to_wait = 50000
                if fe.seconds < optimal_time_to_wait:
                    root_logger.info(f"FloodWaitError waiting {fe.seconds} seconds")
                    time.sleep(fe.seconds)
                else:
                    root_logger.error(f"FloodWaitError too much to wait {fe.seconds} seconds")
                    break

            except Exception as e:
                root_logger.critical(f"Error unsubscribing from {channel.name}: {e}", exc_info=True)
                break

            time.sleep(10)

        return len(channels)

    def check_and_subscribe_channels(self, db: DBConnector):
        channels = self.client.get_dialogs()

        if len(channels) <= 3:
            self.subscribe_to_channels(db, 20)


if __name__ == "__main__":
    from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TG_ACCOUNTS_DB_NAME, MONGODB_HOST, MONGODB_PORT

    tl_client = TelethonClient(
        host=MONGODB_HOST,
        port=MONGODB_PORT,
        api_hash=TELEGRAM_API_HASH,
        api_id=TELEGRAM_API_ID,
        accounts_db_name=TG_ACCOUNTS_DB_NAME,
        parser_db_name="tg"
    )

    while True:
        time.sleep(100)
