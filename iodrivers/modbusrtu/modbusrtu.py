#/usr/bin/env python
#encoding=utf-8

import sqlite3
import json
import binascii
import struct
import socket
import time
import datetime
import os
import sys
import math
import serial
from time import gmtime, strftime
from multiprocessing import Process, Queue, Pipe
socket.setdefaulttimeout(10)

global t

def packxxx(fckey, fc, maxnum):
    j = 0
    fcpacks = {}
    for m in range(0, len(fckey)):
        midmid = fc[fckey[m]]
        pack = []
        packhead = midmid[0][3]
        for i in range(0, len(midmid)):
            if midmid[i][3] - packhead < maxnum:
                pack.append(midmid[i])
            else:
                packhead = midmid[i][3]
                fcpacks[j] = pack
                pack = []
                j = j+1
                pack.append(midmid[i])
        fcpacks[j] = pack
        #print(fcpacks)
        j = j + 1
    return fcpacks

def devlistkxxx(devtablexxx, devxxx, fcxxx):
    devlist = []
    for i in range(0, len(devs)):
        devname = devxxx[i][0]
        devaddr = devxxx[i][1]
        devpacknum = devxxx[i][2]
        devselect = devtablexxx + '_devs_' + devname
        fcnew = []
        fciolinks = {}
        ###----------
        for i in range(0, len(fcxxx)):
            fccode = fcxxx[i]
            #print('功能码：', fc[i])
            try:
                cursor.execute('SELECT * FROM \"' + devselect + '\" WHERE fc = ' + fccode + ' ORDER BY reg ASC')
                abc = cursor.fetchall()

                if abc:
                    #print(abc)
                    fciolinks[fccode] = abc
                    fcnew.append(fccode)
                else:
                    #print(abc)
                    print('fc',fc[i], 'no record!')
            except Exception as err:
                print(err)
        ###----------
        if fciolinks:
            devlist.append(devname)
            devlist.append(devaddr)
            devlist.append(devpacknum)
            devlist.append(fcnew)
            devlist.append(fciolinks)
    return devlist

def datalen(datatype):
    if datatype == '1':
        return 1
    elif datatype == '2':
        return 2
    elif datatype == '3':
        return 4


