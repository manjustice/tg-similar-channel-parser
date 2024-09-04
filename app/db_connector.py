import pymongo

from config import MONGODB_NAME, MONGODB_HOST, MONGODB_PORT, MONGODB_USER, MONGODB_PASSWORD
from app.data import Channel


class DBConnector:
    def __init__(
            self,
            dbname: str,
            host: str = "localhost",
            port: int = 27017,
            username: str = None,
            password: str = None
    ):
        self.dbname = dbname
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = self._get_client()

        self.known_channels = self.client[self.dbname]["known_channels"]
        self.processed_channels = self.client[self.dbname]["processed_channels"]
        self.main_channels = self.client[self.dbname]["main_channels"]

    def _get_client(self) -> pymongo.MongoClient:
        if self.username and self.password:
            mongo_url = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
        else:
            mongo_url = f"mongodb://{self.host}:{self.port}/"

        client = pymongo.MongoClient(mongo_url)

        return client

    def is_channel_processed(self, channel: Channel) -> bool:
        channel_doc = self.processed_channels.find_one({"url": channel.url})

        return bool(channel_doc)

    def add_processed_channel(self, channel: Channel, subscribed: bool = True):
        channel_dict = channel._asdict()
        channel_dict["subscribed"] = subscribed

        self.processed_channels.insert_one(channel_dict)

    def is_channel_known(self, channel: Channel) -> bool:
        channel_doc = self.known_channels.find_one({"url": channel.url})
        processed_channel_doc = self.processed_channels.find_one({"url": channel.url})

        return bool(channel_doc) or bool(processed_channel_doc)

    def add_known_channel(self, channel: Channel, is_new: bool = True, sent: bool = False):
        channel_dict = channel._asdict()
        channel_dict["is_new"] = is_new
        channel_dict["sent"] = sent

        self.known_channels.insert_one(channel_dict)

    def get_channels_to_subscribe(self, limit: int = 50) -> list[Channel]:
        max_limit = 20

        limit = max(max_limit, min(limit, max_limit))

        channels = self.known_channels.find(
            {"is_new": True}
        )[:limit]

        return [
            Channel(name=channel.get("name"), url=channel.get("url"))
            for channel in channels
        ]

    def get_channels_to_unsubscribe(self) -> list[Channel]:
        channels = self.processed_channels.find(
            {"subscribed": True}
        )

        return [
            Channel(name=channel.get("name"), url=channel.get("url"))
            for channel in channels
        ]

    def update_channel_unsubscribed(self, channel: Channel):
        self.processed_channels.update_one(
            {"url": channel.url},
            {"$set": {"subscribed": False}}
        )

    def update_known_channel_is_new(self, channel: Channel, is_new: bool = False):
        self.known_channels.update_one(
            {"url": channel.url},
            {"$set": {"is_new": is_new}}
        )

    def get_not_sent_channels(self):
        channels = self.known_channels.find({"sent": False})

        return [
            Channel(name=channel.get("name"), url=channel.get("url"))
            for channel in channels
        ]

    def mark_channel_as_sent(self, url: str):
        self.known_channels.update_one(
            {"url": url},
            {"$set": {"sent": True}}
        )

    def get_first_channels_and_restart(self):
        self.processed_channels.delete_many({})

        channels = self.get_main_channels_not_processed()

        self.known_channels.update_many({}, {"$set": {"is_new": False}})

        return channels

    def get_main_channels_not_processed(self):
        max_channels = 20
        channels_doc = self.main_channels.find({})
        channels = []

        for channel in channels_doc:
            channel = Channel(name=channel.get("name"), url=channel.get("url"))

            if not self.is_channel_processed(channel):
                channels.append(channel)

        return channels[:max_channels]


def get_db() -> DBConnector:
    return DBConnector(
        MONGODB_NAME, MONGODB_HOST, MONGODB_PORT, MONGODB_USER, MONGODB_PASSWORD
    )
