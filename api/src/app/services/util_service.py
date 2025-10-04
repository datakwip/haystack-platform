from datetime import datetime

date_format = "%Y-%m-%d %H:%M:%S"
def is_valid_date_format(date_string):
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False