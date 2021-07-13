from datetime import datetime, timedelta

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


def symbol_to_ts_code(symbol="600519"):
    symbol = str(symbol)
    if len(symbol) > 6:
        print("Length Error!")
    elif len(symbol) < 6:
        symbol = "{:0>6d}".format(int(symbol))

    # 交易所判断
    ts_code = ""

    if symbol[0] == "6":
        ts_code = symbol + ".SH"
    elif symbol[0] in ["0", "3"]:
        ts_code = symbol + ".SZ"
    elif symbol[0:2] in ["11"]:
        ts_code = symbol + ".SH"
    elif symbol[0:2] in ["12"]:
        ts_code = symbol + ".SZ"

    # 证券类型判断
    stock_type = "传统新股"
    if symbol[0:2] == "68":
        stock_type = "科创板"
    elif symbol[0] == "3":
        stock_type = "注册创业板"
    elif symbol[0] == "1":
        stock_type = "可转债"

    return ts_code, stock_type


def get_flag_date_str(date, delta):
    tmp = datetime.strptime(date, "%Y%m%d")
    date_delta = timedelta(days=delta)
    date_out = datetime.strftime(tmp + date_delta, "%Y%m%d")
    return date_out
