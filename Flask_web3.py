# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_uploads import UploadSet, IMAGES, DEFAULTS, DATA, ARCHIVES, configure_uploads
from flask_wtf import Form
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_bootstrap import Bootstrap
import xlrd, xlwt
import json


app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index(name=None):
    user = { 'nickname': 'viccom' } # fake user
    return render_template("home.html",
        title = 'Home',
        user = user)

if __name__ == '__main__':
    app.run(debug=True)