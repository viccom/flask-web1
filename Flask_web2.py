# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_uploads import UploadSet, IMAGES, DEFAULTS, DATA, ARCHIVES, configure_uploads
from flask_wtf import Form
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_bootstrap import Bootstrap
import xlrd, xlwt,json ,redis

pool0 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=0)
hr0 = redis.Redis(connection_pool=pool0)
pool1 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=1)
hr1 = redis.Redis(connection_pool=pool1)
pool2 = redis.ConnectionPool(host='127.0.0.1', port='6379', db=2)
hr2 = redis.Redis(connection_pool=pool2)

app = Flask(__name__)

# 新建一个set用于设置文件类型、过滤等
set_myfile = UploadSet('myfile')  # mypic

# 用于wtf.quick_form()模版渲染
bootstrap = Bootstrap(app)

# mypic 的存储位置,
# UPLOADED_xxxxx_DEST, xxxxx部分就是定义的set的名称, mypi, 下同
uploadpath = 'static/uploads'
app.config['UPLOADED_MYFILE_DEST'] = './'+uploadpath

# mypic 允许存储的类型, IMAGES为预设的 tuple('jpg jpe jpeg png gif svg bmp'.split())
app.config['UPLOADED_MYFILE_ALLOW'] = DEFAULTS

# 把刚刚app设置的config注册到set_mypic
configure_uploads(app, set_myfile)

app.config['SECRET_KEY'] = 'xxxxx'

# 此处WTF的SCRF密码默认为和flask的SECRET_KEY一样
# app.config['WTF_CSRF_SECRET_KEY'] = 'wtf csrf secret key'


class UploadForm(Form):
    '''
        一个简单的上传表单
    '''

    # 文件field设置为‘必须的’，过滤规则设置为‘set_mypic’
    upload = FileField('', validators=[
                       FileRequired(), FileAllowed(set_myfile, 'you can upload images only!')])
    submit = SubmitField('确定')


@app.route('/network', methods=('GET', 'POST'))
def network():
    form = UploadForm()
    fftags = {'tags': []}
    url = None
    if form.validate_on_submit():
        filename = form.upload.data.filename
        url = set_myfile.save(form.upload.data, name=filename)

        excelbook = xlrd.open_workbook('./'+ uploadpath + '/' + url)
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
        for t in newtags['tags']:
            print(t)

        #return redirect('/static/uploads/'+url)
        return render_template('upload.html', form=form, url=url, newtags=newtags, uploadpath=uploadpath)
    else:
        return render_template('upload.html', form=form, url=url, newtags=fftags, uploadpath=uploadpath)

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
    #return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)