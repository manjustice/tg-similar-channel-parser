import time
from datetime import datetime, timedelta

import psutil
import pyautogui

from app.custom_exeptions import LoadingError, NoAccountError
from app.data import Channel, StatusType
from app.db_connector import DBConnector
from app.block import Block, Size, Position
from app.google_sheet import display_data_in_google_sheet
from app.telethon_client import TelethonClient
from app.utils import get_current_hour, launch_telegram_desktop, get_copy_result, try_to_find_tg_process
from config import root_logger, HOUR_TO_SEND


class Telegram:
    def __init__(
            self,
            db: DBConnector,
            telethon_client: TelethonClient,
            telegram_pid: int,
            telegram_window: Block,
            channels_block: Block,
            channel_size: Size,
            channel_info_button: Block,
            channel_info_window: Block,
            close_info_button: Block,
            back_to_processing_channel_button: Block,
            channel_name_position: Position,
            channel_url_position: Position,
            password_input_position: Position,
            similar_channels_block: Block,
            similar_channels_screenshot: str,
            login_button_screenshot: str,
            window_controls_screenshot: str,
            cloud_password_screenshot: str,
            select_chat_area_screenshot: str
    ):
        self.db = db
        self.telethon_client = telethon_client
        self.telegram_pid = telegram_pid

        self.telegram_window = telegram_window
        self.channels_block = channels_block
        self.channel_size = channel_size
        self.channel_info_button = channel_info_button
        self.channel_info_window = channel_info_window
        self.close_info_button = close_info_button
        self.back_to_processing_channel_button = back_to_processing_channel_button
        self.channel_name_position = channel_name_position
        self.channel_url_position = channel_url_position
        self.password_input_position = password_input_position
        self.similar_channels_block = similar_channels_block

        self.similar_channels_screenshot = similar_channels_screenshot
        self.login_button_screenshot = login_button_screenshot
        self.window_controls_screenshot = window_controls_screenshot
        self.cloud_password_screenshot = cloud_password_screenshot
        self.select_chat_area_screenshot = select_chat_area_screenshot

        self.channels_x, self.channels_y = self.channels_block.get_top_center_position()
        self.login_button_position = Position(510, 500)
        self.change_to_phone_num_button_position = Position(510, 550)
        self.enter_phone_num_position = Position(450, 380)
        self.channels_scroll_times = 0
        self.max_channels_scroll_times = 5

        self.similar_channels_x, self.similar_channels_y = self.similar_channels_block.get_top_center_position()
        self.sim_channel_button_x = self.sim_channel_button_y = None

        self.last_sending_date = None
        self.date_to_restart_parsing = self._get_data_to_restart_parsing()

        self.xclip_error_times = 0
        self.xclip_max_error_times = 3

    def run_parser(self):
        try:
            self.wait_for_telegram()
        except LoadingError:
            pid = try_to_find_tg_process()

            if pid is None:
                self.telegram_pid = launch_telegram_desktop()
            else:
                self.telegram_pid = pid

        is_logged_in = self.check_if_logged_in()

        if not is_logged_in:
            self.login_to_telegram()

        self.start_parsing()

    def start_parsing(self):
        root_logger.info("Starting parser")

        while True:
            try:
                self._start_parsing()
            except NoAccountError as e:
                root_logger.error(f"start parsing - {str(e)}")
                exit(0)
            except Exception as e:
                root_logger.error(f"start parsing - {str(e)}")

            self.restart_telegram()
            self.xclip_error_times = 0
            self.channels_y = self.channels_block.start.y

            logged_in = self.check_if_logged_in()

            if not logged_in:
                self.login_to_telegram()

    def _start_parsing(self):
        channel = self.choose_next_channel()
        time.sleep(2)
        self.click_on_channel_info()
        time.sleep(2)
        self.parse_similar_channels(channel)

        root_logger.info(f"Channel {channel.name} processed")
        self.sim_channel_button_x = self.sim_channel_button_y = None

        self.db.add_processed_channel(channel)

        if get_current_hour() == HOUR_TO_SEND:
            current_date = datetime.now().date()
            # Check if it's a new day before sending to Google Sheet
            if self.last_sending_date is None or self.last_sending_date != current_date:
                self.send_to_google_sheet()
                self.last_sending_date = current_date

        self.check_memory_usage()
        logged_in = self.check_if_logged_in()

        if not logged_in:
            self.login_to_telegram()

    def wait_for_telegram(self):
        was_opened = False
        root_logger.info("Waiting for telegram")

        try:
            telegram_process = psutil.Process(self.telegram_pid)
        except psutil.NoSuchProcess:
            raise LoadingError(f"Telegram process not found {self.telegram_pid}")

        if telegram_process.status() not in ("running", "sleeping"):
            raise LoadingError(f"Telegram process not running {self.telegram_pid}")

        # Wait for telegram window to appear. If it's not appeared in 12 tries or 2 minutes, raise LoadingError
        for _ in range(12):
            telegram_window = None
            try:
                telegram_window = pyautogui.locateCenterOnScreen(
                    self.window_controls_screenshot, confidence=0.9
                )
            except Exception:
                root_logger.debug("Telegram window not found")

            if telegram_window is not None:
                root_logger.info("Telegram has been opened")
                was_opened = True
                break

            time.sleep(10)

        if not was_opened:
            raise LoadingError("Telegram window has not been opened")

    def check_if_logged_in(self) -> bool:
        root_logger.info("Checking if logged in")
        login_button = None

        try:
            login_button = pyautogui.locateCenterOnScreen(
                self.login_button_screenshot, confidence=0.9
            )
        except pyautogui.ImageNotFoundException:
            pass

        if login_button is not None:
            root_logger.info("Not logged in")
            return False

        root_logger.info("Logged in")
        return True

    def check_memory_usage(self):
        memory_usage = None
        memory_threshold_mb = 2048

        try:
            process = psutil.Process(self.telegram_pid)
            memory_info = process.memory_info()
            memory_usage = memory_info.rss / (1024 ** 2)
            root_logger.info(f"Memory usage for Telegram process (pid {process.pid}): {memory_usage:.2f} MB")
        except Exception as e:
            root_logger.error(f"Error checking memory usage: {e}", exc_info=True)

        # Restart Telegram if func can't find how many memory usage or more than memory_threshold_mb
        if memory_usage is None or memory_usage > memory_threshold_mb:
            self.restart_telegram()

    def restart_telegram(self):
        root_logger.info("Restarting Telegram")

        # Kill Telegram process if it's running
        try:
            process = psutil.Process(self.telegram_pid)
            process.terminate()
        except Exception:
            pass

        self.telegram_pid = launch_telegram_desktop()
        self.xclip_error_times = 0
        try:
            self.wait_for_telegram()
        except LoadingError:
            pid = try_to_find_tg_process()

            if pid is None:
                self.telegram_pid = launch_telegram_desktop()
            else:
                self.telegram_pid = pid

    def login_to_telegram(self):
        logged_in = None

        while not logged_in:
            root_logger.info(
                f"Logging to telegram phone number: {self.telethon_client.account_data.phone_number}"
            )

            pyautogui.click(
                self.login_button_position.x,
                self.login_button_position.y,
                duration=0.5
            )
            time.sleep(1.5)
            pyautogui.click(
                self.change_to_phone_num_button_position.x,
                self.change_to_phone_num_button_position.y,
                duration=0.5
            )
            time.sleep(1.5)
            pyautogui.click(
                self.enter_phone_num_position.x,
                self.enter_phone_num_position.y,
                duration=0.5
            )
            time.sleep(1.5)
            pyautogui.press("backspace", presses=5, interval=0.1)
            pyautogui.write(
                self.telethon_client.account_data.phone_number,
                interval=0.1
            )
            pyautogui.press("enter")
            time.sleep(10)

            code = self.telethon_client.get_verification_code()

            pyautogui.write(code, interval=0.1)
            time.sleep(1)

            if self.is_password_required():
                root_logger.info("Password required. Entering password")
                self.enter_password()

            # check if logged successfully
            try:
                location = pyautogui.locateCenterOnScreen(
                    self.select_chat_area_screenshot,
                    confidence=0.9
                )
                logged_in = bool(location)
            except Exception:
                logged_in = False

            if not logged_in and self.telethon_client.account_data.password is not None:
                self.telethon_client.update_account_status(
                    StatusType.INCORRECT_PASSWORD.value
                )

            if not logged_in:
                self.restart_telegram()
                self.telethon_client.update_client()
            else:
                root_logger.info("Logged in")
                time.sleep(2)
                self.telethon_client.check_and_subscribe_channels(self.db)

    def is_password_required(self) -> bool:
        root_logger.info("Check if password required")
        try:
            location = pyautogui.locateCenterOnScreen(
                self.cloud_password_screenshot,
                confidence=0.9
            )

            return bool(location)
        except Exception:
            return False

    def enter_password(self):
        pyautogui.click(
            x=self.password_input_position.x,
            y=self.password_input_position.y
        )
        time.sleep(0.5)

        if self.telethon_client.account_data.password is None:
            self.telethon_client.update_account_status(
                StatusType.PASSWORD_REQUIRED.value
            )
        else:
            pyautogui.write(
                self.telethon_client.account_data.password,
                interval=0.1
            )
            pyautogui.press("enter")
            time.sleep(3)

    def choose_next_channel(self) -> Channel:
        root_logger.info("Choosing next channel")

        self.channels_x, self.channels_y = self.channels_block.get_top_center_position()

        while True:
            if self.channels_scroll_times >= self.max_channels_scroll_times:
                if datetime.now() > self.date_to_restart_parsing:
                    self.restart_parsing_channels()
                else:
                    self.update_channel_list()

            root_logger.debug(f"Current channel position: {self.channels_x}, {self.channels_y}")
            pyautogui.click(self.channels_x, self.channels_y, duration=0.5)
            time.sleep(2)
            channel = self.get_channel_info()

            if channel is not None and not self.db.is_channel_processed(channel):
                root_logger.debug("Channel is not processed. Returning it")
                return channel

            self.channels_y += self.channel_size.height

            if self.channels_y > self.channels_block.start.y + self.channels_block.size.height:
                self.scroll_down_channels()
                self.channels_y = self.channels_block.start.y
                self.channels_scroll_times += 1

    def get_channel_info(self) -> Channel | None:
        root_logger.info("Getting channel info")
        self.click_on_channel_info()

        pyautogui.moveTo(
            self.channel_name_position.x,
            self.channel_name_position.y,
            duration=0.2
        )
        pyautogui.dragTo(
            self.channel_name_position.x,
            self.channel_name_position.y + 10,
            duration=0.5
        )
        pyautogui.hotkey("ctrl", "c")
        time.sleep(1)

        channel_name = get_copy_result()

        pyautogui.moveTo(
            self.channel_url_position.x,
            self.channel_url_position.y,
            duration=0.2
        )
        pyautogui.dragTo(
            self.channel_url_position.x,
            self.channel_url_position.y + 15,
            duration=0.5
        )
        pyautogui.hotkey("ctrl", "c")
        time.sleep(1)

        channel_url = get_copy_result()

        position = self.close_info_button.get_random_position()
        pyautogui.click(position.x, position.y, duration=0.5)
        time.sleep(2)

        root_logger.info(f"Got channel info: {channel_name}, {channel_url}")

        if channel_name is None or channel_url is None:
            self.xclip_error_times += 1

            if self.xclip_error_times >= self.max_channels_scroll_times:
                self.restart_telegram()

            return None

        return Channel.create(channel_name, channel_url)

    def scroll_top_channels(self, scroll_times: int = 100):
        position = self.channels_block.get_random_position()
        pyautogui.moveTo(position.x, position.y, duration=0.5)
        pyautogui.scroll(scroll_times)

    def scroll_down_channels(self, scroll_times: int = 5):
        position = self.channels_block.get_random_position()
        pyautogui.moveTo(position.x, position.y, duration=0.5)
        pyautogui.scroll(-scroll_times)

    def scroll_down_similar_channels(self, scroll_times: int = 8):
        position = self.similar_channels_block.get_random_position()
        pyautogui.moveTo(position.x, position.y, duration=0.5)
        pyautogui.scroll(-scroll_times)

    def click_on_channel_info(self):
        root_logger.debug("Clicking on channel info")
        position = self.channel_info_button.get_random_position()
        pyautogui.click(position.x, position.y)
        time.sleep(3)

    def find_similar_channels(self):
        position = self.channel_info_window.get_random_position()
        pyautogui.moveTo(position.x, position.y, duration=0.5)
        pyautogui.scroll(-100)
        time.sleep(1)

        if self.sim_channel_button_x is None or self.sim_channel_button_y is None:
            location = pyautogui.locateCenterOnScreen(
                self.similar_channels_screenshot,
                confidence=0.9
            )
            self.sim_channel_button_x, self.sim_channel_button_y = location

            if location is None:
                raise Exception()

        time.sleep(1.5)

        pyautogui.click(
            self.sim_channel_button_x, self.sim_channel_button_y, duration=0.5
        )

    def back_to_processing_channel(self):
        root_logger.debug("Back to processing channel")
        position = self.back_to_processing_channel_button.get_random_position()
        pyautogui.click(position.x, position.y)
        time.sleep(2)
        self.click_on_channel_info()

    def parse_similar_channels(self, processing_channel: Channel):
        root_logger.info(f"Starting parsing similar channels for {processing_channel.name}")
        times_scrolled = 0
        max_times_to_scroll = 10
        scroll_number = 8

        self.similar_channels_x, self.similar_channels_y = self.similar_channels_block.get_top_center_position()

        while True:
            try:
                root_logger.debug("Trying to find similar channels")
                self.find_similar_channels()
            except Exception:
                root_logger.error(
                    f"Can't find similar channels on channel {processing_channel.name}"
                )
                return

            time.sleep(1)

            if self.similar_channels_y > self.similar_channels_block.start.y + self.similar_channels_block.size.height:
                times_scrolled += 1
                self.scroll_down_similar_channels(scroll_number * times_scrolled)
                self.similar_channels_y = self.similar_channels_block.start.y
            else:
                if times_scrolled > 0:
                    self.scroll_down_similar_channels(scroll_number * times_scrolled)

            if times_scrolled >= max_times_to_scroll:
                break

            pyautogui.click(self.similar_channels_x, self.similar_channels_y, duration=0.5)
            time.sleep(1)
            channel = self.get_channel_info()

            if channel is not None:
                root_logger.info(
                    f"Got similar channel: {channel.name}. "
                    f"Coordinates: {self.similar_channels_x}, {self.similar_channels_y}"
                )
                if not self.db.is_channel_known(channel):
                    if self.db.dbname != "tg-similar-channels" :
                        root_logger.info("Add new channel to db")
                        self.db.add_known_channel(channel)
                else:
                    root_logger.info(f"Update parameter is_new=True")
                    self.db.update_known_channel_is_new(channel, is_new=True)

            self.back_to_processing_channel()

            self.similar_channels_y += 58

    def update_channel_list(self):
        self.channels_scroll_times = 0

        unsub_count = self.telethon_client.unsubscribe_from_channels()
        self.telethon_client.subscribe_to_channels(self.db, limit=unsub_count)

    def restart_parsing_channels(self):
        root_logger.info("Restart parsing")
        self.date_to_restart_parsing = self._get_data_to_restart_parsing()

        self.telethon_client.unsubscribe_from_channels()

        channels = self.db.get_first_channels_and_restart()
        self.telethon_client.subscribe_to_channels(self.db, 20, channels)

    def send_to_google_sheet(self):
        found_ads_channels = self.db.get_not_sent_channels()

        if found_ads_channels:
            root_logger.info("Sending data to google sheet")

            try:
                display_data_in_google_sheet(found_ads_channels)
            except Exception:
                pass

            for channel in found_ads_channels:
                if isinstance(channel, Channel):
                    self.db.mark_channel_as_sent(channel.url)
        else:
            root_logger.info("No data to send")

    @staticmethod
    def _get_data_to_restart_parsing():
        return datetime.now() + timedelta(days=2)
