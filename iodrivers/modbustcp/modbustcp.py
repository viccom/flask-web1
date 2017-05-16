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
from multiprocessing import Process, Queue, Pipe
socket.setdefaulttimeout(10)


import xml.dom.minidom

# 打开xml文档
try:
    dom = xml.dom.minidom.parse('config.xml')
except Exception as e:
    print('exception catched : ', e)
    time.sleep(5)
    sys.exit()
else:
    cc = dom.getElementsByTagName('Server')
    _REDISIP = cc[0].firstChild.data
    cc = dom.getElementsByTagName('Port')
    _REDISPORT = int(cc[0].firstChild.data)
    #print('连接信息：Redis Server：', _REDISIP, 'Port：', _REDISPORT)

import redis
from RedisHelper import redis_broadcast

pool0 = redis.ConnectionPool(host=_REDISIP, port=_REDISPORT, db=0)
r0 = redis.Redis(connection_pool=pool0)
pool1 = redis.ConnectionPool(host=_REDISIP, port=_REDISPORT, db=1)
r1 = redis.Redis(connection_pool=pool1)

def packxxx(fckey, fc, maxnum):
    j = 0
    fcpacks = {}
    for m in range(0, len(fckey)):
        midmid = fc[fckey[m]]
        pack = []
        packhead = int(midmid[0][3])
        for i in range(0, len(midmid)):
            if int(midmid[i][3]) - packhead < maxnum:
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

def datalen(datatype):
    if datatype == '1':
        return 1
    elif datatype == '2':
        return 2
    elif datatype == '3':
        return 4

