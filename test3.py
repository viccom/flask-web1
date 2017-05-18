#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import json
import os
import hashlib
from time import sleep

fileupurl = 'http://symgrid.com:5000/upfile'
md5upurl = 'http://symgrid.com:5000/upfilemd5'

rs = requests.post(md5upurl, data=json.dumps(
                    {'filename': '1', 'filemd5': '2'}), timeout=5)
