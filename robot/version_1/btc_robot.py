#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import time

from huobi import HuobiService
from gate import GateClient
from okex import OkexClient

# 平的状态soc == 0, 买入的状态soc == 1; 卖出的状态soc == -1
from robot import common_utils
from robot.version_1 import robot_dao

soc_count = 1

btc_result_name = "btc_result.txt"
soc_result_name = "soc_result.txt"


def get_huobi_price_old(symbol, prin):
    huobi_price = 0
    try:
        huobi_content = HuobiService.get_trade(symbol)
        huobi_price = huobi_content["tick"]["data"][0]["price"]
        if prin:
            print json.dumps(huobi_content, default=map)
    except Exception, e:
        print "获取火币的%s价格出错:%s" % (symbol, e.message)
    return float(huobi_price)


# 我要买这个币, 所以获取卖盘第二的价格比较保险; 想卖的时候获取买盘第二个价格
def get_huobi_price(symbol, prin):
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


def get_gate_price(symbol, prin):
    gate_price = 0
    try:
        gate_content = GateClient.gate_query.ticker(symbol)
        gate_price = gate_content["last"]
        if prin:
            print common_utils.get_json(gate_content, map)
    except Exception, e:
        print "获取gate的%s价格出错:%s" % (symbol, e.message)
    return float(gate_price)


def get_ok_price(symbol, prin):
    ok_price = 0
    try:
        ok_content = OkexClient.okcoinSpot.ticker(symbol)
        ok_price = ok_content["ticker"]["buy"]
        if prin:
            print json.dumps(ok_content, default=map)
    except Exception, e:
        print "获取ok的%s价格出错:%s" % (symbol, e.message)
    return float(ok_price)


def get_format_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def get_btc_data():
    # 无限循环, 60s 刷新一次
    huobi_btc_price = get_huobi_price_old("btcusdt", False)
    gate_btc_price = get_gate_price('btc_usdt', False)
    ok_btc_price = get_ok_price('btc_usd', False)
    msg = "%s   get_btc_data启动了  --------  " \
          "huobi_btc_price = %s" \
          "; gate_btc_price = %s" \
          "; ok_btc_price = %s" \
          % (get_format_time(), str(huobi_btc_price), str(gate_btc_price), str(ok_btc_price))

    btc_prices = []
    if huobi_btc_price:
        btc_prices.append(huobi_btc_price)
    if gate_btc_price:
        btc_prices.append(gate_btc_price)
    if ok_btc_price:
        btc_prices.append(ok_btc_price)

    if len(btc_prices) >= 2:
        # 如果有两个价格没有获取到, 那就不用玩了
        # 排序, 然后取最大和最小值
        btc_prices.sort()
        max_price = btc_prices[-1]
        min_price = btc_prices[0]
        minus = max_price - min_price
        percent = minus * 100 / min_price
        msg = msg + "; percent = %s" % (str(percent))
        # 写入数据库
        robot_dao.insert_btc_data(get_format_time(), float(huobi_btc_price), float(ok_btc_price), float(gate_btc_price),
                                  float(minus), percent)
        if percent >= 1:
            print "超过1个点, 也许有利可图, 记录价格"
            all_price = [huobi_btc_price, gate_btc_price, ok_btc_price]
            all_price_str = ["huobi_btc_price", "gate_btc_price", "ok_btc_price"]

            message = "%s和%s相差%s个点 --- %s" % (all_price_str[all_price.index(min_price)],
                                              all_price_str[all_price.index(max_price)],
                                              str(percent),
                                              get_format_time())
            print message
    print msg


