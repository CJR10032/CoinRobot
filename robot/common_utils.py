#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import urllib2
import json

'''
封装一些常用的方法

'''


#   保存用于分析的文件
def write_file(file_name, content):
    f = open(file_name, 'w')
    f.write(content)
    f.close()


#   读取文件
def read_file(file_name):
    f = open(file_name, 'r')
    content = f.read()
    f.close()
    return content


# 获取当前时间戳(13位的毫秒级)
def get_current_timestamp():
    millis = int(round(time.time() * 1000))
    return millis


def get_format_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


#   将list按格式保存
def write_list_2_file(file_name, content_list):
    #   任务结束, 记录保存失败的链接, 人工去检查排错
    content = ''
    for item in content_list:
        content += item + "\n"
    write_file(file_name, content[:-1])


#   将文件读取为列表
def read_file_2_list(file_name):
    f = open(file_name, 'r')
    list = f.readlines()
    f.close()
    return list


def get_json(obj, object_hook):
    return json.dumps(obj, ensure_ascii=False, encoding="utf-8", default=object_hook)


#   将对象json化写入文件
def write_json(file_name, obj, object_hook):
    j_obj = get_json(obj, object_hook)
    write_file(file_name, str(j_obj))


#   反序列化
def read_json(file_name):
    content = read_file(file_name)
    return json.loads(content)


# 获取网址的内容
def get_response_content(url, headers):
    try:
        req = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(req)
        content = response.read()
    except Exception, e:
        print "%s\n加载网页出现异常导致没有拿到content:%s" % (url, str(e))
    else:
        return content


#   保存图片的方法
def save_img(save_name, img_url):
    content = get_response_content(img_url)
    #   w写, b以二进制写入
    with open(save_name, 'wb') as f:
        f.write(content)


def get_round(nums, count):
    p = pow(10, count)
    return float(int(nums * p)) / p
