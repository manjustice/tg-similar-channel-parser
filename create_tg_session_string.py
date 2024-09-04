import os

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ApiIdInvalidError


def get_api_id() -> int:
    while True:
        api_id = input("Enter your API ID: ")

        if api_id.isdigit():
            return int(api_id)

        print("Input must be valid integer")


def get_api_hash() -> str:
    while True:
        api_hash = input("Enter your API Hash: ")

        if len(api_hash) == 32 and all(c in '0123456789abcdef' for c in api_hash):
            return api_hash

        print("Input must contain 32 characters in the 16-digit notation: '0123456789abcdef'")


def get_phone_number() -> str:
    while True:
        phone_number = input("Enter your phone number in format +380XXXXXXXXX: ")

        if phone_number.startswith('+') and phone_number[1:].isdigit():
            return phone_number

        print("Input must be valid phone number")


def main():
    api_id = get_api_id()
    api_hash = get_api_hash()
    phone_number = get_phone_number()

    try:
        client = TelegramClient(phone_number, api_id, api_hash)

        client.start(phone_number)

        session_string = StringSession.save(client.session)

        print(f'Your session string: \n{session_string}')

    except ApiIdInvalidError:
        print("The api_id/api_hash combination is invalid")

    if os.path.exists(f"{phone_number}.session"):
        os.remove(f"{phone_number}.session")


if __name__ == '__main__':
    main()
