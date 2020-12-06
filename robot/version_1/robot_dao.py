#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3

from robot import common_utils

DB_NAME = "CoinRobot.db"


# 连接数据库
def connect_db():
    return sqlite3.connect(DB_NAME)


# 提交数据
def commit_db(conn):
    conn.commit()


# 关闭数据库
def close_db(conn):
    conn.close()


# 创建表, 目前就2张表
def create_table():
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE soc_wicc
                                   (ID  INTEGER PRIMARY KEY   NOT NULL,
                                    create_time          TEXT,
                                    buy_soc_price        REAL,
                                    sell_soc_price       REAL,
                                    buy_wicc_price       REAL,
                                    sell_wicc_price      REAL,
                                    minus                REAL,
                                    percent              REAL);''')
    except Exception, e:
        print e.message

    try:
        c.execute('''CREATE TABLE btc_watch
                                       (ID  INTEGER PRIMARY KEY   NOT NULL,
                                        create_time           TEXT,
                                        huobi_btc             REAL,
                                        okex_btc              REAL, 
                                        gate_btc              REAL,
                                        minus                 REAL,
                                        percent               REAL);''')
    except Exception, e:
        print e.message

    try:
        c.execute('''CREATE TABLE trade_result
                                       (ID  INTEGER PRIMARY KEY   NOT NULL,
                                        create_time           TEXT,
                                        state                 TEXT,
                                        soc_price             REAL,
                                        wicc_price            REAL, 
                                        minus                 REAL,
                                        percent               REAL);''')
    except Exception, e:
        print e.message
    commit_db(conn)
    close_db(conn)
    print "Table created successfully";


def dict_2_str(dictin):
    '''
    将字典变成，key='value',key='value' 的形式
    '''
    tmplist = []
    for k, v in dictin.items():
        tmp = "%s='%s'" % (str(k), str(v))
        tmplist.append(' ' + tmp + ' ')
    return ','.join(tmplist)


# 往soc_wicc表中插入数据
def insert_soc_wicc(create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, minus, percent):
    conn = connect_db()
    c = conn.cursor()

    percent = float(int(percent * 1000)) / 1000
    values = " VALUES ('%s', %f, %f,%f, %f, %f, %.3f)" % (
        str(create_time), buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, minus, percent)
    sql = "INSERT INTO soc_wicc (create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, minus, percent)" + values
    try:
        c.execute(sql)
    except Exception, e:
        print e.message
    commit_db(conn)
    close_db(conn)


def insert_btc_data(create_time, huobi_btc, okex_btc, gate_btc, minus, percent):
    conn = connect_db()
    c = conn.cursor()

    percent = float(int(percent * 1000)) / 1000
    values = "VALUES ('%s', %f, %f, %f, %f, %.3f)" % (str(create_time), huobi_btc, okex_btc, gate_btc, minus, percent)
    sql = "INSERT INTO btc_watch (create_time, huobi_btc, okex_btc,gate_btc, minus, percent)" + values
    try:
        c.execute(sql)
    except Exception, e:
        print e.message
    commit_db(conn)
    close_db(conn)


def insert_trade_data(create_time, state):
    conn = connect_db()
    c = conn.cursor()

    values = "VALUES ('%s', '%s', %f, %f, %f, %.3f)" % (str(create_time), str(state), 0, 0, 0, 0)
    sql = "INSERT INTO trade_result (create_time, state, soc_price,wicc_price, minus, percent)" + values
    try:
        c.execute(sql)
    except Exception, e:
        print e.message
    commit_db(conn)
    close_db(conn)


if __name__ == '__main__':
    create_table()
    # insert_btc_data(common_utils.get_format_time(), 7700, 7769, 7752., 69, 0.8961038961039)
    # insert_trade_data(common_utils.get_format_time(), "买入soc")
    insert_soc_wicc(common_utils.get_format_time(), 0.0191, 0.0192, 0.2028, 0.2050, 69, 0.8961038961039)
