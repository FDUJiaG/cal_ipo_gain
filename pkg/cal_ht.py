import os
import pandas as pd
import tushare as ts
import warnings
from pkg.utils import print_info, quarter_date_dict
from pkg.secret import TS_TOKEN
from WindPy import w

warnings.filterwarnings("ignore")


def cal_gain_ht(f_name, df, ipo, qno):
    # 生成季节的起止节点
    # 例如：start_d="20210101", end_d="20210331"
    start_d = "".join([qno[:4], quarter_date_dict[qno[-2:]][0].replace("-", "")])
    end_d = "".join([qno[:4], quarter_date_dict[qno[-2:]][-1].replace("-", "")])

    # 去除重复的行
    df.drop_duplicates(inplace=True)

    # 数据清洗
    df.columns = [item.replace("=\"", "").replace("\"", "") for item in df.columns]

    print(print_info(), end=" ")
    print("The delivery order (DO) is: \n{}".format(df))
    # print(df.values)

    # 将中小板的代码进行 "0" 补全
    index_list = df.index
    for idx, item in zip(index_list, df["证券代码"]):
        if item != "" and len(item) < 6:
            item = "{:0>6d}".format(int(item))
            # print(item)
            df["证券代码"][idx] = item

    # 删除货币基金
    df.drop(df[df["证券代码"] == "511990"].index, inplace=True)
    df.drop(df[df["证券代码"] == "511880"].index, inplace=True)
    df.drop(df[df["证券代码"] == "511660"].index, inplace=True)

    # 生成一个精简数据表，用于挑选指定时间内的新股
    df_op = df[start_d <= df["发生日期"]]
    df_op = df_op[(df_op["买卖标志"] == "证券卖出") & (df_op["发生日期"] <= end_d)]
    df_op.reset_index(inplace=True)

    df_op_group = df_op.groupby(["证券代码"])[["成交数量", "发生金额"]].agg("sum").reset_index()
    print(print_info(), end=" ")
    print("The op group is: \n{}".format(df_op_group))

    # 生成一个包含新股入账信息的数据表
    df_ns = df[df["买卖标志"].isin(["新股入帐", "红股入帐", "上市流通", "托管转入"])]
    print(print_info(), end=" ")
    print("info of ipo into account: \n{}".format(df_ns))

    # 生成一个考察的新股列表
    ns_list = list()
    for ns_item in df_ns["证券代码"]:
        if ns_item in df_op_group["证券代码"].tolist():
            ns_list.append(ns_item)

    print(print_info(), end=" ")
    print("operated number: {}".format(len(ns_list)))

    out_columns = [
        "证券名称", "证券代码", "日期",
        "卖出金额", "成交数量", "发行价", "网下佣金", "净利润",
        "证券类型"
    ]

    df_out = pd.DataFrame(columns=out_columns)

    for ns_item in ns_list:
        item_dict = dict()
        ts_code, stock_type = symbol_to_ts_code(ns_item)
        if ts_code == "":
            print(ns_item)
            return False
        # 证券名称
        try:
            if stock_type == "可转债":
                item_dict[out_columns[0]] = df_ns[df_ns["证券代码"] == ns_item]["证券名称"].tolist()[0]
            else:
                try:
                    item_dict[out_columns[0]] = ipo[ipo["ts_code"] == ts_code]["name"].tolist()[0]
                except:
                    item_dict[out_columns[0]] = w.wsd(
                        ts_code, "sec_name", wind_date, wind_date, "currencyType="
                    ).Data[0][0]
        except:
            item_dict[out_columns[0]] = pro.stock_basic(
                ts_code=ts_code,
                list_status='L',
                fields='ts_code,symbol,name,area'
            )["name"][0]
        # 证券代码
        item_dict[out_columns[1]] = ts_code
        # 日期
        date_temp = sorted(df_op[df_op["证券代码"] == ns_item]["发生日期"].tolist())[0]
        item_dict[out_columns[2]] = date_temp

        # 查询新股入账数量
        buy_num = df_ns[df_ns["证券代码"] == ns_item]["成交数量"].tolist()[0]

        # 确认卖出数量
        sell_num = abs(df_op_group[df_op_group["证券代码"] == ns_item]["成交数量"].tolist()[0])

        # 最正常情况
        if buy_num == sell_num:
            # 卖出金额
            if stock_type == "可转债":
                item_dict[out_columns[3]] = df_op_group[df_op_group["证券代码"] == ns_item]["发生金额"].tolist()[0]
                item_dict[out_columns[4]] = sell_num * 10
            else:
                item_dict[out_columns[3]] = df_op_group[df_op_group["证券代码"] == ns_item]["发生金额"].tolist()[0]
                item_dict[out_columns[4]] = sell_num
        else:
            print(print_info("W"), end=" ")
            print("异常证券代码: {}".format(ts_code))

        # 发行价
        wind_date = "-".join([qno[:4], quarter_date_dict[qno[-2:]][-1]])
        if stock_type == "可转债":
            item_dict[out_columns[5]] = 100
        else:
            try:
                item_dict[out_columns[5]] = ipo[ipo["ts_code"] == ts_code]["price"].tolist()[0]
                if item_dict[out_columns[5]] == 0:
                    item_dict[out_columns[5]] = w.wsd(
                        ts_code, "ipo_price2", wind_date, wind_date, "currencyType="
                    ).Data[0][0]
            except:
                item_dict[out_columns[5]] = w.wsd(
                    ts_code, "ipo_price2", wind_date, wind_date, "currencyType="
                ).Data[0][0]
        # 网下佣金
        if stock_type == "科创板":
            if item_dict[out_columns[1]].split(".")[0] == "688538":
                # 和辉光电网下佣金率 0.4%
                commission = item_dict[out_columns[5]] * buy_num * 0.004
            else:
                commission = item_dict[out_columns[5]] * buy_num * 0.005
        else:
            commission = 0
        item_dict[out_columns[6]] = commission
        # 净利润
        item_dict[out_columns[7]] = item_dict[out_columns[3]] \
            - item_dict[out_columns[4]] * item_dict[out_columns[5]] - commission
        # 证券类型
        item_dict[out_columns[-1]] = stock_type

        df_out = df_out.append(pd.Series(item_dict), ignore_index=True)

    # 排序
    df_out.sort_values(by=[out_columns[2], out_columns[1]], inplace=True)

    # 分项目统计收益
    df_out_group = df_out.groupby([out_columns[-1]])[[out_columns[7]]].agg("sum").reset_index()
    # 计算收益累计
    # 可转债
    try:
        gain = df_out_group[df_out_group[out_columns[-1]] == "可转债"][out_columns[7]].tolist()[0]
    except:
        gain = 0
    df_out = df_out.append(
        pd.Series({
            out_columns[0]: "可转债",
            out_columns[7]: gain
        }),
        ignore_index=True
    )
    # 传统新股
    try:
        gain = df_out_group[df_out_group[out_columns[-1]] == "传统新股"][out_columns[7]].tolist()[0]
    except:
        gain = 0
    df_out = df_out.append(
        pd.Series({
            out_columns[0]: "传统新股",
            out_columns[7]: gain
        }),
        ignore_index=True
    )
    # 科创板
    try:
        gain = df_out_group[df_out_group[out_columns[-1]] == "科创板"][out_columns[7]].tolist()[0]
    except:
        gain = 0
    df_out = df_out.append(
        pd.Series({
            out_columns[0]: "科创板",
            out_columns[7]: gain
        }),
        ignore_index=True
    )
    # 创业板
    try:
        gain = df_out_group[df_out_group[out_columns[-1]] == "创业板"][out_columns[7]].tolist()[0]
    except:
        gain = 0
    df_out = df_out.append(
        pd.Series({
            out_columns[0]: "创业板",
            out_columns[7]: gain
        }),
        ignore_index=True
    )

    # 合计
    df_out = df_out.append(
        pd.Series({
            out_columns[0]: "合计",
            out_columns[7]: sum(df_out_group[out_columns[7]])
        }),
        ignore_index=True
    )

    # 删除辅助列
    df_out.drop(labels=out_columns[-1], axis=1, inplace=True)
    # 保存结果
    out_name = f_name.split(".")[0] + "新收益统计.xlsx"
    out_path = os.path.join(os.path.abspath(".."), "output", qno,  out_name)
    df_out.to_excel(out_path, index=None)


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
        stock_type = "创业板"
    elif symbol[0] == "1":
        stock_type = "可转债"

    return ts_code, stock_type