def getrtdata(devlist, channeltype):
    ln = int(len(devlist) / 5)
    print('设备数：', ln)
    for xi in range(0, ln):
        print(xi + 1, '#################################################')
        n = 5 * xi
        devname = devlist[n]  ##设备名称
        devaddr = int(devlist[n + 1])  ##设备modbus地址
        devpacknum = int(devlist[n + 2])  ##modbus组包最大寄存器个数
        devfc = devlist[n + 3]  ##modbus功能码集合
        devtags = devlist[n + 4]
        packs = packxxx(devfc, devtags, devpacknum)
        print('packs:', len(packs))
        print('设备名称:', devname, '设备modbus地址:', devaddr, 'modbus组包最大寄存器个数:', devpacknum, 'modbus功能码集合:', devfc)

        rtdata = []
        for p in range(0, len(packs)):

            iovalues = packs[p]
            fc = int(iovalues[0][2])
            #print('function code:', fc)
            # print(iovalues)

            if fc == 3 or fc == 4:
                startreg = int(iovalues[0][3])
                #print('start register:', startreg)
                endreg = int(iovalues[len(iovalues) - 1][3]) + datalen(iovalues[len(iovalues) - 1][4]) - 1
                # print('end   register:', endreg)
                reglen = endreg - (startreg - 1)
            elif fc == 1 or fc == 2:
                startreg = int(iovalues[0][3])
                #print('start register:', startreg)
                endreg = int(iovalues[len(iovalues) - 1][3])
                # print('end   register:', endreg)
                reglen = endreg - (startreg - 1)

            devaddrbin = struct.pack('B', devaddr)
            fcbin = struct.pack('B', fc)
            startregbin = struct.pack('>H', startreg)
            regslenbin = struct.pack('>H', reglen)

            sendpackbin = devaddrbin + fcbin + startregbin + regslenbin
            sendpackbin = sendpackbin + struct.pack('<H', crc16A(sendpackbin))

            #print('send    hex packet NO', p + 1, ':', str(binascii.b2a_hex(sendpackbin))[2:-1].upper())
            if channeltype=='serial':
                try:
                    #print(p, time.time())
                    sendn = t.write(sendpackbin)  ##发送数据包
                except Exception as err:
                    print(err)
                    #c.close()
                    break
                try:
                    retdata = t.read(1)##收取数据包
                    if retdata:
                        retdata += t.read(t.inWaiting())
                        #retdatahex = str(binascii.b2a_hex(retdata))[2:-1].upper()
                        #print('返回报文：', retdatahex)
                except Exception as err:
                    print(err)
                    t.close()
                    time.sleep(2)
                    sys.exit()
                #print(time.time())

            elif channeltype=='tcp_client':
                try:
                    c.send(sendpackbin)  ##发送数据包
                except Exception as err:
                    print(err)
                    #c.close()
                    break
                try:
                    retdata = c.recv(1024)  ##收取数据包
                    #print(retdata)
                    #retdatahex = str(binascii.b2a_hex(retdata))[2:-1].upper()
                    #print('返回报文：', retdatahex)
                    #sys.exit()
                except Exception as err:
                    print(err)
                    c.close()
                    time.sleep(2)
                    print(c, devip, devport)
                    global c
                    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    reconnect(c, devip, devport)
                    break
                pass
            else:
                print('不支持的通道类型')

            
            if retdata:
                #print(p, time.time())
                #print('开始解码')
                read_first = retdata[0:2]
                if read_first == (struct.pack('>B', devaddr) + struct.pack('>B', fc)):
                    ###########开始解码#############
                    retdata=retdata[0:len(retdata)-2]
                    retdatahex = str(binascii.b2a_hex(retdata))[2:-1].upper()
                    #print('receive hex packet:', retdatahex)
                    retdatahexlen = len(retdatahex)
                    ret1 = '%d' % struct.unpack('!B', retdata[0:1])
                    ret2 = '%d' % struct.unpack('!B', retdata[1:2])
                    ret3 = '%d' % struct.unpack('!B', retdata[2:3])
                    
                    rttime = str(datetime.datetime.fromtimestamp(int(time.time())))
                    if int(ret1) == int(devaddr) and int(ret2) == int(fc) and int(
                            ret3) == reglen * 2:  ##判断返回报文是否符合协议
                        valuehex = retdatahex[6:retdatahexlen]
                        rtvalue = retdata[3:len(retdata)]
                        rtdatadict = {}

                        for i in range(0, len(iovalues)):
                            datatype = iovalues[i][4]
                            if datatype == '1':
                                dlen = 2
                                startpos = (int(iovalues[i][3]) - startreg) * 2
                                valuebin = rtvalue[startpos:startpos + dlen]
                                value = '%d' % struct.unpack('!h', valuebin)  # 数值,2个字节int

                            elif datatype == '2':
                                dlen = 4
                                startpos = (int(iovalues[i][3]) - startreg) * 2
                                valuebin = rtvalue[startpos:startpos + dlen]
                                value = '%.2f' % struct.unpack('!f', valuebin)  # 数值,4个字节float

                            elif datatype == '3':
                                dlen = 8
                                startpos = (int(iovalues[i][3]) - startreg) * 2
                                valuebin = rtvalue[startpos:startpos + dlen]
                                value = '%.2f' % struct.unpack('!d', valuebin)  # 数值,8个字节double

                            rtdatadict[i] = {}
                            rtdatadict[i]['tagname'] = iovalues[i][0]
                            rtdatadict[i]['tagdesc'] = iovalues[i][1]
                            rtdatadict[i]['time'] = rttime
                            rtdatadict[i]['value'] = value
                            # print(rtdatadict[i])
                        for j in range(0, len(iovalues)):
                            rtdata.append(rtdatadict[j])

                    elif int(ret1) == int(devaddr) and int(ret2) == int(fc) and int(ret3) == math.ceil(
                                    reglen / 8):  ##判断返回报文是否符合协议
                        valuehex = retdatahex[6:retdatahexlen]
                        rtvalue = retdata[3:3 + int(ret3)]
                        bitstr = ''
                        for n in range(0, len(rtvalue)):
                            onebyte = rtvalue[n:n + 1]
                            onebytehex = str(binascii.b2a_hex(onebyte))[2:-1]
                            onebytestr = '{0:08b}'.format(int(onebytehex, 16))[::-1]
                            # print(onebytestr)
                            bitstr = bitstr + onebytestr
                        # print(bitstr)
                        rtdatadict = {}

                        for i in range(0, len(iovalues)):
                            regnum = iovalues[i][3]
                            nxx = regnum - startreg
                            value = bitstr[nxx:nxx + 1]
                            rtdatadict[i] = {}
                            rtdatadict[i]['tagname'] = iovalues[i][0]
                            rtdatadict[i]['tagdesc'] = iovalues[i][1]
                            rtdatadict[i]['time'] = rttime
                            rtdatadict[i]['value'] = value
                            # print(rtdatadict[i])
                        for j in range(0, len(iovalues)):
                            rtdata.append(rtdatadict[j])
                        pass

                    else:
                        rtdatadict = {}
                        for i in range(0, len(iovalues)):
                            rtdatadict[i] = {}
                            rtdatadict[i]['tagname'] = iovalues[i][0]
                            rtdatadict[i]['tagdesc'] = iovalues[i][1]
                            rtdatadict[i]['time'] = rttime
                            rtdatadict[i]['value'] = 'no data'
                            # print(rtdatadict[i])
                        for j in range(0, len(iovalues)):
                            rtdata.append(rtdatadict[j])
                    ###########结束解码#############

                else:
                    #print('返回报文不正确')
                    rtdatadict = {}
                    for i in range(0, len(iovalues)):
                        rtdatadict[i] = {}
                        rtdatadict[i]['tagname'] = iovalues[i][0]
                        rtdatadict[i]['tagdesc'] = iovalues[i][1]
                        rtdatadict[i]['time'] = rttime
                        rtdatadict[i]['value'] = 'no data'
                        # print(rtdatadict[i])
                    for j in range(0, len(iovalues)):
                        rtdata.append(rtdatadict[j])
                    #sys.exit()
            else:
                print('无任何返回信息')
                rtdatadict = {}
                for i in range(0, len(iovalues)):
                    rtdatadict[i] = {}
                    rtdatadict[i]['tagname'] = iovalues[i][0]
                    rtdatadict[i]['tagdesc'] = iovalues[i][1]
                    rtdatadict[i]['time'] = rttime
                    rtdatadict[i]['value'] = 'no data'
                    # print(rtdatadict[i])
                for j in range(0, len(iovalues)):
                    rtdata.append(rtdatadict[j])
            time.sleep(0.1)#包扫描间隔时间
                #sys.exit()
        #print(time.time())
        #for nn in rtdata:
            #print(nn)

        json_rtdata = json.dumps(rtdata)
        print('数据条数：', len(rtdata))
        #print(json_rtdata)
        print(xi + 1, '#################################################')
        #time.sleep(1)

