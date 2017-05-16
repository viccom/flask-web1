import json
import redis
import os, sys
import xlrd
import xlwt
from datetime import datetime

pool0 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=0)
hr0 = redis.Redis(connection_pool=pool0)
pool1 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=1)
hr1 = redis.Redis(connection_pool=pool1)
pool2 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=2)
hr2 = redis.Redis(connection_pool=pool2)


sheethead = ['tagname', 'tagdesc', 'fc', 'reg', 'datatype']

print(hr0.keys())
chlists = json.loads(hr0.get('Channel_List_Json').decode('utf-8'))
print(chlists)

for ch in chlists['Channel_List']:
	print(ch)
	chinfo = json.loads(hr0.hget("Channel_List", ch).decode('utf-8'))
	print(chinfo)
	mydev = chinfo['linkdev']
	devtags = eval(hr0.get(mydev))['tags']

	wb = xlwt.Workbook()
	ws2 = wb.add_sheet('sheet1', cell_overwrite_ok=True)
	for n in range(len(sheethead)):
		ws2.write(0, n, sheethead[n])

	i = 1
	for t in devtags:
		for n in range(len(sheethead)):
			ws2.write(i, n, t[sheethead[n]])
		i += 1
		#print(t)
	wb.save('./static/downloads/' + mydev + '.xls')
	#devvalues = hr1.hgetall(mydev)
# print(devvalues)

sys.exit()

devpools = hr0.hkeys('DevPool_list')
# print(devpools)
for dev in devpools:
	devinfo = eval(hr0.hget('DevPool_list', dev).decode('utf-8'))
	print(dev.decode('utf-8'), devinfo['protocol_name'], devinfo['protocol_cfg'])

excelbook = xlrd.open_workbook("e4sad23x543.xlsx")
print("表单数量:",excelbook.nsheets)
print("表单名称:", excelbook.sheet_names())
sh = excelbook.sheet_by_index(0)
print("表单名称：{0},行数：{1},列数：{2}".format(sh.name, sh.nrows, sh.ncols))
#print("Cell D20 is {0}".format(sh.cell_value(rowx=19, colx=3)))
sheethead = sh.row(0)
print("表头：", sheethead)
tags = []
for rx in range(1, sh.nrows):
	#print(sh.row(rx))
	tag = {}
	for n in range(len(sheethead)):
		tag[sheethead[n].value] = sh.row(rx)[n].value
		pass
	tags.append(tag)

newtags = {'tags': tags}
for t in newtags['tags']:
	print(t)


style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
    num_format_str='#,##0.00')
style1 = xlwt.easyxf(num_format_str='D-MMM-YY')

wb = xlwt.Workbook()
ws1 = wb.add_sheet('A Test Sheet')

ws1.write(0, 0, 1234.56, style0)
ws1.write(1, 0, datetime.now(), style1)
ws1.write(2, 0, 1)
ws1.write(2, 1, 1)
ws1.write(2, 2, xlwt.Formula("A3+B3"))

ws2 = wb.add_sheet('sheet2')

for n in range(len(sheethead)):
	ws2.write(0, n, sheethead[n].value)

i = 1
for t in tags:
	for n in range(len(sheethead)):
		ws2.write(i, n, t[sheethead[n].value])
	i+=1


wb.save('example.xls')