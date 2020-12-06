#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 卖出 soc 并买入 wicc
import json

import time

from huobi import HuobiService
from robot import common_utils

# 是否 测试模式(进行回溯的时候数据都是从SQLite中读取的)
from robot.version_2 import robot_dao

is_debug = True

# 扣除手续费后剩下的点(huobi交易手续费2‰)
FEE_LEFT_PERCENT = 0.998

# 从SQLite中获取的测试数据, 每次拿一条
soc_skip = 0
wicc_skip = 0

# y = kx + n 回归方程 y = 9.0902 * x + 0.0468
g_K = 9.0907
g_N = 0.0468

# 因为数据是1min记录一次的(大约一下), 每次跳过60条就相当于没60min执行一次数据
g_interval_time = 30


# 获取买到的数量
def get_buy_count(order_id):
    orders = HuobiService.order_matchresults(order_id)
    if orders['status'] == 'ok':
        count = 0
        for i in xrange(len(orders['data'])):
            count = count + float(orders['data'][i]['filled-amount']) - float(orders['data'][i]['filled-fees'])
        return count
    else:
        # 如果一次不成功, 再试一次
        orders = HuobiService.order_matchresults(order_id)
        if orders['status'] == 'ok':
            count = 0
            for i in xrange(len(orders['data'])):
                count = count + orders['data'][i]['filled-amount'] - orders['data'][i]['filled-fees']
            return count
        else:
            # 第二次还不成功, 返回-1
            return -1


def sell_soc_and_buy_wicc(sell_nums):
    if not is_debug:
        print "正式环境调用sell_soc_and_buy_wicc, 卖soc买wicc"
        # 正式环境
        sell_soc_result = sell_soc(sell_nums)
        print "sell_soc_result = %s" % (str(sell_soc_result))
        if sell_soc_result:
            buy_wicc_result = buy_wicc()
            print "buy_wicc_result = %s" % (str(buy_wicc_result))
            if buy_wicc_result:
                time.sleep(1)
                # 获取成交了的数量
                count = get_buy_count(buy_wicc_result)
                if count != -1:
                    return count
                else:
                    exit()
                    return 0
            else:
                #  卖成功了却没买成功, 在试一次
                two_result = buy_wicc()
                if two_result:
                    time.sleep(1)
                    # 获取成交了的数量
                    count = get_buy_count(two_result)
                    if count != -1:
                        return count
                    else:
                        exit()
                        return 0
                else:
                    # 卖了却没买成功, 程序出问题了, 退出
                    exit()
                    return 0
    else:
        # 测试环境进行回测
        print "测试环境进行回测sell_soc_and_buy_wicc, 卖soc买wicc"
        soc_buy_price, soc_sell_price, wicc_buy_price, wicc_sell_price = robot_dao.get_debug_soc_wicc_data(
            soc_skip - 1, True)
        count = soc_buy_price * sell_nums * FEE_LEFT_PERCENT / wicc_sell_price * FEE_LEFT_PERCENT
        count = common_utils.get_round(count, 4)
        return count


# 卖出wicc 并买入 soc
def sell_wicc_and_buy_soc(sell_nums):
    if not is_debug:
        print "正式环境启动sell_wicc_and_buy_soc, 卖wicc买soc"
        # 正式环境
        sell_wicc_result = sell_wicc(sell_nums)
        print "sell_wicc_result = %s" % (str(sell_wicc_result))
        if sell_wicc_result:
            buy_soc_result = buy_soc()
            print "buy_soc_result = %s" % (str(buy_soc_result))
            if buy_soc_result:
                time.sleep(1)
                # 获取成交了的数量
                count = get_buy_count(buy_soc_result)
                if count != -1:
                    return count
                else:
                    exit()
                    return 0
            else:
                #  卖wicc成功, 买soc却失败了, 再试一次
                two_result = buy_soc()
                if two_result:
                    time.sleep(1)
                    # 获取成交了的数量
                    count = get_buy_count(two_result)
                    if count != -1:
                        return count
                    else:
                        exit()
                        return 0
                else:
                    # 卖了却没买成功, 程序出问题了, 退出
                    exit()
                    return 0
    else:
        # 测试环境进行回测
        print "测试环境进行回测sell_wicc_and_buy_soc, 卖wicc买soc"
        soc_buy_price, soc_sell_price, wicc_buy_price, wicc_sell_price = robot_dao.get_debug_soc_wicc_data(
            soc_skip - 1, True)
        count = wicc_buy_price * sell_nums * FEE_LEFT_PERCENT / soc_sell_price * FEE_LEFT_PERCENT
        count = common_utils.get_round(count, 4)
        return count


