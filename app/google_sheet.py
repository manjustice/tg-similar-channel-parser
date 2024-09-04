import warnings

import gspread
from gspread import Spreadsheet, WorksheetNotFound
from datetime import datetime

from app.custom_exeptions import SpreadSheetError
from app.data import Channel
from config import root_logger, GOOGLE_CRED_FILE_PATH, SPREADSHEET_ID


warnings.filterwarnings("ignore", category=DeprecationWarning)


def display_data_in_google_sheet(data: list[Channel | list[str]]) -> None:
    try:
        sh = _get_google_sheet()
    except Exception as e:
        root_logger.error(
            f"Error getting google sheet {SPREADSHEET_ID}. Error: {str(e)}"
        )
        raise SpreadSheetError()
    sheet_name = datetime.now().strftime("%Y-%m-%d")

    try:
        worksheet = sh.worksheet(sheet_name)
        existing_rows, existing_columns = worksheet.row_count, worksheet.col_count

        root_logger.info(f"Updating existing sheet with name {sheet_name}")
    except WorksheetNotFound:
        worksheet = sh.add_worksheet(sheet_name, 1, 1)
        existing_rows, existing_columns = 0, 0

        root_logger.info(f"Creating new sheet with name {sheet_name}")

    sheet_hat = [field.capitalize() for field in data[0].readable_fields]
    data.insert(0, sheet_hat)

    if existing_rows > 0:
        if len(data) > 1:
            data = data[1:]
        else:
            root_logger.info(f"Empty data")
            return

    row_count = len(data)
    column_count = len(data[0])

    if existing_rows == 0 and existing_columns == 0:
        range_to_write = f"A1:{chr(65 + column_count - 1)}{row_count}"
    else:
        range_to_write = f"A{existing_rows + 1}:{chr(65 + column_count - 1)}{existing_rows + row_count}"

    try:
        worksheet.resize(row_count + existing_rows, column_count)
        worksheet.update(range_to_write, data)

        if existing_rows == 0:
            root_logger.info(f"Sheet was created successfully")
        else:
            root_logger.info(f"Sheet was updated successfully")

    except Exception as e:
        root_logger.error(f"Error updating worksheet. Error: {str(e)}")


def _get_google_sheet() -> Spreadsheet:
    gc = gspread.service_account(filename=GOOGLE_CRED_FILE_PATH)
    sh = gc.open_by_key(SPREADSHEET_ID)

    return sh