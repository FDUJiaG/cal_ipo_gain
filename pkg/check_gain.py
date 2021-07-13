import os
import pandas as pd
from shutil import copyfile
import os
from pkg.utils import print_info


def check_gain(dir_s, dir_d, dir_c, ignore_cyb=True):
    s_list = os.listdir(dir_s)
    d_list = os.listdir(dir_d)
    df_out = pd.DataFrame(columns=["产品", "差距"])

    if len(s_list) == 0:
        print(print_info("E"), end=" ")
        print("The path: {} is empty.".format(dir_s))
        return 0

    # 循环自己计算的所有收益表
    judge = 0
    for s_item in s_list:

        if s_item.split(".")[-1] == "xlsx":
            if "号" in s_item:
                s_name = s_item.split("号")[0] + "号"
            else:
                s_name = s_item[:2]

            df_s = pd.read_excel(
                os.path.join(dir_s, s_item), index_col=0
            )

            # df_s = pd.read_excel(
            #     os.path.join(dir_s, s_item), header=1, index_col=0
            # )

            # 获取自己计算的净利润
            # s_gain = df_s["净利润"].tolist()[-1]
            s_gain = df_s["净利润"][["可转债", "传统新股", "科创板", "注册创业板", "合计"]]

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
                    os.path.join(dir_d, d_name), header=1, index_col=0
                )

                # 获取收益程序计算的净利润
                # d_gain = df_d["净利润"].tolist()[-1]
                d_gain = df_d["净利润"][["可转债", "传统新股", "科创板", "注册创业板", "合计"]]

                if abs(s_gain[3] - d_gain[3]) + abs(s_gain[-1] - d_gain[-1]) <= 1e1:
                    # 将没有问题的版本单独存出
                    copyfile(
                        os.path.join(dir_d, d_name),
                        os.path.join(dir_c, d_name)
                    )
                    judge += 1
                elif abs(s_gain[0] - d_gain[0]) + abs(s_gain[1] - d_gain[1]) + abs(s_gain[2] - d_gain[2]) <= 1e1:
                    if ignore_cyb and abs(s_gain[3] - d_gain[3]) <= 1e1:
                        copyfile(
                            os.path.join(dir_d, d_name),
                            os.path.join(dir_c, d_name)
                        )
                        judge += 0.001
                        print(print_info("W"), end=" ")
                        print(
                            "{:<6s} Warning: The variance amount of CYB is {:10.2f}.".format(
                                s_name, s_gain[3] - d_gain[3]
                            )
                        )
                        df_out = df_out.append({"产品": s_name, "差距": s_gain[3] - d_gain[3]}, ignore_index=True)
                    else:
                        print(print_info("W"), end=" ")
                        print(
                            "{:<6s} Warning: self-calculation's CYB: {:>10.2f} is not equal to"
                            " the dpf-calculation's CYB: {:10.2f}, "
                            "The variance amount of CYB is {:10.2f}.".format(
                                s_name, s_gain[3], d_gain[3], s_gain[3] - d_gain[3]
                            )
                        )
                else:
                    print(print_info("W"), end=" ")
                    print(
                        "{:<6s} Warning: self-calculation: {:>10.2f} is not equal to the dpf-calculation: {:10.2f}, "
                        "The variance amount is {:10.2f}. \n"
                        "The variance amount of KZZ is {:10.2f}. "
                        "The variance amount of CTG is {:10.2f}. "
                        "The variance amount of KCB is {:10.2f}.".format(
                            s_name, s_gain[-1], d_gain[-1], s_gain[-1] - d_gain[-1],
                            s_gain[0] - d_gain[0],
                            s_gain[1] - d_gain[1],
                            s_gain[2] - d_gain[2],
                        )
                    )

    df_out.to_excel("test.xlsx", index=None)
    return judge


if __name__ == '__main__':
    cal_quarter = "2021Q2"
    self_path = os.path.join(os.path.abspath(".."), "output", cal_quarter)
    dpf_path = os.path.join(os.path.abspath(".."), "dpf", cal_quarter)
    checked_path = os.path.join(os.path.abspath(".."), "output", "checked", cal_quarter)
    isExists = os.path.exists(checked_path)
    # 判断结果
    if not isExists:
        os.makedirs(checked_path)
        print(print_info(), end=" ")
        print("Successfully created the path: {}.".format(checked_path))
    else:
        print(print_info(), end=" ")
        print("Please use the path: {}.".format(checked_path))
    judge_value = check_gain(self_path, dpf_path, checked_path)
    print(print_info(), end=" ")
    print("The Judge Value is: {:.3f}".format(judge_value))