#  买入soc
def buy_soc():
    usdt_balance = get_coin_balance("usdt")
    print common_utils.get_json(usdt_balance, map)
    if usdt_balance:
        # 这里不抓异常, 出错就把程序停掉, 避免更大的损失
        buy_result = HuobiService.send_order(usdt_balance, source="api", symbol="socusdt", _type="buy-market")
        print common_utils.get_json(buy_result, map)
        if buy_result["status"] == "ok":
            return str(buy_result["data"])
    return ""


# 卖出soc
def sell_soc(sell_nums):
    # 限价卖  币币交易使用‘spot’账户的
    # buy_soc_result = HuobiService.send_order(amount = "1",source = "api", symbol = "socusdt",_type = "sell-limit",price = "0.0650")
    # 市价卖
    sell_result = HuobiService.send_order(amount=str(sell_nums), source="api", symbol="socusdt", _type="sell-market")
    print common_utils.get_json(sell_result, map)
    if sell_result["status"] == "ok":
        return str(sell_result["data"])
    return ""


#  买入wicc
def buy_wicc():
    usdt_balance = get_coin_balance("usdt")
    print common_utils.get_json(usdt_balance, map)
    if usdt_balance:
        # 这里不抓异常, 出错就把程序停掉, 避免更大的损失
        buy_result = HuobiService.send_order(usdt_balance, source="api", symbol="wiccusdt", _type="buy-market")
        print common_utils.get_json(buy_result, map)
        if buy_result["status"] == "ok":
            return str(buy_result["data"])
    return ""


# 卖出wicc
def sell_wicc(sell_nums):
    # 限价卖  币币交易使用‘spot’账户的
    # buy_soc_result = HuobiService.send_order(amount = "1",source = "api", symbol = "wiccusdt",_type = "sell-limit",price = "0.0650")
    # 市价卖
    print "sell_wicc方法中sell_nums:%s" % (str(sell_nums))
    sell_result = HuobiService.send_order(amount=float(sell_nums), source="api", symbol="wiccusdt", _type="sell-market")
    print common_utils.get_json(sell_result, map)
    if sell_result["status"] == "ok":
        return str(sell_result["data"])
    return ""


# 获取指定币的数量
def get_coin_balance(coin):
    if not is_debug:
        # 正式请求
        balance = HuobiService.get_balance()
        if balance['status'] == 'ok':
            result = 0
            for e in balance["data"]["list"]:
                if e["type"] == "trade" and e["currency"] == coin:
                    # result = float(int(float(e["balance"]) * 10000)) / 10000
                    result = common_utils.get_round(float(e["balance"]), 2)
                if result:
                    # 获取到想要的值, 跳出循环
                    break
            return result
        else:
            time.sleep(2)
            # 第一次请求失败, 再试一次
            balance = HuobiService.get_balance()
            if balance['status'] == 'ok':
                result = 0
                for e in balance["data"]["list"]:
                    if e["type"] == "trade" and e["currency"] == coin:
                        # result = float(int(float(e["balance"]) * 10000)) / 10000
                        result = common_utils.get_round(float(e["balance"]), 2)
                    if result:
                        # 获取到想要的值, 跳出循环
                        break
                return result
            else:
                # 第二次还失败, 这里停掉程序
                return -100
    else:
        # 测试模式, 设置 回测的数据
        json_count = common_utils.read_json("debug_count.json")
        if "soc" == coin:
            return json_count['soc_count']
        if "wicc" == coin:
            return json_count['wicc_count']
        return -100


