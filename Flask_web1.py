# -*- coding: utf-8 -*-
import os
from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_uploads import UploadSet, IMAGES, DEFAULTS, DATA, ARCHIVES, configure_uploads
from flask_wtf import Form
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import xlrd,xlwt,json,redis,os,sys,shutil
import xml.dom.minidom

pool0 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=0)
hr0 = redis.Redis(connection_pool=pool0)
pool1 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=1)
hr1 = redis.Redis(connection_pool=pool1)


app = Flask(__name__)
# 新建一个set用于设置文件类型、过滤等
set_myfile = UploadSet('myfile')  # mypic

# UPLOADED_xxxxx_DEST, xxxxx部分就是定义的set的名称, mypi, 下同
uploadpath = './tmp/xslx'
app.config['UPLOADED_MYFILE_DEST'] = uploadpath

# mypic 允许存储的类型, IMAGES为预设的 tuple('jpg jpe jpeg png gif svg bmp'.split())
app.config['UPLOADED_MYFILE_ALLOW'] = DEFAULTS

app.static_folder

# 把刚刚app设置的config注册到set_mypic
configure_uploads(app, set_myfile)

app.config['SECRET_KEY'] = 'xxxxx'
path = sys.path[0]
print(path)

os.chdir(path)


leftnavlist = [{'ico': 'fa-tachometer', 'name': '控制台', 'url': '/'}, {'ico': 'fa-paw', 'name': '设备池', 'url': '/devpool'},
	{'ico': 'fa-cogs', 'name': '采集服务', 'url': '/acquisition'}, {'ico': 'fa-upload', 'name': '数据推送', 'url': '/datapush'},
	{'ico': 'fa-tasks', 'name': '网络配置', 'url': '/network'}, ]

@app.route('/')
@app.route('/home/<name>')
def index(name=None):
	if not name:
		name='NoName'
	user = { 'nickname': name } # fake user
	return render_template("index.html",
		leftnavlist = leftnavlist,
		title = 'Home',
		user = user)

@app.route('/get_devinfo/<devname>', methods={'GET', 'POST'})
def get_devinfo(devname=None):
	if devname:
		devinfo = eval(hr0.hget('DevsPool_list', devname))
		return json.dumps(devinfo)
	else:
		return '{"message":"no devid"}'

@app.route('/deldev/<devname>', methods={'GET', 'POST'})
def deldev(devname=None):
	if request.method == 'GET':
		return "请使用POST方法提交"
	if request.method == 'POST':
		if devname:
			try:
				hr0.hdel('DevsPool_list', devname)
			except Exception as e:
				return e
			else:
				if os.path.isdir("devices/" + devname):
					shutil.rmtree("devices/" + devname)

				message = {'message': 'del '+devname+' successful'}
				return json.dumps(message)
		else:
			return json.dumps({"message": "no devid"})

@app.route('/get_devtags')
def get_devtags():
	tags = {'tags':[]}
	try:
		devname = request.args['devname']
	except Exception as e:
		return json.dumps(tags)
	else:
		print(devname)
		if os.path.isfile("devices/" + devname + "/" + devname + ".xls"):
			excelbook = xlrd.open_workbook("devices/" + devname + "/" + devname + ".xls")
			print("表单数量:", excelbook.nsheets)
			print("表单名称:", excelbook.sheet_names())
			sh = excelbook.sheet_by_index(0)
			print("表单名称：{0},行数：{1},列数：{2}".format(sh.name, sh.nrows, sh.ncols))
			# print("Cell D20 is {0}".format(sh.cell_value(rowx=19, colx=3)))
			sheethead = sh.row(0)
			print("表头：", sheethead)
			devtags = []
			for rx in range(1, sh.nrows):
				# print(sh.row(rx))
				tag = {}
				for n in range(len(sheethead)):
					tag[sheethead[n].value] = sh.row(rx)[n].value
				devtags.append(tag)
			newtags = {'tags': devtags}
			return json.dumps(newtags)

		else:
			return json.dumps(tags)



@app.route('/adddev/<devname>', methods={'GET', 'POST'})
def adddev(devname=None):
	if request.method == 'GET':
		return "请使用POST方法提交新建设备信息"
	if request.method == 'POST':
		if devname:
			devinfo = json.loads(request.get_data().decode('utf-8'))
			print(devinfo)
			devinfotoredis = devinfo['devinfo']
			#del devinfotoredis['Protocol_paramter']['extend_parameter']
			#print(devinfotoredis)
			hr0.hdel('DevsPool_list', devname)
			hr0.hset('DevsPool_list', devname, json.dumps(devinfotoredis))
			if os.path.isdir("devices/" + devname):
				pass
			else:
				os.makedirs("devices/" + devname, 755)
				if os.path.isfile(uploadpath + '/' + devname + ".xls"):
					shutil.move(uploadpath + '/' + devname + ".xls", "devices/" + devname + "/" + devname + ".xls")
			return '{"message":"save successful"}'
		else:
			return '{"message":"no devid"}'

