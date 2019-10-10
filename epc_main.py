import requests
import re
import json

json_str = ''
with open('config.json') as f:
    json_str = f.read()
js = json.loads(json_str)
stuid = js['stuno']
passwd = js['passwd']


main_site = 'http://epc.ustc.edu.cn/main.asp'

situational_dlg_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2001'
topical_discus_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2002'
debate_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2003'
drama_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2004'

nleft_page = 'http://epc.ustc.edu.cn/n_left.asp'
record_page = 'http://epc.ustc.edu.cn/record_book.asp'

# visit the site and get cookies
default_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
                    }
s = requests.Session()
s.headers.update(default_headers)
s.get(main_site)
    # get check code's timestamp
nleft_text = s.get(nleft_page).text
timestamp = None
try:
    timestamp = re.search('<TD ><img src="(.*?)">', nleft_text).group(1)
except Exception:
    print("Parse error.")
timestamp = timestamp.split('checkcode.asp?')[1]
checkcode_path = 'http://epc.ustc.edu.cn/checkcode.asp'

img = s.get(checkcode_path, params = {timestamp:None}).content
# ---Rotine to recoginze check code---
with open('checkcode.png','wb') as f:
    f.write(img)
checkcode = input("Charcode:")
# ---
login_dict = {'submit_type': 'user_login',
    'name': stuid,
    'pass': passwd,
    'txt_check': checkcode,
    'user_type': 2,
    'Submit': 'LOG IN'
    }
res = s.post(nleft_page, data=login_dict)
if(res.status_code == 200):
    print('Logined.')
else:
    print('Login failed.')
    exit()

# First, check study hous
s.cookies.set('querytype','all')
res = s.get(record_page)
status_raw = res.text

all_hours = int(re.search(r'已预约的交流英语学时:(\d+)', status_raw).group(1))
studied_hours  = int(re.search(r'已获得的交流英语学时:(\d+)', status_raw).group(1))
planned_hours = all_hours - studied_hours # not greater than 4


pass