# 我要买这个币, 所以获取卖盘第二的价格比较保险; 想卖的时候获取买盘第二个价格
def get_huobi_price(symbol, prin):
    if not is_debug:
        # 正式请求
        # 买盘价格
        buy_price = 0
        sell_price = 0
        try:
            huobi_content = HuobiService.get_depth(symbol, 'step0')
            # 这里拿的是买盘的第二个价格
            buy_price = huobi_content["tick"]["bids"][1][0]
            # 这里拿的是卖盘的第二个价格
            sell_price = huobi_content["tick"]["asks"][1][0]
            if prin:
                print json.dumps(huobi_content, default=map)
        except Exception, e:
            print "获取火币的%s价格出错:%s" % (symbol, e.message)
        return float(buy_price), float(sell_price)
    else:
        #  从SQLite中获取测试数据进行回测
        if symbol == 'socusdt':
            global soc_skip
            soc_buy_price, soc_sell_price, wicc_buy_price, wicc_sell_price = robot_dao.get_debug_soc_wicc_data(soc_skip,
                                                                                                               True)
            soc_skip = soc_skip + g_interval_time
            return float(soc_buy_price), float(soc_sell_price)
        elif symbol == 'wiccusdt':
            global wicc_skip
            soc_buy_price, soc_sell_price, wicc_buy_price, wicc_sell_price = robot_dao.get_debug_soc_wicc_data(
                wicc_skip, False)
            wicc_skip = wicc_skip + g_interval_time
            return float(wicc_buy_price), float(wicc_sell_price)


def set_debug(debug):
    global is_debug
    is_debug = debug


#  获取两个等差数列的两个公差
def get_deviation(n, max_index):
    one_deviation = 200.0 / (max_index + max_index * n)
    two_deviation = float(max_index) * one_deviation / (n - max_index + 1)
    return common_utils.get_round(one_deviation, 3), common_utils.get_round(two_deviation, 3)


def calc_by_soc(soc_price):
    return soc_price * g_K + g_N


def calc_by_wicc(wicc_price):
    return (wicc_price - g_N) / g_K


# 将交易数据写入数据库
def save_trade_data(create_time, state, soc_price, wicc_price, minus, percent, soc_count, wicc_count):
    if is_debug:
        state = "回测---" + state
        json_count = {"soc_count": soc_count, "wicc_count": wicc_count}
        common_utils.write_json("debug_count.json", json_count, map)
    robot_dao.insert_trade_data(create_time, state, soc_price, wicc_price, minus, percent, soc_count, wicc_count)


# 生成配置文件
def create_config():
    global g_K
    global g_N
    params = common_utils.read_json("params.json")

    g_K = params['g_K']
    g_N = params['g_N']

    config = {
        'is_debug': True,
        'soc': [],
        'wicc': []
    }
    point_size = params['point_size']
    max_index = params['max_index']
    one_deviation, two_deviation = get_deviation(point_size, max_index)
    for i in xrange(1, point_size + 1):
        if i <= max_index:
            point = i * one_deviation
        else:
            # 9 - 5 + 1 = 5      6 - 5 + 1
            point = (point_size - max_index + 1 - (i - max_index + 1) + 1) * two_deviation
        point = common_utils.get_round(point, 4)
        soc_obj = {'percent': point, 'state': 0, 'trade_count': 0}
        wicc_obj = {'percent': point, 'state': 0, 'trade_count': 0}
        config['soc'].append(soc_obj)
        config['wicc'].append(wicc_obj)
    json_count = {"soc_count": 0, "wicc_count": 1000}
    # json_count = {"soc_count": 100, "wicc_count": 0}

    if json_count["wicc_count"] == 0:
        # 单边开局(一开局只有soc), 记录wicc转换的数据
        for i in xrange(len(config['wicc'])):
            trade_count = json_count['soc_count'] / 200 * config['wicc'][i]['percent']
            config['wicc'][i]['trade_count'] = common_utils.get_round(trade_count, 2)
            config['wicc'][i]['state'] = 1
    elif json_count['soc_count'] == 0:
        # 单边开局(一开局只有wicc), 记录soc转换的数据
        for i in xrange(len(config['soc'])):
            trade_count = json_count['wicc_count'] / 200 * config['soc'][i]['percent']
            config['soc'][i]['trade_count'] = common_utils.get_round(trade_count, 2)
            config['soc'][i]['state'] = 1

    common_utils.write_json("config.json", config, map)
    common_utils.write_json("debug_count.json", json_count, map)


def exit():
    n = 1 / 0
    print n


if __name__ == "__main__":
    print "main start"
    # TODO 创建config的方法要慎重调用, 别把实际数据给覆盖了
    # create_config()
    # set_debug(False)
    # soc_count = get_coin_balance("soc")
    # print "soc_count = %s" % str(soc_count)