@app.route('/devpool', methods=('GET', 'POST'))
def devpool():
	devs = []
	devkeys = hr0.hkeys("DevsPool_list")
	for devkey in devkeys:
		devinfo = {}
		devinfo['dev_id'] = devkey.decode('ascii')
		devinfo['devinfo'] = eval(hr0.hget("DevsPool_list", devkey))
		devs.append(devinfo)
	protocollist = []
	protocoldict = {}
	iodevinfodict = {}
	print(devs)
	for parent, dirnames, files in os.walk("iodrivers"):
		if dirnames:
			print("############################################")
			for dirname in dirnames:
				for p, d, f in os.walk("iodrivers" + "/" + dirname):
					if f:
						if os.path.isfile("iodrivers" + "/" + dirname + "/" + dirname + ".xml"):
							# 打开xml文档
							try:
								dom = xml.dom.minidom.parse("iodrivers" + "/" + dirname + "/" + dirname + ".xml")
							except Exception as e:
								print('exception catched : ', e)
							else:
								cc = dom.getElementsByTagName('Protocol_Name')
								Protocol_Name = cc[0].firstChild.data
								cc = dom.getElementsByTagName('Protocol_ver')
								Protocol_ver = cc[0].firstChild.data
								cc = dom.getElementsByTagName('dev_type')
								dev_type = cc[0].firstChild.data
								cc = dom.getElementsByTagName('dev_manufacturer')
								dev_manufacturer = cc[0].firstChild.data
								cc = dom.getElementsByTagName('dev_model')
								dev_model = cc[0].firstChild.data
								iodevinfo = {'dev_type': dev_type,'dev_manufacturer': dev_manufacturer,'dev_model': dev_model}
								extend_parameters = dom.getElementsByTagName("extend_parameter")
								e_p = []
								for e in extend_parameters:
									Node1 = e.getElementsByTagName("name")[0]
									Node2 = e.getElementsByTagName("parameter")[0]
									e_p.append({'name': Node1.childNodes[0].nodeValue,
									            'parameter': Node2.childNodes[0].nodeValue})
								protocol = {'Protocol_Name': Protocol_Name, 'Protocol_ver': Protocol_ver,
								            'extend_parameter': e_p}
							print(protocol)
							protocollist.append(dirname)
							protocoldict[dirname] = protocol
							iodevinfodict[dirname] = iodevinfo
	return render_template('devpool.html', leftnavlist=leftnavlist, title='devpool', devs=devs, protocollist=protocollist, protocoldict=protocoldict, iodevinfodict=iodevinfodict)



@app.route('/acquisition')
def acquisition():
	return render_template("acquisition.html", leftnavlist=leftnavlist, title='acquisition')

@app.route('/datapush')
def datapush():
	return render_template("datapush.html", leftnavlist=leftnavlist, title='datapush')

@app.route('/upload/<devname>', methods=('GET', 'POST'))
def upload(devname=None):

	if request.method == 'POST':
		if devname:
			print(devname)
			print(request.files)
			upload_file = request.files['upfile']
			if upload_file:
				fname = secure_filename(upload_file.filename)
				upload_file.save(os.path.join(uploadpath, fname))
				print(upload_file.filename, upload_file.content_type)
				if os.path.isdir("devices/"+devname):
					print("devices/"+devname,"目录存在，开始移动文件")
					shutil.move(uploadpath + '/' + upload_file.filename,"devices/"+devname+"/"+devname+".xls")
					excelbook = xlrd.open_workbook("devices/"+devname+"/"+devname+".xls")
				else:
					print("devices/"+devname+"目录不存在，读取上传路径文件")
					shutil.move(uploadpath + '/' + upload_file.filename, uploadpath + '/' + devname + ".xls")
					excelbook = xlrd.open_workbook(uploadpath + '/' + devname + ".xls")
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
				return json.dumps(newtags)
		else:
			return "未包含设备ID信息"
	elif request.method == 'GET':
		if devname:
			if os.path.isfile("devices/" + devname + "/" + devname + ".xls"):
				print("devices/" + devname, "目录存在，开始读取文件")
				excelbook = xlrd.open_workbook("devices/" + devname + "/" + devname + ".xls")
			else:
				print("devices/" + devname + "目录不存在，读取上传路径文件")
				excelbook = xlrd.open_workbook(uploadpath + '/' + devname + ".xls")
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
			return json.dumps(newtags)
		else:
			newtags = {'tags': []}
			return json.dumps(newtags)

@app.route('/network', methods=('GET', 'POST'))
def network():
	fftags = {'tags': []}
	#print('@@@@@', os.getcwd())
	if request.method == 'GET':
		return render_template('network.html', leftnavlist=leftnavlist, title='network', newtags=fftags)
	elif request.method == 'POST':
		r = request.files
		print(r)
		upload_file = r['data']
		print(upload_file)
		return "200"




@app.route('/downtable/<devname>', methods=('GET', 'POST'))
def downtable(devname=None):
	if devname:
		sheethead = ['tagname', 'tagdesc', 'fc', 'reg', 'datatype']
		devtags = eval(hr0.get(devname))['tags']
		wb = xlwt.Workbook()
		ws2 = wb.add_sheet('sheet1', cell_overwrite_ok=True)
		for n in range(len(sheethead)):
			ws2.write(0, n, sheethead[n])
		i = 1
		for t in devtags:
			for n in range(len(sheethead)):
				ws2.write(i, n, t[sheethead[n]])
			i += 1
		wb.save('./static/downloads/' + devname + '.xls')
		return redirect('/static/downloads/' + devname + '.xls')
	else:
		return '未包含设备ID'

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=5000, debug=True)
