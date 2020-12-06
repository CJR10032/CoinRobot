#!/usr/bin/env python
# -*- coding: utf-8 -*-
from robot import common_utils
from robot.common_utils import get_format_time
from robot.version_2 import robot_dao, soc_wicc_helper

# 无限循环 while 的标志, 正式环境不用管, 回测的时候可以修改该标识结束程序
from robot.version_2.soc_wicc_helper import get_huobi_price, calc_by_soc
from robot.version_2.soc_wicc_robot import COUNT_DECIMAL

g_run = True

# 注意, 这里只做了debug版本进行回测
g_is_debug = True

# 循环次数
g_run_count = 0

# soc的持有量, 精确到2位小数
g_soc_count = 0

# wicc的持有量, 精确到2位小数
g_wicc_count = 0

# 平的状态soc == 0, 买入的状态soc == 1; 卖出的状态soc == -1
soc_state = 0

# 点差
g_delta_point = 2

# 记录soc最大的数量
g_max_has_soc_count = 0
# 记录转换后soc数量最大的值
g_max_trans_soc_count = 0
# 记录wicc最大的数量
g_max_has_wicc_count = 0
# 记录转换后wicc数量最大的值
g_max_trans_wicc_count = 0


# 获取soc和wicc的价格, 并计算是否交易
def get_soc_wicc_data():
    global soc_state
    global g_soc_count
    global g_wicc_count
    global g_max_has_soc_count, g_max_trans_soc_count, g_max_has_wicc_count, g_max_trans_wicc_count

    soc_buy_price, soc_sell_price = get_huobi_price("socusdt", False)
    wicc_buy_price, wicc_sell_price = get_huobi_price("wiccusdt", False)
    msg = "%s 1.1版本的 get_soc_wicc_data启动了  --------  单买单卖" \
          "\n soc_buy_price = %s" \
          "; soc_sell_price = %s" \
          "; wicc_buy_price = %s" \
          "; wicc_sell_price = %s" \
          % (get_format_time(), str(soc_buy_price), str(soc_sell_price), str(wicc_buy_price), str(wicc_sell_price))

    if soc_buy_price and soc_sell_price and wicc_buy_price and wicc_buy_price:
        # 4个价格不为0, 说明网络获取成功
        # soc价格更高的时候, 找soc的买盘价格(卖soc) - wicc的卖盘价格(买wicc) / wicc的卖盘价格
        soc_to_wicc_minus = calc_by_soc(soc_buy_price) - wicc_sell_price
        soc_to_wicc_percent = common_utils.get_round((soc_to_wicc_minus * 100 / wicc_sell_price), 4)

        # wicc价格更高的时候, 找wicc的买盘价格(卖wicc) - soc的卖盘价格(买soc) / soc的卖盘价格
        wicc_to_soc_minus = wicc_buy_price - calc_by_soc(soc_sell_price)
        wicc_to_soc_percent = common_utils.get_round((wicc_to_soc_minus * 100 / calc_by_soc(soc_sell_price)), 4)

        # 计算一下全部转化为soc会有多少
        all_trans_soc_count = wicc_buy_price * g_wicc_count * 0.998 / soc_sell_price * 0.998 + g_soc_count
        # 计算一下全部转化为wicc会有多少
        all_trans_wicc_count = soc_buy_price * g_soc_count * 0.998 / wicc_sell_price * 0.998 + g_wicc_count

        g_max_has_soc_count = max(g_max_has_soc_count, g_soc_count)
        g_max_trans_soc_count = max(g_max_trans_soc_count, all_trans_soc_count)

        g_max_has_wicc_count = max(g_max_has_wicc_count, g_wicc_count)
        g_max_trans_wicc_count = max(g_max_trans_wicc_count, all_trans_wicc_count)

        per_msg = "\n soc_to_wicc_minus = %s" \
                  "; wicc_to_soc_minus = %s" \
                  "; soc_to_wicc_percent = %s" \
                  "; wicc_to_soc_percent = %s" \
                  "\n all_trans_soc_count = %s" \
                  "; all_trans_wicc_count = %s" \
                  "; soc_count = %s" \
                  "; wicc_count = %s" % (
                      str(soc_to_wicc_minus),
                      str(wicc_to_soc_minus),
                      str(soc_to_wicc_percent),
                      str(wicc_to_soc_percent),
                      str(all_trans_soc_count),
                      str(all_trans_wicc_count),
                      str(g_soc_count),
                      str(g_wicc_count))

        msg = msg + per_msg
        if g_is_debug:
            per_msg = "\n max_has_soc_count = %s" \
                      "; max_trans_soc_count = %s" \
                      "; max_has_wicc_count = %s" \
                      "; max_trans_wicc_count = %s" % (
                          str(g_max_has_soc_count),
                          str(g_max_trans_soc_count),
                          str(g_max_has_wicc_count),
                          str(g_max_trans_wicc_count))
            msg = msg + per_msg

        print msg

        # (soc和wicc偏差不大的情况下) 平的状态下
        if soc_state == 0:
            if wicc_to_soc_percent >= g_delta_point:
                # 卖wicc买soc
                buy_soc_count = soc_wicc_helper.sell_wicc_and_buy_soc(g_wicc_count)
                print "......卖%s个wicc买%s个soc" % (str(g_wicc_count), str(buy_soc_count))
                # 记录soc数量的变化
                g_soc_count = common_utils.get_round(g_soc_count + buy_soc_count, COUNT_DECIMAL)
                # 记录wicc数量的变化
                g_wicc_count = 0
                # 持有soc
                soc_state = 1
                minus = wicc_to_soc_minus
                percent = common_utils.get_round(wicc_to_soc_percent, 3)
                state = "卖wicc买soc"
                soc_wicc_helper.save_trade_data(get_format_time(), state, soc_sell_price, wicc_buy_price, minus,
                                                percent, g_soc_count, g_wicc_count)
                return
            if soc_to_wicc_percent >= g_delta_point:
                # 卖soc买wicc
                buy_wicc_count = soc_wicc_helper.sell_soc_and_buy_wicc(g_soc_count)
                print "......卖%s个soc买%s个wicc" % (str(g_soc_count), str(buy_wicc_count))
                # 记录soc数量的变化
                g_soc_count = 0
                # 记录wicc数量的变化
                g_wicc_count = common_utils.get_round(g_wicc_count + buy_wicc_count, COUNT_DECIMAL)
                # 持有wicc
                soc_state = -1
                minus = soc_to_wicc_minus
                percent = common_utils.get_round(soc_to_wicc_percent, 3)
                state = "卖soc买wicc"
                soc_wicc_helper.save_trade_data(get_format_time(), state, soc_buy_price, wicc_sell_price, minus,
                                                percent, g_soc_count, g_wicc_count)
                return

            if soc_state == 1:
                # 持有soc的状态
                if soc_to_wicc_percent > 0:
                    soc_sell_count = common_utils.get_round(g_soc_count * 0.5, COUNT_DECIMAL)
                    # 卖soc买wicc
                    buy_wicc_count = soc_wicc_helper.sell_soc_and_buy_wicc(soc_sell_count)
                    print "......卖%s个soc买%s个wicc" % (str(soc_sell_count), str(buy_wicc_count))
                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count - soc_sell_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count + buy_wicc_count, COUNT_DECIMAL)
                    #  状态为平
                    soc_state = 0
                    minus = soc_to_wicc_minus
                    percent = common_utils.get_round(soc_to_wicc_percent, 3)
                    state = "卖soc买wicc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_buy_price, wicc_sell_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    return

            if soc_state == -1:
                # 持有wicc的状态
                if wicc_to_soc_percent > 0:
                    wicc_sell_count = common_utils.get_round(g_wicc_count * 0.5, COUNT_DECIMAL)
                    # 卖wicc买soc
                    buy_soc_count = soc_wicc_helper.sell_wicc_and_buy_soc(wicc_sell_count)
                    print "......卖%s个wicc买%s个soc" % (str(wicc_sell_count), str(buy_soc_count))
                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count + buy_soc_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count - wicc_sell_count, COUNT_DECIMAL)
                    # 状态为平
                    soc_state = 0
                    minus = wicc_to_soc_minus
                    percent = common_utils.get_round(wicc_to_soc_percent, 3)
                    state = "卖wicc买soc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_buy_price, wicc_sell_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    return
    else:
        # TODO 这个代码只做了测试版本用于查看测试数据, 如果测试结果比较理想, 需要实际跑的话要注意修改
        # TODO 然而跑过之后发现效果并不理想, 当然, 这里的写法也没有btc_robot里这么复杂, 但是还是决定用2.0版本了
        # 获取到的价格有0出现
        # 测试环境说明 已经没有数据了
        global g_run
        g_run = False
        print "=======回测结束======="


#  打印分隔符
def print_divider():
    print "=" * 134


def watch_task():
    global g_run_count
    while g_run:
        if g_run_count == 0:
            # 每间隔6小时纠正一次soc_count和wicc_count
            print "校正g_soc_count和g_wicc_gount的值"
            get_wicc_soc_count()
        get_soc_wicc_data()
        if g_run:
            print_divider()
        # 循环次数+1
        g_run_count = g_run_count + 1


# 获取soc和wicc的数量
def get_wicc_soc_count():
    print "get_wicc_soc_count方法调用了"
    global g_soc_count
    # 获取soc的数量
    g_soc_count = soc_wicc_helper.get_coin_balance("soc")
    global g_wicc_count
    # 获取wicc的数量
    g_wicc_count = soc_wicc_helper.get_coin_balance("wicc")

    if g_soc_count < 0 or g_wicc_count < 0:
        print "回测失败, 没有进行soc_count或者wicc_count的初始化"
        soc_wicc_helper.exit()


def debug_init():
    json_count = {"soc_count": 10000, "wicc_count": 1000}
    common_utils.write_json("debug_count.json", json_count, map)


if __name__ == "__main__":
    print "main start"
    debug_init()
    # robot_dao.create_table()
    watch_task()