def get_soc_wicc_data():
    global soc_count

    soc_buy_price, soc_sell_price = get_huobi_price("socusdt", False)
    wicc_buy_price, wicc_sell_price = get_huobi_price("wiccusdt", False)
    msg = "%s get_soc_wicc_data启动了  --------  " \
          "soc_buy_price = %s" \
          "; soc_sell_price = %s" \
          "; wicc_buy_price = %s" \
          "; wicc_sell_price = %s" \
          % (get_format_time(), str(soc_buy_price), str(soc_sell_price), str(wicc_buy_price), str(wicc_sell_price))

    if soc_buy_price and soc_sell_price and wicc_buy_price and wicc_buy_price:
        # 4个价格不为0, 说明网络获取成功

        # soc价格更高的时候, 找soc的买盘价格(卖soc) - wicc的卖盘价格(买wicc) / wicc的卖盘价格
        soc_expensive_percent = common_utils.get_round(
            float((soc_buy_price * 10 - wicc_sell_price) * 100 / wicc_sell_price), 5)
        # wicc价格更高的时候, 找wicc的买盘价格(卖wicc) - soc的卖盘价格(买soc) / soc的卖盘价格
        wicc_expensive_percent = common_utils.get_round(
            float((wicc_buy_price - soc_sell_price * 10) * 100 / (soc_sell_price * 10)), 5)

        percent = max(soc_expensive_percent, wicc_expensive_percent)
        if percent == wicc_expensive_percent:
            minus = wicc_buy_price - soc_sell_price * 10
        else:
            minus = soc_buy_price * 10 - wicc_sell_price

        msg = msg + "; percent = %s" % (str(percent))
        # 写入数据库
        robot_dao.insert_soc_wicc(get_format_time(), float(soc_buy_price), float(soc_sell_price),
                                  float(wicc_buy_price), float(wicc_sell_price), float(minus), percent)
        # (soc和wicc偏差不大的情况下) 平的状态下
        if soc_count == 0:
            if percent >= 15:
                if percent == wicc_expensive_percent:
                    # soc价格低, 买入soc
                    message = "相差为%s, 可以买入soc了 --- %s" % (str(percent), get_format_time())
                    wicc_balance = get_coin_balance("wicc")
                    if wicc_balance != 0:
                        sell_wicc_and_buy_soc(wicc_balance, 1)
                    print message
                    print msg
                    return
            if percent >= 5.5:
                if percent != wicc_expensive_percent:
                    # 卖出soc, 买入wicc
                    message = "相差为%s, 可以买入wicc了 --- %s" % (str(percent), get_format_time())
                    soc_balance = get_coin_balance("soc")
                    if soc_balance != 0:
                        sell_soc_and_buy_wicc(soc_balance, -1)
                    print message
                    print msg
                    return
        # 持有soc状态下
        if soc_count == 1:
            # 这里重新计算一下平soc的百分比
            sell_soc_percent = common_utils.get_round(
                float((wicc_sell_price - soc_buy_price * 10) * 100 / (soc_buy_price * 10)), 5)
            # 卖soc(看买盘价格), 买wicc(看卖盘价格)
            if wicc_sell_price <= soc_buy_price * 10:
                message = "wicc比soc便宜, 可以平了 --- %s" % get_format_time()
                print message
                soc_balance = get_coin_balance("soc")
                if soc_balance != 0:
                    sell_soc_and_buy_wicc(common_utils.get_round(float(soc_balance * 2 / 3), 2), 0)
            elif sell_soc_percent >= 0 and sell_soc_percent <= 0.5:
                message = "相差小于千分之5, 可以平了 --- %s" % get_format_time()
                print message
                soc_balance = get_coin_balance("soc")
                if soc_balance != 0:
                    sell_soc_and_buy_wicc(common_utils.get_round(float(soc_balance * 2 / 3), 2), 0)
            print msg
            return
        # 持有wicc状态下
        if soc_count == -1:
            # 这里重新计算一下平wicc的百分比
            wicc_sell_percent = common_utils.get_round(
                float((soc_sell_price * 10 - wicc_buy_price) * 100 / wicc_buy_price), 5)
            # 卖wicc(看买盘价格), 买soc(看卖盘价格)
            if wicc_buy_price >= soc_sell_price * 10:
                message = "wicc比soc贵, 可以平了 --- %s" % get_format_time()
                print message
                wicc_balance = get_coin_balance("wicc")
                if wicc_balance != 0:
                    sell_wicc_and_buy_soc(common_utils.get_round(float(wicc_balance  * 1 / 3), 2), 0)
            elif wicc_sell_percent >= 0 and wicc_sell_percent <= 0.5:
                message = "相差小于千分之5, 可以平了 --- %s" % get_format_time()
                print message
                wicc_balance = get_coin_balance("wicc")
                if wicc_balance != 0:
                    sell_wicc_and_buy_soc(common_utils.get_round(float(wicc_balance  * 1 / 3), 2), 0)
            print msg
            return

        # 持有soc的状态
        # if soc_count == 1:
        #     if percent <= 24:
        #         if max_price == wicc_price:
        #             # 还是soc价格低, 卖掉1000 soc
        #             sell_soc_result = sell_soc(10000)
        #             print "sell_soc_result = %s" % (str(sell_soc_result))
        #             if sell_soc_result:
        #                 buy_wicc_result = buy_wicc()
        #                 print "buy_wicc_result = %s" % (str(buy_wicc_result))
        #                 if buy_wicc_result:
        #                     robot_dao.insert_trade_data(get_format_time(), "卖soc买wicc")
        #                     soc_count = -1
        #                 else:
        #                     #  卖成功了却没买成功, 在试一次
        #                     two_result = buy_wicc()
        #                     if two_result:
        #                         soc_count = -1
        #                     else:
        #                         soc_count = -22
        #             message = "相差为%s, 卖soc买wicc --- %s" % (str(percent), get_format_time())
        #         else:
        #             # wicc价格低, 这里做平仓, 然后今晚不操作了
        #             message = "相差为%s, 平仓后不再操作--- %s" % (str(percent), get_format_time())
        #             soc_count = -22
        #             robot_dao.insert_trade_data(get_format_time(), message)
        #         print message
        #         return
        # elif soc_count == -1:
        #     #  已经买了wicc的状态
        #     if percent >= 28.5:
        #         wicc_balance = get_coin_balance("wicc")
        #         print "wicc_balance = %s" % (str(wicc_balance))
        #         if wicc_balance:
        #             sell_wicc_result = sell_wicc(wicc_balance)
        #             print "sell_wicc_result = %s" % (str(sell_wicc_result))
        #             if sell_wicc_result:
        #                 buy_soc_result = buy_soc()
        #                 print "buy_soc_result = %s" % (str(buy_soc_result))
        #                 if buy_soc_result:
        #                     soc_count = 1
        #                     robot_dao.insert_trade_data(get_format_time(), "卖wicc买soc")
        #                 else:
        #                     #  卖wicc成功, 买soc却失败了, 再试一次
        #                     two_result = buy_soc()
        #                     if two_result:
        #                         soc_count = 1
        #                     else:
        #                         soc_count = -22
    print msg