def getrtdata(devlist):
    global c, r0, r1, r2
    ln = int(len(devlist) / 5)
    for xi in range(0, ln):
        #print(xi + 1, '#################################################')
        n = 5 * xi
        devname = devlist[n]  ##设备名称
        devpacknum = int(devlist[n + 2])  ##modbus组包最大寄存器个数
        if not (0 < devpacknum < 128):
            devpacknum = 32
        devaddr = int(devlist[n + 1])  ##设备modbus地址
        if not (0 < devaddr < 255):
            break
        devfc = devlist[n + 3]  ##modbus功能码集合
        devtags = devlist[n + 4]
        packs = packxxx(devfc, devtags, devpacknum)
        #print('设备名称:', devname, '设备modbus地址:', devaddr, 'modbus组包最大寄存器个数:', devpacknum, 'modbus功能码集合:', devfc)

        rtdata = {}
        rmess = {}
        rtmessage = {}
        for p in range(0, len(packs)):
            iovalues = packs[p]
            fc = int(iovalues[0][2])
            # print('function code:', fc)
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

            fixedbin = b'\x00\x00\x00\x00\x00\x00'
            devaddrbin = struct.pack('b', devaddr)
            fcbin = struct.pack('b', fc)
            startregbin = struct.pack('>h', startreg)
            regslenbin = struct.pack('>h', reglen)

            sendpackbin = fixedbin + devaddrbin + fcbin + startregbin + regslenbin
            s_mes = str(binascii.b2a_hex(sendpackbin))[2:-1].upper()
            print('send    hex packet NO', p + 1, ':', s_mes) #发送报文
            rtmessage['发送'] = s_mes
            try:
                c.send(sendpackbin)  ##发送数据包
            except Exception as err:
                print(err)
                #c.close()
                break
            try:
                retdata = c.recv(1024)  ##收取数据包
            except Exception as err:
                print(err)
                c.close()
                time.sleep(2)
                print(c, devip, devport)
                c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                reconnect(c, devip, devport)
                break
            retdatahex = str(binascii.b2a_hex(retdata))[2:-1].upper()
            print('receive hex packet:', retdatahex) #接收报文
            rtmessage['接收'] = retdatahex
            retdatahexlen = len(retdatahex)
            ret1 = '%d' % struct.unpack('!B', retdata[6:7])#设备地址
            ret2 = '%d' % struct.unpack('!B', retdata[7:8])#功能码
            ret3 = '%d' % struct.unpack('!B', retdata[8:9])#长度

            rttime = str(datetime.datetime.fromtimestamp(int(time.time())))
            if int(ret1) == int(devaddr) and int(ret2) == int(fc) and int(ret3) == reglen * 2: ##判断返回报文是否符合协议
                valuehex = retdatahex[18:retdatahexlen]
                rtvalue = retdata[9:len(retdata)]
                rtdatadict = {}

                for i in range(0, len(iovalues)):
                    datatype = iovalues[i][4]
                    if datatype == '1':
                        dlen = 2
                        startpos = (int(iovalues[i][3]) - startreg) * 2
                        valuebin = rtvalue[startpos:startpos + dlen]
                        value = '%d' % struct.unpack('!h', valuebin)  # 数值,2个字节int
                        #print(i, value)

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
                    #rtdatadict[i]['tagname'] = iovalues[i][0]
                    rtdatadict[i]['tagdesc'] = iovalues[i][1]
                    rtdatadict[i]['time'] = rttime
                    rtdatadict[i]['value'] = value
                    #print(i, rtdatadict[i])
                for j in range(0, len(iovalues)):
                    rtdata[iovalues[j][0]] = rtdatadict[j]

            elif int(ret1) == int(devaddr) and int(ret2) == int(fc) and int(ret3) == math.ceil(reglen/8): ##判断返回报文是否符合协议
                valuehex = retdatahex[18:retdatahexlen]
                rtvalue = retdata[9:9+int(ret3)]
                bitstr = ''
                for n in range(0, len(rtvalue)):
                    onebyte = rtvalue[n:n + 1]
                    onebytehex = str(binascii.b2a_hex(onebyte))[2:-1]
                    onebytestr = '{0:08b}'.format(int(onebytehex, 16))[::-1]
                    #print(onebytestr)
                    bitstr = bitstr + onebytestr
                #print(bitstr)
                rtdatadict = {}

                for i in range(0, len(iovalues)):
                    regnum = iovalues[i][3]
                    nxx = regnum-startreg
                    value = bitstr[nxx:nxx+1]
                    rtdatadict[i] = {}
                    #rtdatadict[i]['tagname'] = iovalues[i][0]
                    rtdatadict[i]['tagdesc'] = iovalues[i][1]
                    rtdatadict[i]['time'] = rttime
                    rtdatadict[i]['value'] = value
                    #print(rtdatadict[i])
                for j in range(0, len(iovalues)):
                    rtdata[iovalues[j][0]] = rtdatadict[j]

            else:
                rtdatadict = {}
                for i in range(0, len(iovalues)):
                    rtdatadict[i] = {}
                    #rtdatadict[i]['tagname'] = iovalues[i][0]
                    rtdatadict[i]['tagdesc'] = iovalues[i][1]
                    rtdatadict[i]['time'] = rttime
                    rtdatadict[i]['value'] = 'no data'
                    #print(rtdatadict[i])
                r_dict = {}
                for j in range(0, len(iovalues)):
                    rtdata[iovalues[j][0]] = rtdatadict[j]
                pass
            rmess[p] = rtmessage

        #json_rtdata = json.dumps(rtdata)
        print('数据条数：', len(rtdata))
        print('报文条数：', len(rtmessage))
        #print(rtdata, devname)
        print('订阅参数:', subscribe)
        if subscribe:
            Bdobj = redis_broadcast(devname)
            Bdobj.publish(json.dumps(rtdata))
            Bdobj = redis_broadcast(devname+'_mes')
            Bdobj.publish(json.dumps(rmess))
            print('@@@@@@@@@@@@@@')
        r1.hmset(devname, rtdata)
        #print(xi + 1, '#################################################')

def reconnect(tcpclient, devip, devport):
    while True:
        if procpipe.poll():
            piperecv = procpipe.recv()
            if piperecv == 'stop':
                print(os.getpid(), '收到父进程', os.getppid(), '消息：', piperecv)
                print(os.getpid(), '正在退出')
                procpipe.send('已经退出')
                time.sleep(2)
                os._exit(0)
        try:
            #c.timeout(10)
            tcpclient.connect((devip, devport))
            break
        except Exception as err:
            print(err)
            time.sleep(5)

