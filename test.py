import datetime
import time

utc = "2017-05-05T16:35:53.226Z"
UTC_FORMAT1 = "%Y-%m-%dT%H:%M:%S.%fZ"
UTC_FORMAT2 = "%Y-%m-%dT%H:%M:%SZ"
LOCAL_FORMAT = "%Y-%m-%d %H:%M:%S"


def utc2local(utc_st):
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st

try:
	utc_time = datetime.datetime.strptime(utc, UTC_FORMAT1)
except Exception as err:
	pass

if not 'utc_time' in dir():
	try:
		utc_time = datetime.datetime.strptime(utc, UTC_FORMAT2)
	except Exception as err:
		pass
local_time = utc2local(utc_time).strftime("%Y-%m-%d %H:%M:%S")
print(local_time)
