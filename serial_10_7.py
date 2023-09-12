from ast import Global
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import serial
import time
import os
import threading

GPIO.setmode(GPIO.BOARD)
pin,t1 = 7,0                                                    #設定繼電器控制腳位和RFID設備接口，以及宣告相關變數
GPIO.setup(pin,GPIO.OUT)
sr = serial.Serial("/dev/ttyUSB0",115200)                       
token,answer,tempstr=[],[],[]
tag,license="",""
flag,exist=False,False
tagdict = {}

def hex2dec(string_num):                                        #將16進制數值轉成10進制
    return str(int(string_num, 16))
def output(packs,t):                                            #判斷收集到的一串數列
    global tag,tempstr,exist,license,t1

    if len(packs) < 7 or int(hex2dec(packs[6])) > 20:           #篩掉長度小於7或是tag長度值大於20的數列(數列第7元素為16進制的tag長度值)
        return

    if len(packs) >= (7+int(hex2dec(packs[6]))):
        if int(packs[6]) == 0:                                  #如果tag長度值等於0則不對此數列作操作
            ...
        else:
            exist,tag = False,""
            answer=packs[10:10+int(hex2dec(packs[6]))-4]        #根據tag格式截取tag
            for row in answer:
                tag = tag + str(row)
             
            if tagdict.get(tag, "no") != "no":                  #判斷tag是否存在dictionary中，存在即讓exist = True，並記錄該tag對應的車牌
                exist = True
                license = tagdict.get(tag)
                
            if exist:                                           #如果exist = True，樹莓派第7接腳通電，並記錄當前時間
                GPIO.output(pin,True)
                t1 = time.time_ns()
            license = ""

def open_time():                                                #利用執行續判斷樹莓派第7接腳通電時間，超過1秒就斷電
    global t1
    while True:
        t = time.time_ns()
        if t - t1 > 1000000000 and t1 != 0:
            GPIO.output(pin,False)

try:
    with open("result2.csv","r") as f:                          #開啟tag與車牌的對照表，並將tag當成key，生成名為tagdict的dictionary
        for line in f.readlines():
            tempstr = line.replace("\n","").split(",")
            tagdict[tempstr[1]] = tempstr[0]
    ot = threading.Thread(target = open_time)
    ot.start()

    while(True):                                              
        data = sr.read().hex()    
        if data == '1b':                                        #tag的表頭數列固定是[1B,39]，數列必須是以此開頭才會丟入output方法做判斷
            flag=True
            continue
        if flag:
            if data == '39':
                output(token,t1)
                flag=False
                token=['1b','39']
                continue
        token.append(data)                                      #將後續讀取的數值放入數列
        if len(token) > 50:                                     #如果數列長度過長，則放棄該數列
            token = []
finally:
    GPIO.cleanup()                                              #程式執行結束時，清空GPIO設定
