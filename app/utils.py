import os
import shutil
import subprocess
import time
from datetime import datetime

import psutil

from config import root_logger


def get_current_hour() -> int:
    return int(time.strftime("%H", time.localtime()))


def launch_telegram_desktop() -> int | None:
    attempts = 10

    command = _get_tg_command()

    while attempts > 0:
        root_logger.info(f"Launching Telegram Desktop. Attempt {abs(attempts - 10) + 1}")
        try:
            with open(os.devnull, "w") as devnull:
                process = subprocess.Popen(
                    [command], stdout=devnull, stderr=devnull
                )

            time.sleep(10)
            pid = process.pid
            root_logger.info(f"Telegram {pid=}")

            if psutil.pid_exists(pid):
                root_logger.info(f"Telegram Desktop launched with pid {pid}")
                return pid
            else:
                pid = try_to_find_tg_process()

            if pid is not None:
                root_logger.info(f"Telegram Desktop launched with pid {pid}")
                return pid

        except Exception as e:
            root_logger.error(f"Error launching Telegram Desktop: {e}", exc_info=True)

        attempts -= 1

    raise Exception("Can't launch Telegram Desktop")


def get_unix_timestamp():
    current_time = datetime.now()
    timestamp = current_time.timestamp()

    return timestamp

def get_copy_result() -> str | None:
    tries = 3
    paste_command = ["xclip", "-selection", "clipboard", "-o"]

    while tries > 0:
        try:
            result = subprocess.run(paste_command, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                root_logger.error(f"Paste process finished with error {result.returncode}")
                return None
        except subprocess.TimeoutExpired:
            root_logger.error("Paste process has been working over 5 seconds. Restart process")

        tries -= 1


def try_to_find_tg_process() -> int | None:
    root_logger.info("Trying to find tg process by name")
    for process in psutil.process_iter():
        if "telegram" in process.name().lower():
            return process.pid


def _get_tg_command() -> str:
    valid_command = None

    commands = ("telegram-desktop", "telegram")

    for command in commands:
        if shutil.which(command):
            valid_command = command
            break

    if valid_command is None:
        root_logger.critical("Telegram Desktop app not found")
        raise Exception("Telegram Desktop app not found")

    return valid_command
