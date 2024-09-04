import os
import re

from telethon import TelegramClient

from config import TELEGRAM_API_ID, TELEGRAM_API_HASH


def add_session():
    phone_pattern = r'^\+?\d{10,15}$'
    phone_number = input("Please enter your phone (or type '0' if you want to cancel): ")

    if phone_number == "0":
        os.system("clear")
        return

    if not re.match(phone_pattern, phone_number):
        os.system("clear")
        print(f"Not a valid phone number: {phone_number}")
        return add_session()

    client = TelegramClient(phone_number, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    client.start(phone_number)


if __name__ == '__main__':
    while True:
        choice = input(
            "Choose option:\n"
            "1. Add new session.\n"
            "2. Exit.\n-> "
        )
        if choice == "1":
            os.system("clear")
            add_session()
        elif choice == "2":
            os.system("clear")
            break
        else:
            os.system("clear")
            print("Invalid choice. Please enter 1 or 2.")