def reconnect(tcpclient, devip, devport):
    while True:
        try:
            #c.timeout(10)
            tcpclient.connect((devip, devport))
            break
        except Exception as err:
            print(err)
            time.sleep(5)

def crc16A(dat):
    crc = 0xFFFF  # 65535
    index = 0
    for j in dat:
        crc = crc ^ j
        #print("crc=%x" % crc)
        for i in range(8):
            if (crc & 1) == 1:
                crc = crc >> 1
                crc = crc ^ 0xA001  # 40961 多项式
            else:
                crc = crc >> 1
    return crc

#utctm = 'modbusrtu_148453854241'
import common.globalValue
utctm = common.globalValue.get_value()
procpipe = common.globalValue.get_pipe()
fc = ['1', '2', '3', '4', '5']                      #定义需要查询的功能码
conn = sqlite3.connect('mbiolink.db')
cursor = conn.cursor()

try:
    cursor.execute('SELECT * FROM ch_index WHERE ch_name=\"'+utctm+'\"') ##查询通道信息表名
    result = cursor.fetchall()
    devtable = result[0][0]
except Exception as err:
    print(err)

try:
    cursor.execute('SELECT * FROM \"'+devtable+'\"') ##查询通道信息表
    channel = cursor.fetchall()
    #print(channel)