def new_tags(tags):
    if tags:
        tags.sort(key=lambda x: x['reg'])
        _xx = []
        for xx in tags:
            zx = (xx['tagname'], xx['tagdesc'], xx['fc'], xx['reg'], xx['datatype'])
            _xx.append(zx)
        return _xx

def get_devlists(dev):
    dev_info = eval(r0.hget("DevPool_list", dev).decode('ascii'))
    devaddr = dev_info['protocol_cfg']['devaddr']
    devpacknum = dev_info['protocol_cfg']['devpacknum']
    linkdevtags = eval(r0.get(dev).decode('utf-8'))
    fc1_tags = []
    fc2_tags = []
    fc3_tags = []
    fc4_tags = []
    _dict = {}
    fclist = []
    for x in linkdevtags['tags']:
        if x['fc'] == '1':
            fc1_tags.append(x)
        if x['fc'] == '2':
            fc2_tags.append(x)
        if x['fc'] == '3':
            fc3_tags.append(x)
        if x['fc'] == '4':
            fc4_tags.append(x)

    if fc1_tags:
        _dict['1'] = new_tags(fc1_tags)
        fclist.append('1')
    if fc2_tags:
        _dict['2'] = new_tags(fc2_tags)
        fclist.append('2')
    if fc3_tags:
        _dict['3'] = new_tags(fc3_tags)
        fclist.append('3')
    if fc4_tags:
        _dict['4'] = new_tags(fc4_tags)
        fclist.append('4')
    return [dev, devaddr, devpacknum, fclist, _dict]


#utctm = 'modbustcp_148453854241'
import common.globalValue
ch_id = common.globalValue.get_value()
procpipe = common.globalValue.get_pipe()

ch_list = r0.hkeys("Channel_List")
c_dict = {}
for c_list in ch_list:
    ch_info = eval(r0.hget("Channel_List", c_list.decode('ascii')).decode('ascii'))
    c_dict[c_list.decode('ascii')] = ch_info

devip = c_dict[ch_id]['link_cfg']['devip']
devport = c_dict[ch_id]['link_cfg']['devport']
linkdev = c_dict[ch_id]['linkdev']

if linkdev:
    global devlists
    devlists = get_devlists(linkdev)
    # print(devip, devport, protocol_name, chtags)
    r0.hset("Process_Status", ch_id, '1')
    r0.hset("Process_Status", ch_id + '_id', os.getpid())
    global subscribe
    subscribe = 1
    r1.delete(linkdev)
    scanperiod = 50                           #扫描周期xxx 100ms
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('start connect Modbus Server: ')
    reconnect(c, devip, devport)

    while True:
        for scanp in range(0, scanperiod):
            if procpipe.poll():
                piperecv = procpipe.recv()
                print('收到:', piperecv)
                if piperecv == 'stop':
                    print(os.getpid(), '收到父进程', os.getppid(), '消息：', piperecv)
                    print(os.getpid(), '正在退出')
                    procpipe.send('已经退出')
                    r0.hset("Process_Status", ch_id, '0')
                    time.sleep(2)
                    os._exit(0)
                elif piperecv == 'subscribe':
                    print(os.getpid(), '收到父进程', os.getppid(), '订阅消息：', piperecv)
                    subscribe = 1
                elif piperecv == 'unsubscribe':
                    print(os.getpid(), '收到父进程', os.getppid(), '取消订阅消息：', piperecv)
                    subscribe = 0
                elif piperecv == 'config_change':
                    devlists = get_devlists(linkdev)
                    r1.delete(linkdev)
                    time.sleep(0.1)
            if scanp == 0:
                getrtdata(devlists)
            else:
                if (scanp*0.1).is_integer():
                    #print(scanp*0.1)
                    pass
                time.sleep(0.1)

else:
    print('devlist no data!')
    sys.exit()