if __name__ == '__main__':
    # # 单个文件计算
    # file_name = "东风12号.xls"
    # file_path = os.path.join(os.path.abspath(".."), "raw_data", file_name)
    # raw_df = pd.read_table(file_path, encoding="gbk", converters={"发生日期": str, "证券代码": str})
    # # raw_df = pd.read_excel(file_path, converters={"发生日期": str, "证券代码": str})
    # ipo_df = pd.read_csv("ipo.csv", index_col=0, converters={"发生日期": str, "证券代码": str})
    # w.start()
    # cal_gain_ht(file_name, raw_df, ipo_df, "20210101", "20210331")
    # w.stop()

    # # 文件夹计算
    period = "2021Q2"
    dir_path = os.path.join(os.path.abspath(".."), "raw_data", period)
    file_list = os.listdir(dir_path)
    # ipo_df = pd.read_csv("ipo.csv", index_col=0, converters={"发生日期": str, "证券代码": str})

    # 通过 tushare 获取一个 ipo 表格, 删除发行价没有的行
    pro = ts.pro_api(TS_TOKEN)
    ts_end_d = "".join([period[:4], quarter_date_dict[period[-2:]][-1].replace("-", "")])
    ipo_df = pro.new_share(start_date='20200101', end_date=ts_end_d)
    ipo_df.dropna(subset=["price"], inplace=True)

    w.start()
    for file_name in file_list:
        if file_name.split(".")[-1] == "xls":
            file_path = os.path.join(dir_path, file_name)
            raw_df = pd.read_table(file_path, encoding="gbk", converters={"发生日期": str, "证券代码": str})
            cal_gain_ht(file_name, raw_df, ipo_df, period)
    w.stop()
