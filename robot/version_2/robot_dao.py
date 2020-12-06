#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
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
                                    soc_to_wicc_minus    REAL,
                                    wicc_to_soc_minus    REAL,
                                    soc_to_wicc_percent  REAL,
                                    wicc_to_soc_percent  REAL);''')
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
                                        percent               REAL,
                                        soc_count             REAL,
                                        wicc_count            REAL);''')
    except Exception, e:
        print e.message
        try:
            sql = "select * from trade_result where soc_count > 0"
            c.execute(sql)
        except Exception, e:
            print "没有soc_count和wicc_count, 加上这两列:%s" % str(e.message)
            # https://blog.csdn.net/codepython/article/details/47749973
            # SQLite不支持一次添加多列...一列一列加
            sql = "ALTER TABLE trade_result ADD COLUMN soc_count REAL default 0"
            c.execute(sql)
            sql = "ALTER TABLE trade_result ADD COLUMN wicc_count REAL default 0"
            c.execute(sql)
    commit_db(conn)
    close_db(conn)
    print "Table created successfully"


# 往soc_wicc表中插入数据
def insert_soc_wicc(create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, soc_to_wicc_minus,
                    wicc_to_soc_minus, soc_to_wicc_percent, wicc_to_soc_percent):
    conn = connect_db()
    c = conn.cursor()

    soc_to_wicc_percent = common_utils.get_round(soc_to_wicc_percent, 3)
    wicc_to_soc_percent = common_utils.get_round(wicc_to_soc_percent, 3)
    values = " VALUES ('%s', %f, %f,%f, %f, %f,%f, %.3f, %.3f)" % (
        str(create_time), buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, soc_to_wicc_minus,
        wicc_to_soc_minus, soc_to_wicc_percent, wicc_to_soc_percent)
    sql = "INSERT INTO soc_wicc (create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price," \
          " soc_to_wicc_minus,wicc_to_soc_minus, soc_to_wicc_percent,wicc_to_soc_percent )" + values
    try:
        c.execute(sql)
    except Exception, e:
        print e.message
    commit_db(conn)
    close_db(conn)


def insert_trade_data(create_time, state, soc_price, wicc_price, minus, percent, soc_count, wicc_count):
    conn = connect_db()
    c = conn.cursor()

    values = "VALUES ('%s', '%s', %f, %f, %f, %.3f, %f, %f)" % (
        str(create_time), str(state), soc_price, wicc_price, minus, percent, soc_count, wicc_count)
    sql = "INSERT INTO trade_result (create_time, state, soc_price,wicc_price, minus, percent, soc_count, wicc_count)" + values
    try:
        c.execute(sql)
    except Exception, e:
        print e.message
    commit_db(conn)
    close_db(conn)


def get_debug_soc_wicc_data(skip, is_print):
    conn = connect_db()
    c = conn.cursor()

    sql = "SELECT buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, create_time from soc_wicc  limit 1 offset %d" % skip
    cursor = c.execute(sql)

    soc_buy_price = 0
    soc_sell_price = 0
    wicc_buy_price = 0
    wicc_sell_price = 0

    for row in cursor:
        soc_buy_price = row[0]
        soc_sell_price = row[1]
        wicc_buy_price = row[2]
        wicc_sell_price = row[3]
        if is_print:
            print row[4]
    conn.close()
    return soc_buy_price, soc_sell_price, wicc_buy_price, wicc_sell_price


if __name__ == '__main__':
    print "robot_dao --- main start"
    # create_table()
    # insert_trade_data(common_utils.get_format_time(), "买入soc", 0.019, 0.2027, 0.0127, 6.68, 88500, 93.36)
    # insert_soc_wicc(common_utils.get_format_time(), 0.0191, 0.0192, 0.2028, 0.2050, 69, 72, 0.8961038961039,
    #                 0.4761038961039)