def get_soc_wicc_balance():
    balance = HuobiService.get_balance()
    soc_balance = 0
    wicc_balance = 0
    for e in balance["data"]["list"]:
        if e["type"] == "trade" and e["currency"] == "soc":
            soc_balance = int(float(e["balance"]))
        if e["type"] == "trade" and e["currency"] == "wicc":
            wicc_balance = int(float(e["balance"]))
        if soc_balance and wicc_balance:
            break
    j_balance = common_utils.get_json(balance, map)
    # print j_balance
    print "soc_balance = %s; wicc_balance = %s" % (str(soc_balance), str(wicc_balance))


def watch_dog():
    while True:
        # get_btc_data()
        get_soc_wicc_data()
        time.sleep(60)


# 获取指定币的数量
def get_coin_balance(coin):
    balance = HuobiService.get_balance()
    result = 0
    for e in balance["data"]["list"]:
        if e["type"] == "trade" and e["currency"] == coin:
            # result = float(int(float(e["balance"]) * 10000)) / 10000
            result = common_utils.get_round(float(e["balance"]), 4)
        if result:
            # 获取到想要的值, 跳出循环
            break
    return result


#  买入soc
def buy_soc():
    usdt_balance = get_coin_balance("usdt")
    print common_utils.get_json(usdt_balance, map)
    if usdt_balance:
        # 这里不抓异常, 出错就把程序停掉, 避免更大的损失
        buy_result = HuobiService.send_order(usdt_balance, source="api", symbol="socusdt", _type="buy-market")
        print common_utils.get_json(buy_result, map)
        if buy_result["status"] == "ok":
            return True
    return False


