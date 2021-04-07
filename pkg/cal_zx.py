import pandas as pd
import tushare as ts
import warnings
from pkg.utils import print_info
from pkg.secret import TS_TOKEN
from pkg.cal_ht import symbol_to_ts_code
from WindPy import w

warnings.filterwarnings("ignore")


def cal_gain_ht(df, ipo, start_d="20201001", end_d="20201231"):
    pro = ts.pro_api(TS_TOKEN)
    w.start()

    # 去除重复的行
    df.drop_duplicates(inplace=True)

    # 数据清洗
    df.columns = [item.replace("=\"", "").replace("\"", "") for item in df.columns]

    print(df)
    print(df.values)

    # 将中小板的代码进行 "0" 补全
    index_list = df.index
    for idx, item in zip(index_list, df["证券代码"]):
        if len(item) < 6:
            item = "{:0>6d}".format(int(item))
            print(item)
            df["证券代码"][idx] = item

    # 删除华宝添益
    df.drop(df[df["证券代码"] == "511990"].index, inplace=True)

    # 生成一个精简数据表，用于挑选指定时间内的新股
    df_op = df[start_d <= df["发生日期"]]
    df_op = df_op[(df_op["业务名称"] == "证券卖出") & (df_op["发生日期"] <= end_d)]
    df_op.reset_index(inplace=True)

    df_op_group = df_op.groupby(["证券代码"])[["成交数量", "清算金额"]].agg("sum").reset_index()
    print(df_op_group)

    # 生成一个包含新股入账信息的数据表
    df_ns = df[df["业务名称"].isin(["新股入帐", "红股入帐"])]
    print(df_ns)

    # 生成一个考察的新股列表
    ns_list = list()
    for ns_item in df_ns["证券代码"]:
        if ns_item in df_op_group["证券代码"].tolist():
            ns_list.append(ns_item)

    print(len(ns_list))

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
                item_dict[out_columns[0]] = ipo[ipo["ts_code"] == ts_code]["name"].tolist()[0]
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
                item_dict[out_columns[3]] = df_op_group[df_op_group["证券代码"] == ns_item]["清算金额"].tolist()[0]
                item_dict[out_columns[4]] = sell_num * 10
            else:
                item_dict[out_columns[3]] = df_op_group[df_op_group["证券代码"] == ns_item]["清算金额"].tolist()[0]
                item_dict[out_columns[4]] = sell_num
        else:
            print(item_dict[out_columns[0]])

        # 发行价
        if stock_type == "可转债":
            item_dict[out_columns[5]] = 100
        else:
            try:
                item_dict[out_columns[5]] = ipo[ipo["ts_code"] == ts_code]["price"].tolist()[0]
            except:
                item_dict[out_columns[5]] = w.wsd(
                    ts_code, "ipo_price2", "2020-12-31", "2020-12-31", "currencyType="
                ).Data[0][0]
        # 网下佣金
        if stock_type == "科创板":
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
    # 传统新股
    df_out = df_out.append(
        pd.Series({
            out_columns[0]: "传统新股",
            out_columns[7]: df_out_group[df_out_group[out_columns[-1]] == "传统新股"][out_columns[7]].tolist()[0]
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
    df_out.to_excel("output.xlsx", index=None)

    w.stop()


if __name__ == '__main__':
    raw_df = pd.read_table("高升3号.xls", encoding="gbk", converters={"发生日期": str, "证券代码": str})
    ipo_df = pd.read_csv("ipo.csv", index_col=0, converters={"发生日期": str, "证券代码": str})
    cal_gain_ht(raw_df, ipo_df, "20201001", "20201231")
