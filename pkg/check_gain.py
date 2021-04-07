import os
import pandas as pd
from pkg.utils import print_info


def check_gain(dir_s, dir_d):
    s_list = os.listdir(dir_s)
    d_list = os.listdir(dir_d)

    if len(s_list) == 0:
        print(print_info("E"), end=" ")
        print("The path: {} is empty.".format(dir_s))
        return 0

    # 循环自己计算的所有收益表
    for s_item in s_list:
        judge = 1

        if s_item.split(".")[-1] == "xlsx":
            if "号" in s_item:
                s_name = s_item.split("号")[0] + "号"
            else:
                s_name = s_item[:2]

            df_s = pd.read_excel(
                os.path.join(dir_s, s_item)
            )

            # 获取自己计算的净利润
            s_gain = df_s["净利润"].tolist()[-1]

            # 去总表中查找对应的表并比对
            count = 0
            for d_item in d_list:
                if s_name in d_item and d_item.split(".")[-1] == "xlsx":
                    d_name = d_item
                    count += 1

            if count == 0:
                print(print_info("E"), end=" ")
                print("Can not find the '{}' in the path: {}.".format(s_name, dir_d))
            elif count > 1:
                print(print_info("E"), end=" ")
                print("Not only one '{}' found in the path: {}.".format(s_name, dir_d))
            else:
                df_d = pd.read_excel(
                    os.path.join(dir_d, d_name), header=1
                )

                # 获取收益程序计算的净利润
                d_gain = df_d["净利润"].tolist()[-1]

                if s_gain - d_gain > 1e-5:
                    print(print_info("W"), end=" ")
                    print(
                        "{} Warning: self-calculation: {} is not equal to the dpf-calculation: {}".format(
                            s_name, s_gain, d_gain
                        )
                    )
                    judge *= 0

    return judge


if __name__ == '__main__':
    cal_quarter = "2021Q1"
    self_path = os.path.join(os.path.abspath(".."), "output", cal_quarter)
    dpf_path = os.path.join(os.path.abspath(".."), "dpf", cal_quarter)
    check_gain(self_path, dpf_path)