except Exception as err:
    print(err)
if channel:
    channeltype = channel[0][0]
    #channeltype = 'tcp_client'
    channelconfig = json.loads(channel[0][1])
    #print(channelconfig['comnum'])

try:
    cursor.execute('SELECT * FROM \"'+devtable+'_devs\"' + ' ORDER BY devname ASC') ##查询通道下面的设备表名及各设备规约参数
    devs = cursor.fetchall()
    print(devs)
except Exception as err:
    print(err)


if devs:
    devlists = devlistkxxx(devtable, devs, fc) #获取通道下所有设备的点信息及对设备点表按照设备地址和功能码重新归类整理
    cursor.close()
    conn.close()
else:
    print('devs no data!')
    cursor.close()
    conn.close()
    sys.exit()

if devlists:
    if channeltype=='serial':
        comnum = channelconfig['comnum']                     #获取串口编号
        baudrate = int(channelconfig['baudrate'])              #获取波特率
        bytesize = int(channelconfig['bytesize'])              #获取数据位
        parity = channelconfig['parity']                     #获取校验方式
        stopbits = int(channelconfig['stopbits'])              #获取停止位
        waittime = int(channelconfig['waittime'])              #获取串口超时时间
        scanperiod = int(channelconfig['scan_period'])            #扫描周期xx秒
        #print(scanperiod)
        #sys.exit()
        try:
            t = serial.Serial(comnum, baudrate=baudrate, timeout=waittime, writeTimeout=2, bytesize=bytesize, stopbits=stopbits, parity=parity)
            #print(t.get_settings())
            print('start comunication with modbusrtu: ')
            while True:
                for scanp in range(0, scanperiod):
                    if procpipe.poll():
                        piperecv = procpipe.recv()
                        print(os.getpid(), '收到父进程', os.getppid(), '消息：', piperecv)
                        print(os.getpid(), '正在退出')
                        procpipe.send('已经退出')
                        time.sleep(2)
                        os._exit(0)
                    #print('*************************')
                    if scanp == 0:
                        getrtdata(devlists, channeltype)
                    else:
                        if (scanp*0.1).is_integer():
                            print(scanp*0.1)
                        time.sleep(0.1)

        except Exception as err:
            print(err)
    elif channeltype=='tcp_client':
        devip = channelconfig['devip']                     #获取TCP通道IP地址
        devport = int(channelconfig['devport'])              #获取TCP通道端口号
        scanperiod = int(channelconfig['scan_period'])            #扫描周期xx秒
        #devip = '192.168.163.1'
        #devport = 2345
        #scanperiod = 50

        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('start connect ModbusRTU Server: ')
        reconnect(c, devip, devport)

        while True:
            for scanp in range(0, scanperiod):
                if procpipe.poll():
                    piperecv = procpipe.recv()
                    print(os.getpid(), '收到父进程', os.getppid(), '消息：', piperecv)
                    print(os.getpid(), '正在退出')
                    procpipe.send('已经退出')
                    time.sleep(2)
                    os._exit(0)
                if scanp == 0:
                    getrtdata(devlists, channeltype)
                else:
                    if (scanp*0.1).is_integer():
                        print(scanp*0.1)
                    time.sleep(0.1)
        pass
    else:
        print('通道端口类型错误')

else:
    print('devlist no data!')
    sys.exit()