# 卖出 soc 并买入 wicc
def sell_soc_and_buy_wicc(sell_nums, status):
    global soc_count
    sell_soc_result = sell_soc(sell_nums)
    print "sell_soc_result = %s" % (str(sell_soc_result))
    if sell_soc_result:
        buy_wicc_result = buy_wicc()
        print "buy_wicc_result = %s" % (str(buy_wicc_result))
        if buy_wicc_result:
            robot_dao.insert_trade_data(get_format_time(), "卖soc买wicc")
            soc_count = status
        else:
            #  卖成功了却没买成功, 在试一次
            two_result = buy_wicc()
            if two_result:
                soc_count = status
            else:
                soc_count = -1111


# 卖出wicc 并买入 soc
def sell_wicc_and_buy_soc(sell_nums, status):
    global soc_count
    sell_wicc_result = sell_wicc(sell_nums)
    print "sell_wicc_result = %s" % (str(sell_wicc_result))
    if sell_wicc_result:
        buy_soc_result = buy_soc()
        print "buy_soc_result = %s" % (str(buy_soc_result))
        if buy_soc_result:
            soc_count = status
            robot_dao.insert_trade_data(get_format_time(), "卖wicc买soc")
        else:
            #  卖wicc成功, 买soc却失败了, 再试一次
            two_result = buy_soc()
            if two_result:
                soc_count = status
            else:
                soc_count = -1111


# 卖出soc
def sell_soc(sell_nums):
    # 限价卖  币币交易使用‘spot’账户的
    # buy_soc_result = HuobiService.send_order(amount = "1",source = "api", symbol = "socusdt",_type = "sell-limit",price = "0.0650")
    # 市价卖
    sell_result = HuobiService.send_order(amount=str(sell_nums), source="api", symbol="socusdt", _type="sell-market")
    print common_utils.get_json(sell_result, map)
    if sell_result["status"] == "ok":
        return True
    return False


#  买入wicc
def buy_wicc():
    usdt_balance = get_coin_balance("usdt")
    print common_utils.get_json(usdt_balance, map)
    if usdt_balance:
        # 这里不抓异常, 出错就把程序停掉, 避免更大的损失
        buy_result = HuobiService.send_order(usdt_balance, source="api", symbol="wiccusdt", _type="buy-market")
        print common_utils.get_json(buy_result, map)
        if buy_result["status"] == "ok":
            return True
    return False


# 卖出wicc
def sell_wicc(sell_nums):
    # 限价卖  币币交易使用‘spot’账户的
    # buy_soc_result = HuobiService.send_order(amount = "1",source = "api", symbol = "wiccusdt",_type = "sell-limit",price = "0.0650")
    # 市价卖
    print "sell_wicc方法中sell_nums:%s" % (str(sell_nums))
    sell_result = HuobiService.send_order(amount=float(sell_nums), source="api", symbol="wiccusdt", _type="sell-market")
    print common_utils.get_json(sell_result, map)
    if sell_result["status"] == "ok":
        return True
    return False


if __name__ == '__main__':
    print "task start"

    robot_dao.create_table()
    watch_dog()
