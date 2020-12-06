#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 合并 多日的数据, 方便进行回测
import os
import sqlite3


def debug_create_table(conn):
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
    conn.commit()
    print "Table created successfully"


def merge_database(dir):
    new_conn = sqlite3.connect("debug_CoinRobot.db")
    # 创建 表
    debug_create_table(new_conn)

    new_c = new_conn.cursor()

    for file in os.listdir(dir):
        decode = file.decode('gbk')
        if decode.endswith(".db") and not decode.startswith("debug"):
            # 转换为绝对路径
            conn = sqlite3.connect(decode)
            c = conn.cursor()

            sql = "SELECT create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price from soc_wicc"
            cursor = c.execute(sql)

            params = []
            for row in cursor:
                create_time = row[0]
                buy_soc_price = row[1]
                sell_soc_price = row[2]
                buy_wicc_price = row[3]
                sell_wicc_price = row[4]

                new_values = " VALUES ('%s', %f, %f,%f, %f, %f,%f, %.3f, %.3f)" % (
                    str(create_time), buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, 0, 0, 0, 0)
                new_sql = "INSERT INTO soc_wicc (create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price," \
                          " soc_to_wicc_minus,wicc_to_soc_minus, soc_to_wicc_percent,wicc_to_soc_percent )" + new_values
                new_c.execute(new_sql)

                # params.append(
                #     (str(create_time), buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, 0, 0, 0, 0))
            conn.close()
            # new_sql = "INSERT INTO soc_wicc (create_time, buy_soc_price, sell_soc_price, buy_wicc_price, sell_wicc_price, " \
            #           "soc_to_wicc_minus,wicc_to_soc_minus, soc_to_wicc_percent,wicc_to_soc_percent) VALUES (?,?,?,?,?,?,?,?,?)"
            #
            # new_c.executemany(new_sql, params)
    new_conn.commit()
    new_conn.close()
    print "===merge_database方法结束==="


if __name__ == '__main__':
    print "merge_db --- main start"
    merge_database("F:\\python_project\\CoinRobot\\robot\\version_2\\db_temp")
