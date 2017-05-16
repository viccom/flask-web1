import datetime
import time
import xlrd,xlwt,json,redis,os,sys
import xml.dom.minidom

#{"dev_Id": "m32sx924efcas", "dev_Type": "电表", "dev_Manufacturer": "威胜仪表", "dev_Model": "DSSD331", "dev_Protocol":"Modbus"}
for parent, dirnames, files in os.walk("devices"):
	devs = []
	if dirnames:
		print("############################################")
		for dirname in dirnames:
			for p, d, f in os.walk("devices"+"/"+dirname):
				if f:
					if os.path.isfile("devices"+"/"+dirname+"/"+dirname+".xml"):
						# 打开xml文档
						try:
							dom = xml.dom.minidom.parse("devices"+"/"+dirname+"/"+dirname+".xml")
						except Exception as e:
							print('exception catched : ', e)
						else:
							cc = dom.getElementsByTagName('Protocol_Name')
							Protocol_Name = cc[0].firstChild.data
							cc = dom.getElementsByTagName('Protocol_ver')
							Protocol_ver = cc[0].firstChild.data
							extend_parameters = dom.getElementsByTagName("extend_parameter")
							e_p = []
							for e in extend_parameters:
								Node1 = e.getElementsByTagName("name")[0]
								Node2 = e.getElementsByTagName("parameter")[0]
								e_p.append(
									{'name': Node1.childNodes[0].nodeValue, 'parameter': Node2.childNodes[0].nodeValue})
							protocol = {'Protocol_Name': Protocol_Name, 'Protocol_ver': Protocol_ver,
							            'extend_parameter': e_p}
						print(protocol)
						print("############################################")
						pass
					if os.path.isfile("devices"+"/"+dirname+"/"+dirname+".xls"):
						excelbook = xlrd.open_workbook("devices"+"/"+dirname+"/"+dirname+".xls")
						print("表单数量:", excelbook.nsheets)
						print("表单名称:", excelbook.sheet_names())
						sh = excelbook.sheet_by_index(0)
						print("表单名称：{0},行数：{1},列数：{2}".format(sh.name, sh.nrows, sh.ncols))
						# print("Cell D20 is {0}".format(sh.cell_value(rowx=19, colx=3)))
						sheethead = sh.row(0)
						print("表头：", sheethead)
						tags = []
						for rx in range(1, sh.nrows):
							# print(sh.row(rx))
							tag = {}
							for n in range(len(sheethead)):
								tag[sheethead[n].value] = sh.row(rx)[n].value
								pass
							tags.append(tag)
							newtags = {'tags': tags}


			print("############################################")
	elif files:
		pass
	else:
		print("nothing!")