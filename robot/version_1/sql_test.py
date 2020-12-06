#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3


def create_database():
    # http://www.runoob.com/sqlite/sqlite-python.html
    try:
        conn = sqlite3.connect('test.db')
        print "Opened database successfully";
        c = conn.cursor()
        c.execute('''CREATE TABLE COMPANY
                       (ID  INTEGER PRIMARY KEY     NOT NULL,
                       NAME           TEXT    NOT NULL,
                       AGE            INT     NOT NULL,
                       ADDRESS        CHAR(50),
                       SALARY         REAL);''')
        print "Table created successfully";
        conn.commit()
        conn.close()
    except Exception ,e:
        print e.message

def insert_database():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    print "Opened database successfully";

    c.execute("INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY) \
                  VALUES ('Paul', 32, 'California', 20000.00 )");

    c.execute("INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY) \
                  VALUES ('Allen', 25, 'Texas', 15000.00 )");

    c.execute("INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY) \
                  VALUES ('Teddy', 23, 'Norway', 20000.00 )");

    c.execute("INSERT INTO COMPANY (NAME,AGE,ADDRESS,SALARY) \
                  VALUES ('Mark', 25, 'Rich-Mond ', 65000.00 )");
    conn.commit()
    print "Records created successfully";
    conn.close()

def select_database():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    print "Opened database successfully";

    cursor = c.execute("SELECT id, name, address, salary  from COMPANY")
    for row in cursor:
        print "ID = ", row[0]
        print "NAME = ", row[1]
        print "ADDRESS = ", row[2]
        print "SALARY = ", row[3], "\n"

    print "Operation done successfully";
    conn.close()

def update_database():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    print "Opened database successfully";

    c.execute("UPDATE COMPANY set SALARY = 25000.00 where ID=1")
    conn.commit()
    print "Total number of rows updated :", conn.total_changes

    cursor = conn.execute("SELECT id, name, address, salary  from COMPANY")
    for row in cursor:
        print "ID = ", row[0]
        print "NAME = ", row[1]
        print "ADDRESS = ", row[2]
        print "SALARY = ", row[3], "\n"

    print "Operation done successfully";
    conn.close()

def delete_database():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    print "Opened database successfully";

    c.execute("DELETE from COMPANY where ID=2;")
    conn.commit()
    print "Total number of rows deleted :", conn.total_changes

    cursor = conn.execute("SELECT id, name, address, salary  from COMPANY")
    for row in cursor:
        print "ID = ", row[0]
        print "NAME = ", row[1]
        print "ADDRESS = ", row[2]
        print "SALARY = ", row[3], "\n"

    print "Operation done successfully";
    conn.close()

def alter_table():
    try:
        conn = sqlite3.connect('test.db')
        c = conn.cursor()
        print "Opened database successfully";

        c.execute("ALTER TABLE COMPANY ADD COLUMN SEX TEXT NOT NULL")

        print "Operation done successfully";
        conn.close()
    except Exception, e:
        print e.message

if __name__ == '__main__':
    create_database()
    insert_database()
    select_database()
    update_database()
    delete_database()


