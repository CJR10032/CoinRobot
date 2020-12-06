#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
基于协整的搬砖策略: 参考: https://www.joinquant.com/post/1810
soc和wicc的存在协整关系, 这里是镰刀2.0版本, 加入了海龟策略的思想
'''
import json

import time

from robot import common_utils
from robot.common_utils import get_format_time
from robot.version_2 import soc_wicc_helper, robot_dao
from robot.version_2.soc_wicc_helper import get_huobi_price, calc_by_soc

# 配置信息
g_config = {}

# 从16跌后到14的时候, 把16点位买的卖出
g_delta_point = 3

# 无限循环 while 的标志, 正式环境不用管, 回测的时候可以修改该标识结束程序
g_run = True

# 每次任务间隔60s
INTERVAL_SLEEP_TIME = 60

# 需要调整币的比例, 这里如果之前没运行过2.0调整策略, 最好是调整一下, 如果是运行2.0策略时中途断掉的, 就不需要了
# (想不出什么好的分法...这里手动协整)
g_need_balance = False

# soc的持有量, 精确到2位小数
g_soc_count = 0

# wicc的持有量, 精确到2位小数
g_wicc_count = 0

# 打算卖wicc买soc, 在网络结果回来之前的标识位
WICC_TO_SOC_TEMP_STATE = 2

# 打算卖soc买wicc, 在网络结果回来之前的标识位
SOC_TO_WICC_TEMP_STATE = 3

# 已经交易的状态
HAS_TRADE_STATE = 1

# 默认装填, 没有发生交易的状态
NORMAL_STATE = 0

# 循环次数
g_run_count = 0

# soc和wicc的币的个数小数点保留位数
COUNT_DECIMAL = 2

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
    global g_soc_count
    global g_wicc_count
    global g_max_has_soc_count, g_max_trans_soc_count, g_max_has_wicc_count, g_max_trans_wicc_count

    soc_buy_price, soc_sell_price = get_huobi_price("socusdt", False)
    wicc_buy_price, wicc_sell_price = get_huobi_price("wiccusdt", False)
    msg = "%s 2.0的 get_soc_wicc_data启动了  --------  " \
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
        if g_config['is_debug']:
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

        if not g_config['is_debug']:
            # 正式交易的时候记录每次获取的数据
            robot_dao.insert_soc_wicc(get_format_time(), float(soc_buy_price), float(soc_sell_price),
                                      float(wicc_buy_price), float(wicc_sell_price), float(soc_to_wicc_minus),
                                      float(wicc_to_soc_minus), float(soc_to_wicc_percent), float(wicc_to_soc_percent))

        if calc_by_soc(soc_buy_price) >= wicc_sell_price:
            print "soc贵, 卖soc买wicc流程"
            # =========================  1. 价格变成soc贵了, wicc上还有点位的话这里就卖掉  =========================
            change_count = 0
            end = len(g_config['wicc'])
            for i in xrange(0, end):
                if g_config['wicc'][i]['state'] == HAS_TRADE_STATE:
                    g_config['wicc'][i]['state'] = SOC_TO_WICC_TEMP_STATE
                    # 记录需要转换的数量
                    change_count = change_count + g_config['wicc'][i]['trade_count']

            if change_count != 0:
                change_count = common_utils.get_round(change_count, COUNT_DECIMAL)
                buy_wicc_count = soc_wicc_helper.sell_soc_and_buy_wicc(change_count)
                print "......卖%s个soc买%s个wicc" % (str(change_count), str(buy_wicc_count))
                if buy_wicc_count:
                    for i in xrange(0, end):
                        if g_config['wicc'][i]['state'] == SOC_TO_WICC_TEMP_STATE:
                            # 重置标识位
                            g_config['wicc'][i]['state'] = NORMAL_STATE
                            # 转换数量清零
                            g_config['wicc'][i]['trade_count'] = 0
                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count - change_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count + buy_wicc_count, COUNT_DECIMAL)

                    minus = soc_to_wicc_minus
                    percent = common_utils.get_round(soc_to_wicc_percent, 3)
                    state = "卖soc买wicc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_buy_price, wicc_sell_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    # 更新配置信息
                    save_config()
            # =========================  2. 当前点位下, 比该点位小的点位有没有进行转换(soc -> wicc)  =========================
            # 注意, 虽然是1 - n的点位划分的, 但是索引是从0开始的
            point = int(soc_to_wicc_percent)
            index = point - 1
            # 防止越界
            end = min(point, len(g_config['soc']))

            has_soc_to_wicc_percent = 0
            need_soc_to_wicc_percent = 0
            for i in xrange(0, end):
                # 比如现在是偏离 6个点, 索引就是0-5, 将里面state  == 0(这部分应该要转为wicc的)的值取出来
                if g_config['soc'][i]['state'] == NORMAL_STATE:
                    # 还需要买的
                    need_soc_to_wicc_percent = need_soc_to_wicc_percent + g_config['soc'][i]['percent']
                    # 把 标识位改为1(已经转为wicc), 等网络请求结果成功后, 再将原先的soc替换
                    g_config['soc'][i]['state'] = SOC_TO_WICC_TEMP_STATE
                elif g_config['soc'][i]['state'] == HAS_TRADE_STATE:
                    # 记录已经买了的百分比
                    has_soc_to_wicc_percent = has_soc_to_wicc_percent + g_config['soc'][i]['percent']

            # soc转wicc操作
            if need_soc_to_wicc_percent != 0:
                # 需要卖soc买wicc, 计算数量
                soc_sell_count = float(need_soc_to_wicc_percent) / (100 - has_soc_to_wicc_percent) * g_soc_count
                soc_sell_count = common_utils.get_round(soc_sell_count, COUNT_DECIMAL)
                # 卖soc买wicc
                buy_wicc_count = soc_wicc_helper.sell_soc_and_buy_wicc(soc_sell_count)
                print "......卖%s个soc买%s个wicc" % (str(soc_sell_count), str(buy_wicc_count))

                if buy_wicc_count != 0:
                    for i in xrange(0, end):
                        if g_config['soc'][i]['state'] == SOC_TO_WICC_TEMP_STATE:
                            # 修改标识位为已购买状态
                            g_config['soc'][i]['state'] = HAS_TRADE_STATE
                            # 计算购买的数量
                            there_count = buy_wicc_count * g_config['soc'][i]['percent'] / need_soc_to_wicc_percent
                            # 记录购买了的数量
                            g_config['soc'][i]['trade_count'] = common_utils.get_round(there_count, COUNT_DECIMAL)

                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count - soc_sell_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count + buy_wicc_count, COUNT_DECIMAL)
                    minus = soc_to_wicc_minus
                    percent = common_utils.get_round(soc_to_wicc_percent, 3)
                    state = "卖soc买wicc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_buy_price, wicc_sell_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    # 更新配置信息
                    save_config()
            # =========================  3. 当前点位下, 比该点位大g_delta_point的点位有没有换回来(wicc -> soc)  =========================
            # 在soc还是比wicc贵的情况下, 如果15个点的时候soc转wicc了, 现在滑到10个点, 那就把15个点转的wicc再转回soc
            # 这里是卖wicc买soc, 但是soc的价格比wicc贵
            percent = common_utils.get_round((calc_by_soc(soc_sell_price) - wicc_buy_price) * 100 / wicc_buy_price, 4)
            # 当前点位档次(注意, 索引从0开始总会比点位档次小1)
            point = int(percent)
            # 防止越界
            end = len(g_config['soc'])
            change_count = 0
            # 如果 point + g_delta_point >= end 了的话不会进入循环, change_count 一样等于0
            for i in xrange(point - 1 + g_delta_point, end):
                # 这里有点绕, 假设点位档次14, 索引是13 (point - 1), 应该转换15 (索引  + g_delta_point)以上档次的
                if g_config['soc'][i]['state'] == HAS_TRADE_STATE:
                    # 将标识位改为 想要转换的标识位
                    g_config['soc'][i]['state'] = WICC_TO_SOC_TEMP_STATE
                    # 计算之前一共买了多少个wicc
                    change_count = change_count + g_config['soc'][i]['trade_count']

            if change_count != 0:
                # 卖wicc买soc
                buy_soc_count = soc_wicc_helper.sell_wicc_and_buy_soc(change_count)
                print "......卖%s个wicc买%s个soc" % (str(change_count), str(buy_soc_count))
                if buy_soc_count != 0:
                    for i in xrange(point - 1 + g_delta_point, end):
                        if g_config['soc'][i]['state'] == WICC_TO_SOC_TEMP_STATE:
                            # 重置标识位
                            g_config['soc'][i]['state'] = NORMAL_STATE
                            # 转换数量清零
                            g_config['soc'][i]['trade_count'] = 0

                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count + buy_soc_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = g_wicc_count - change_count
                    minus = calc_by_soc(soc_sell_price) - wicc_buy_price
                    percent = common_utils.get_round(percent, 3)
                    state = "卖wicc买soc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_sell_price, wicc_buy_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    # 更新配置信息
                    save_config()
            # 结束 soc 比 wicc 贵的逻辑
            return

        if wicc_buy_price >= calc_by_soc(soc_sell_price):
            print "wicc贵, 卖wicc买soc流程"

            # =========================  1. 价格变成wicc贵了, soc上还有点位的话这里就卖掉  =========================
            change_count = 0
            end = len(g_config['soc'])
            for i in xrange(0, end):
                if g_config['soc'][i]['state'] == HAS_TRADE_STATE:
                    g_config['soc'][i]['state'] = WICC_TO_SOC_TEMP_STATE
                    # 记录需要转换的数量
                    change_count = change_count + g_config['soc'][i]['trade_count']

            if change_count != 0:
                change_count = common_utils.get_round(change_count, COUNT_DECIMAL)
                buy_soc_count = soc_wicc_helper.sell_wicc_and_buy_soc(change_count)
                print "......卖%s个wicc买%s个soc" % (str(change_count), str(buy_soc_count))
                if buy_soc_count:
                    for i in xrange(0, end):
                        if g_config['soc'][i]['state'] == WICC_TO_SOC_TEMP_STATE:
                            # 重置标识位
                            g_config['soc'][i]['state'] = NORMAL_STATE
                            # 转换数量清零
                            g_config['soc'][i]['trade_count'] = 0
                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count + buy_soc_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count - change_count, COUNT_DECIMAL)
                    minus = wicc_to_soc_minus
                    percent = common_utils.get_round(wicc_to_soc_percent, 3)
                    state = "卖wicc买soc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_sell_price, wicc_buy_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    # 更新配置信息
                    save_config()
            # =========================  2. 当前点位下, 比该点位小的点位有没有进行转换(wicc -> soc)  =========================
            # 注意, 虽然是1 - n的点位划分的, 但是索引是从0开始的
            point = int(wicc_to_soc_percent)
            index = point - 1
            # 防止越界
            end = min(point, len(g_config['wicc']))

            has_wicc_to_soc_percent = 0
            need_wicc_to_soc_percent = 0
            for i in xrange(0, end):
                # 比如现在是偏离 6个点, 索引就是0-5, 将里面state  == 0(这部分应该要转为soc的)的值取出来
                if g_config['wicc'][i]['state'] == NORMAL_STATE:
                    # 还需要买的
                    need_wicc_to_soc_percent = need_wicc_to_soc_percent + g_config['wicc'][i]['percent']
                    # 把 标识位改为1(已经转为wicc), 等网络请求结果成功后, 再将原先的soc替换
                    g_config['wicc'][i]['state'] = WICC_TO_SOC_TEMP_STATE
                elif g_config['wicc'][i]['state'] == HAS_TRADE_STATE:
                    # 记录已经买了的百分比
                    has_wicc_to_soc_percent = has_wicc_to_soc_percent + g_config['wicc'][i]['percent']

            # wicc转soc操作
            if need_wicc_to_soc_percent != 0:
                # 需要卖wicc买soc, 计算数量
                wicc_sell_count = float(need_wicc_to_soc_percent) / (100 - has_wicc_to_soc_percent) * g_wicc_count
                wicc_sell_count = common_utils.get_round(wicc_sell_count, COUNT_DECIMAL)

                # 卖wicc买soc
                buy_soc_count = soc_wicc_helper.sell_wicc_and_buy_soc(wicc_sell_count)
                print "......卖%s个wicc买%s个soc" % (str(wicc_sell_count), str(buy_soc_count))

                if buy_soc_count != 0:
                    for i in xrange(0, end):
                        if g_config['wicc'][i]['state'] == WICC_TO_SOC_TEMP_STATE:
                            # 修改标识位为已购买状态
                            g_config['wicc'][i]['state'] = HAS_TRADE_STATE
                            # 计算购买的数量
                            there_count = buy_soc_count * g_config['wicc'][i]['percent'] / need_wicc_to_soc_percent
                            # 记录购买了的数量
                            g_config['wicc'][i]['trade_count'] = common_utils.get_round(there_count, COUNT_DECIMAL)

                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count + buy_soc_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count - wicc_sell_count, COUNT_DECIMAL)
                    minus = wicc_to_soc_minus
                    percent = common_utils.get_round(wicc_to_soc_percent, 3)
                    state = "卖wicc买soc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_sell_price, wicc_buy_price,
                                                    minus, percent, g_soc_count, g_wicc_count)
                    # 更新配置信息
                    save_config()
            # =========================  3. 当前点位下, 比该点位大g_delta_point的点位有没有换回来(soc -> wicc)  =========================
            # 在wicc还是比soc贵的情况下, 如果15个点的时候wicc转soc了, 现在滑到10个点, 那就把15个点转的soc再转回wicc
            # 这里是卖soc买wicc, 但是wicc的价格比soc贵
            percent = common_utils.get_round(
                (wicc_sell_price - calc_by_soc(soc_buy_price)) * 100 / calc_by_soc(soc_buy_price), 4)
            # 当前点位档次(注意, 索引从0开始总会比点位档次小1)
            point = int(percent)
            # 防止越界
            end = len(g_config['wicc'])
            change_count = 0
            # 如果 point + g_delta_point >= end 了的话不会进入循环, change_count 一样等于0
            for i in xrange(point - 1 + g_delta_point, end):
                # 这里有点绕, 假设点位档次14, 索引是13 (point - 1), 应该转换15 (索引  + g_delta_point)以上档次的
                if g_config['wicc'][i]['state'] == HAS_TRADE_STATE:
                    # 将标识位改为 想要转换的标识位
                    g_config['wicc'][i]['state'] = SOC_TO_WICC_TEMP_STATE
                    # 计算之前一共买了多少个soc
                    change_count = change_count + g_config['wicc'][i]['trade_count']

            if change_count != 0:
                # 卖soc买wicc
                buy_wicc_count = soc_wicc_helper.sell_soc_and_buy_wicc(change_count)
                print "......卖%s个soc买%s个wicc" % (str(change_count), str(buy_wicc_count))
                if buy_wicc_count != 0:
                    for i in xrange(point - 1 + g_delta_point, end):
                        if g_config['wicc'][i]['state'] == SOC_TO_WICC_TEMP_STATE:
                            # 重置标识位
                            g_config['wicc'][i]['state'] = NORMAL_STATE
                            # 转换数量清零
                            g_config['wicc'][i]['trade_count'] = 0

                    # 记录soc数量的变化
                    g_soc_count = common_utils.get_round(g_soc_count - change_count, COUNT_DECIMAL)
                    # 记录wicc数量的变化
                    g_wicc_count = common_utils.get_round(g_wicc_count + buy_wicc_count, COUNT_DECIMAL)
                    minus = wicc_sell_price - calc_by_soc(soc_buy_price)
                    percent = common_utils.get_round(percent, 3)
                    state = "卖soc买wicc"
                    soc_wicc_helper.save_trade_data(get_format_time(), state, soc_buy_price, wicc_sell_price, minus,
                                                    percent, g_soc_count, g_wicc_count)
                    # 更新配置信息
                    save_config()
            # 结束 wicc 比 soc 贵的逻辑
            return

    else:
        # 获取到的价格有0出现
        if g_config['is_debug']:
            # 测试环境说明 已经没有数据了
            global g_run
            g_run = False
            print "=======回测结束======="
        else:
            # 正式环境中, 可能由于网络问题, 没有拿到价格, 这里把信息打印出来
            msg = msg
            print msg


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


#  打印分隔符
def print_divider():
    print "=" * 140


# 初始化
def init_config():
    global g_config
    global g_delta_point
    print "==========init_config方法调用了 start=========="
    g_config = common_utils.read_json("config.json")
    print "is_debug = %s " % str(g_config['is_debug'])
    soc_wicc_helper.set_debug(g_config['is_debug'])
    try:
        params = common_utils.read_json("params.json")
        g_delta_point = params['g_delta_point']
    except Exception, e:
        print e.message
    print "==========init_config方法调用了 end=========="


# 使用协整策略在soc和wicc之间进行搬砖
def soc_wicc_task():
    global g_run_count
    init_config()
    if g_need_balance:
        balance_soc_wicc()
    while g_run:
        if g_run_count * INTERVAL_SLEEP_TIME % 21600 == 0:
            if not g_config['is_debug'] or g_run_count == 0:
                # 每间隔6小时纠正一次soc_count和wicc_count
                print "校正g_soc_count和g_wicc_gount的值"
                get_wicc_soc_count()
        get_soc_wicc_data()
        if g_run:
            print_divider()
        # 循环次数+1
        g_run_count = g_run_count + 1
        time.sleep(INTERVAL_SLEEP_TIME)


# 根据当前比例调配两个币
def balance_soc_wicc():
    print "balance_soc_wicc方法调用了-----------进行协整策略之前要先进行币的分配"
    # 获取当前账户两个币种的数量
    get_wicc_soc_count()
    # 获取当前价格
    soc_buy_price, soc_sell_price = get_huobi_price("socusdt", False)
    wicc_buy_price, wicc_sell_price = get_huobi_price("wiccusdt", False)

    if soc_buy_price and soc_sell_price and wicc_buy_price and wicc_buy_price:
        # 4个价格不为0, 说明网络获取成功

        # soc价格更高的时候, 找soc的买盘价格(卖soc) - wicc的卖盘价格(买wicc) / wicc的卖盘价格
        soc_to_wicc_minus = calc_by_soc(soc_buy_price) - wicc_sell_price
        soc_to_wicc_percent = common_utils.get_round((soc_to_wicc_minus * 100 / wicc_sell_price), 4)

        # wicc价格更高的时候, 找wicc的买盘价格(卖wicc) - soc的卖盘价格(买soc) / soc的卖盘价格
        wicc_to_soc_minus = wicc_buy_price - calc_by_soc(soc_sell_price)
        wicc_to_soc_percent = common_utils.get_round((wicc_to_soc_minus * 100 / calc_by_soc(soc_sell_price)), 4)

        if calc_by_soc(soc_buy_price) >= wicc_sell_price:
            print "soc价格贵时候的调配"
            # 结束 soc 比 wicc 贵的协整逻辑
            return

        if wicc_buy_price >= calc_by_soc(soc_sell_price):
            print "wicc价格贵时候的调配"
            # 结束 wicc 比 soc 贵的协整的逻辑
            return
    else:
        print "在协整方法中, 获取soc和wicc的价格中有0, 协整失败, 停止程序"
        soc_wicc_helper.exit()


# 每次交易后保存配置信息
def save_config():
    common_utils.write_json("config.json", g_config, map)


if __name__ == "__main__":
    # TODO: 注意删除
    # soc_wicc_helper.create_config()

    print "main start"
    robot_dao.create_table()
    soc_wicc_task()
