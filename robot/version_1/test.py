#!/usr/bin/env python
# -*- coding: utf-8 -*-


# coding:utf-8
import urllib
import re

import time

from huobi import HuobiService
from robot import common_utils

file = open("spider_eamil.txt", "w+")

# url = "http://tieba.baidu.com/p/5865014625?pn="
# url = "http://tieba.baidu.com/p/5861525771?pn="
# url = "http://tieba.baidu.com/p/5853211433?pn="
# url = "http://tieba.baidu.com/p/5867307325?pn="
url = "http://tieba.baidu.com/p/5845929935?pn="


def get_ye(url):
    html = urllib.urlopen(url).read()
    reyuan = r'<a href=".*?pn=(.*?)">尾页</a>'
    index = 1
    try:
        recom = re.compile(reyuan)
        refind = re.findall(recom, html)
        index = refind[0]
    except Exception, e:
        print "获取页数出错:%s" % (e.message)
    return index


def get_email():
    i = 1
    j = 1
    all_indexs = get_ye(url)
    while i <= int(all_indexs):
        content = urllib.urlopen(url + str(i)).read()
        print("现在在下载第" + str(i) + "页，总共" + str(all_indexs) + "页")
        i += 1
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}'
        items = re.findall(pattern, content)
        for item in items:
            file.write(item + '\n')
            j += 1
    else:
        print "结束"
        file.write(str(j) + '\n')
        print j
        file.close()


def get_data_price():
    conn = robot_dao.connect_db()
    c = conn.cursor()

    sql = "SELECT buy_soc_price from soc_wicc limit 350"
    cursor = c.execute(sql)
    for row in cursor:
        # print "ID = ", row[0]
        # print "email =", row[1]
        # print "url = ", row[2], "\n"
        print row[0]
    conn.close()


def get_soc_wicc_day_prices():
    # 2018-09-12  今天取前百日(本来想取200, 但是soc和wicc对usdt的交易没这么多数据)的数据算出 k = 9.0902; n = 0.0468
    # soc_kline = HuobiService.get_kline("socusdt", "1day", "100")

    '''
     2018-09-18 11:11 今天取百日数据算的 k = 6.9950; n = 0.1150; 用这组数据回测收益较低, 所以这里取106日的数据试试
     2018-09-18 106日的数据算出来 k = 9.1002; n = 0.0458
    '''
    days = 106
    soc_kline = HuobiService.get_kline("socusdt", "1day", "%d" % days)
    soc_day_prices = []
    for soc_bean in soc_kline['data']:
        soc_day_prices.append(float(soc_bean['close']))
    print soc_day_prices
    common_utils.write_json("soc_day_prices.txt", soc_day_prices, list)

    time.sleep(5)

    wicc_kline = HuobiService.get_kline("wiccusdt", "1day", "%d" % days)
    wicc_day_prices = []
    for wicc_bean in wicc_kline['data']:
        wicc_day_prices.append(float(wicc_bean['close']))
    print wicc_day_prices
    common_utils.write_json("wicc_day_prices.txt", wicc_day_prices, list)


if __name__ == "__main__":
    print "test main start"
    # get_soc_wicc_day_prices()
    # content = HuobiService.orders_matchresults("socusdt")
    # 12350913620
    content = HuobiService.order_matchresults("12808178820")
    print common_utils.get_json(content, map)

