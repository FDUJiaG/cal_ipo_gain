from datetime import datetime

quarter_date_dict = {
    "Q1": ["01-01", "03-31"],
    "Q2": ["04-01", "06-30"],
    "Q3": ["07-01", "09-30"],
    "Q4": ["10-01", "12-31"]
}


def get_time(date=False, utc=False, msl=3):
    if date:
        time_fmt = "%Y-%m-%d %H:%M:%S.%f"
    else:
        time_fmt = "%H:%M:%S.%f"

    if utc:
        return datetime.utcnow().strftime(time_fmt)[:(msl - 6)]
    else:
        return datetime.now().strftime(time_fmt)[:(msl - 6)]


def print_info(status="I"):
    return "\033[0;33;1m[{} {}]\033[0m".format(status, get_time())
