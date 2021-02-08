#!/usr/bin/env python
# -*- coding: utf-8 -*-

# scp
# nohup /usr/bin/python3.6 /root/retail_pos.py &

# scp /Users/hironobu.ohara/Desktop/retail_pos_data/20201014-1028.csv root@47.74.54.209:/root/retail_pos_data/
# scp /Users/hironobu.ohara/Desktop/retail_pos_data/20201029-1107.csv root@47.74.54.209:/root/retail_pos_data/


import os, sys, json, codecs
import csv, pprint
import datetime, time, pytz
from datetime import timedelta
from datetime import date
import random
from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=[{'host': "", 'port':9200}],
    http_auth=('', ''))

start = datetime.datetime.strptime('2021-01-21', '%Y-%m-%d').date() 
end   = datetime.datetime.strptime('2025-12-31', '%Y-%m-%d').date() 

def csv_reader(file, header=False):
    with open(file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header:
            next(reader)

        for row in reader:
            yield row

def get_nth_week(day):
    return (day - 1) // 7 + 1

def get_nth_dow(year, month, day):
    return get_nth_week(day), calendar.weekday(year, month, day)

def daterange(_start, _end):
    for n in range((_end - _start).days):
        yield _start + timedelta(n)

def total_seconds(t: datetime.time):
    return t.hour * 3600 + t.minute * 60 + t.second

def check_total_seconds(t: datetime.time):
    print("------")
    print(t.year * 1000000000)
    print(t.month * 10000000)
    print(t.day   *   100000)
    print(t.hour * 3600)
    print(t.minute * 60)
    print(t.second)
    print("-------------")
    return t.year + t.month + t.day + t.hour * 3600 + t.minute * 60 + t.second


def output():
    youbi = 5
    stream_num = 0
    add_second = 0    
    for i in daterange(start, end):    
        strYoubi = str(youbi) if len(str(youbi)) > 1 else "0" + str(youbi)
        filepath = "/root/retail_pos_data_ph2/es-pos-sample-" + strYoubi + ".csv"
        print(i,youbi,filepath)
        youbi = 1 if youbi > 7+7+7+7 else youbi + 1

        g = csv_reader(filepath, header=False)
        line = next(g)
        line = next(g) 
        print(line[1]) 
        try:
            while True:
                record_date_d = datetime.datetime.strptime(i.strftime('%Y/%m/%d') + " " + line[1][11:], "%Y/%m/%d %H:%M:%S")  
                print(type(record_date_d))  
                print("csvの時刻:" + str(record_date_d)) 

                basetime = datetime.datetime.now(pytz.timezone('Asia/Tokyo')) # 現在のTokyo時刻（リアルタイム）
                basetime_d = basetime.strftime("%Y-%m-%d %H:%M:%S")
                basetime_d = datetime.datetime.strptime(basetime_d, '%Y-%m-%d %H:%M:%S')
                print("現在の時刻:" + str(basetime_d))

                delta = datetime.timedelta(seconds=total_seconds(basetime_d) - total_seconds(record_date_d))
                print("差分:" + str(delta.total_seconds()))

                if (delta.total_seconds() > -60 and delta.total_seconds() < 60 and basetime_d.day == record_date_d.day ):
                    #utc_basetime = datetime.datetime.utcnow() - datetime.timedelta(days=25) - datetime.timedelta(hours=2) + datetime.timedelta(minutes=add_second) - datetime.timedelta(hours=9)
                    ## utc_basetime = datetime.datetime.utcnow() - datetime.timedelta(minutes=30) # - datetime.timedelta(hours=9)!!!!!!!!! 2020/11/07 リリースするときは、以下 utc_basetime = datetime.datetime.utcnow() を使って
                    utc_basetime = datetime.datetime.utcnow()
                    utc_datetime = utc_basetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    print("---------------------------------")
                    print(utc_datetime)
                    print(type(utc_datetime))

                    retail_pos_data = {
                                "@timestamp":utc_datetime,
                                "week":line[2],
                                "time_zone":line[3],
                                "Avg_ActiveUser":float(line[4]),
                                "set":line[5],
                                "set_number":int(line[6]),
                                "Code":line[7],
                                "Master_Code":line[8], # コード
                                "Category":line[9], # カテゴリ
                                "Maker":line[10], # メーカー名
                                "ProductName":line[11], #商品名称
                                "unit price":int(line[13]), # 単価
                                "purchasing quantities":int(line[14]), # 購入個数
                                "Total price":int(line[15]), # 合計
                                "Total stock number":int(line[16]), # 配置数
                                "Stock number":int(line[17]), # 在庫数
                                "Total sales":int(line[18])} #  総売上

                    json.dumps(retail_pos_data)
                    #print(utc_datetime)
                    print(">>>>>>>>>>>>> %d", stream_num)
                    print(retail_pos_data)
                    print("-----------------------")

                    stream_num += 1
                    es.index(index="pos_demo_index",
                                doc_type="pos",
                                id=stream_num,
                                body=retail_pos_data,
                                ignore=400)

                    line = next(g)

                else:
                    time.sleep(1)
                    add_second += 1

        except StopIteration:
            pass



'''
            retail_pos_data = {
                        "@timestamp":utc_datetime,
                        "week":line[2],
                        "time_zone":line[3],
                        "Avg_ActiveUser":float(line[4]),
                        "set":line[5],
                        "set_number":int(line[6]),
                        "Code":line[7],
                        "Master_Code":line[8], # コード
                        "Category":line[9], # カテゴリ
                        "Maker":line[10], # メーカー名
                        "ProductName":line[11], #商品名称
                        "unit price":int(line[13]), # 単価
                        "purchasing quantities":int(line[14]), # 購入個数
                        "Total price":int(line[15]), # 合計
                        "Total stock number":int(line[16]), # 配置数
                        "Stock number":int(line[17]), # 在庫数
                        "Total sales":int(line[18])} #  総売上

            json.dumps(retail_pos_data)
            #print(utc_datetime)
            print(">>>>>>>>>>>>> %d", stream_num)
            print(retail_pos_data)
            print("-----------------------")

            stream_num += 1
            es.index(index="pos_demo_index",
                        doc_type="pos",
                        id=stream_num,
                        body=retail_pos_data,
                        ignore=400)

            line = next(g)

        else:
            time.sleep(1)
            add_second += 1
'''


if __name__ == '__main__':
#    output()
    while True:
        output()
        

