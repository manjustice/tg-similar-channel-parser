class SpreadSheetError(Exception):
    """Raise when not able to connect to spreadsheet"""
    pass


class LoadingError(Exception):
    """Raise when not able to load some application"""
    pass


class NoAccountError(Exception):
    """Raise when there is no account for tg"""
    pass
