import requests
import re
import json
from os import system
from datetime import datetime

json_str = ''
with open('config.json') as f:
    json_str = f.read()
js = json.loads(json_str)
stuid = js['stuno']
passwd = js['passwd']
order_flag = js['enable.order']
replace_flag = js['enable.replace']
order_week_beforeequal = js['order_week_beforeequal']
replace_candidate = js['replace.candidate']
replaec_forbidden = js['replace.forbidden']
verbose_mode = js['verbose']
course_forbidden = js['course.forbidden']

enable_array = [js['enable.situational_dialog'], js['enable.topical_discuss'], js['enable.debate'], js['enable.drama']]

root_site = 'http://epc.ustc.edu.cn'
main_site = 'http://epc.ustc.edu.cn/main.asp'

situational_dlg_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2001'
topical_discus_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2002'
debate_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2003'
drama_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2004'

nleft_page = 'http://epc.ustc.edu.cn/n_left.asp'
record_page = 'http://epc.ustc.edu.cn/record_book.asp'

class Course:
    def __init__(self, params, start_time: datetime, name: str, score: int, week: int):
        self.params = params
        self.week = week
        self.start_time = start_time
        self.name = name
        self.score = score
    
    
selected_courses = []
# TODO: maintain selected_courses in order, cancel

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

course_form_patt = re.compile(r'(<form action="(m_practice.asp\?second_id.*?)".*?</form>)', re.DOTALL)
form_tag_patt = re.compile('(<form action="(.*?)".*?</form>)', re.DOTALL)
td_tag_patt = re.compile('<td.*?</td>',re.DOTALL)
td_content_patt = re.compile('<td.*?>(.*?)</td>',re.DOTALL)
datetime_patt = re.compile(r'(\d+)/(\d+)/(\d+)<br>(\d+):(\d+)-')
name_in_td_patt = re.compile(r'<td.*?<a href.*?>(.*?)</a></td>')

# First, check study hours
# Refresh selected_course
def check_study_hours(s):
    selected_courses.clear()
    s.cookies.set('querytype','all')
    res = s.get(record_page)
    status_raw = res.text
    all_hours = int(re.search(r'已预约的交流英语学时:(\d+)', status_raw).group(1))
    studied_hours  = int(re.search(r'已获得的交流英语学时:(\d+)', status_raw).group(1))
    disobey_hours = int(re.search(r'预约未上的交流英语学时：(\d+)', status_raw).group(1))
    planned_hours = all_hours - studied_hours - disobey_hours # not greater than 4
    available_hours = 4 - planned_hours

    # Check the earliest course that has been planned
    candidate = None
    candidate_courses = []
    candidate_dt = None
    candidate_params = None
    candidate_name = None

    form_list_raw = form_tag_patt.findall(status_raw)[1::] # remove the first form, which is not a course
    for form in form_list_raw:
        try:
            td_list = td_tag_patt.findall(form[0])
            dt_match = datetime_patt.search(td_list[6])
            dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
            planned = '预约中' in td_list[9]
            nm = name_in_td_patt.search(td_list[0]).group(1)
            # skip if score is non digit
            score = int(td_content_patt.search(td_list[2]).group(1))
            week  = int(td_content_patt.search(td_list[4]).group(1))
        except Exception as e:
            print('Parse error. The item is ignored.')
            print(str(e))
        else:
            # add to selected_courses first
            c = Course(form[1], dt, nm, score, week)
            selected_courses.append(c)
            if(c.name != replaec_forbidden):
                candidate_courses.append(c)
            if len(replace_candidate)>0:
                if(planned and replace_candidate in nm):
                    candidate_dt, candidate_params, candidate_name = dt, form[1], nm
                    candidate = Course(form[1],dt,nm,2,week)
                else:
                    continue
            # By default, choose the latest as the candidate
            elif planned and (candidate is None or dt>candidate.start_time):
                candidate_dt = dt
                candidate_params = form[1]
                candidate_name = name_in_td_patt.search(td_list[0]).group(1)
                candidate = Course(form[1],dt,nm,score,week)
    #TODO: sort candidate_courses
    #TODO: code here is WRONG
    if(candidate_name is None):
        print('No course candidate found, fall back to the first course')
        td_list = td_tag_patt.findall(form[0])
        dt_match = datetime_patt.search(td_list[6])
        dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
        candidate_dt, candidate_params, candidate_name = dt, form[1], name_in_td_patt.search(td_list[0]).group(1)
    else:
        print('Course candidate to be replaced: '+candidate_name+' at '+str(candidate_dt))
    return available_hours, candidate_dt, candidate_params, candidate_name

available_hours, candidate_dt, candidate_params, candidate_name = check_study_hours(s)

print('Situ(1)\tTopi(2)\tDeba(2)\tDrama(2)')

old_state = [0,0,0,0]

week_patt = re.compile(r'<td align="center">第(\d+)周</td>')

order_msg_patt = re.compile(r'<tr><td colspan="2" style="padding-left:20px; padding-right:20px;color:#000000; font-weight:bold;">\s*(.*?)\s*</td', re.DOTALL)

def check_unfull_courses(s:requests.Session, page_url:str):
    pass

def check_earliest_course(s:requests.Session, page_url:str):
    week_patt = re.compile(r'<td align="center">第(\d+)周</td>')
    page_raw = s.get(page_url+'&isall=some').text
    earliest_week = int(week_patt.search(page_raw).group(1))
    course_params = course_form_patt.search(page_raw).group(2)
    course_form = course_form_patt.search(page_raw).group(1)
    td_list = td_tag_patt.findall(course_form)
    course_name = name_in_td_patt.search(td_list[0]).group(1)
    dt_match = datetime_patt.search(td_list[5])
    dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
    return [earliest_week, dt, course_params, course_name]

def course_duplicate(name:str):
    for c in selected_courses:
        if name in c.name:
            return True
    return False

def order(course_params: str):
    book_form = {'submit_type':'book_submit',
                '截止日期':'end_date'}
    course_path = root_site + '/' + course_params
    res = s.post(course_path,book_form)
    succeed= not '操作失败' in res.text
    with open('log.txt','w') as f:
        f.write(res.text)
    operation_msg = None
    try:
        operation_msg = order_msg_patt.search(res.text).group(1)
    except Exception:
        print('Operation message parse failed.')
    global available_hours
    if(succeed):
        # TODO: add support for 1 point courses
        available_hours -= 2
    return succeed, operation_msg

def cancel(cancel_params: str):
    cancel_form = {'submit_type':'book_cancel',
                '截止日期':'end_date'}
    course_path = root_site + '/' + cancel_params
    res = s.post(course_path,cancel_form)
    succeed= not '操作失败' in res.text
    global available_hours
    #TODO: add msg here
    if(succeed):
        # TODO: add support for 1 point courses
        available_hours += 2
    return succeed

def smart_order(course_params: str):
    global available_hours
    if(available_hours == 1):
        print('Now we don\'t consider 1 point course.')
        return
    if(available_hours>=2):
        print('可用预约学时足够，直接选课')
        order_res = order(course_params)
        if(order_res[0]):
            return True
        else:
            print('选课失败，原因：'+order_res[1])
            return False
    elif(replace_flag):
        # we're NOT considering the score being ONE!
        print('正在换课， 将退课程：'+str(candidate_dt)+' '+candidate_name)
        if(not cancel(candidate_params)):
            return False
        if(available_hours>=2):
            print('正在选课...')
            order_res = order(course_params)
            if(order_res[0]):
                return True
            else:
                # first roll back
                print('选课失败，原因：' + order_res[1])
                print('正在回滚...')
                candidate_params_order = candidate_params.replace('record_book.asp','m_practice.asp')
                rb_res = order(candidate_params_order)
                if(not rb_res[0]):
                    print('回滚失败! 原因：'+rb_res[1])
                else:
                    print('回滚成功.')
                return False
    else:
        print('可用预约学时不足')

#--- test part
# Only print for situational dialog.
while True:
    #situational_res = check_earliest_course(s,situational_dlg_page+'&isall=some')
    #print(str(situational_res[0]), end='\t', flush=True)
    for i, page in enumerate([situational_dlg_page, topical_discus_page, debate_page, drama_page]):
        if(not enable_array[i]):
            if verbose_mode:
                print('', end='\t')
            continue
        res = check_earliest_course(s, page+'&isall=some')
        if verbose_mode:
            print(str(res[0]), end='\t', flush=True)
        duplicate = course_duplicate(res[3]) or res[3] in course_forbidden
        case1 = res[0] <= order_week_beforeequal and order_week_beforeequal>0
        case2 = order_week_beforeequal==0 and res[1]<candidate_dt
        if(case1 or case2):
            if(duplicate):
                print('发现更早的可替代课程：'+str(res[1])+' '+ res[3] + ',但这门课已经上过')
            else:
                print('发现更早的可替代课程：'+str(res[1])+' '+ res[3])
                if(order_flag):
                    if(smart_order(res[2])):
                        print('换课成功！')
                        exit(0)
                    else:
                        print('换课失败')
                        exit(0)
    if verbose_mode:
        print('')
            # if(not r[0] and r[1]=='Order Failed'):
            #     print('换课失败，且已退课，正在尝试回滚')

            # elif(not r[0] and r[1]=='Cancel Failed'):
            #     print('换课失败，但未退课')
            # elif(r[0]):
            #     print('换课成功')

#--------------

while True:
    situatioinal_str = s.get(situational_dlg_page+'&isall=some').text
    situational_week = int(week_patt.search(situatioinal_str).group(1))
    print(str(situational_week), end='\t', flush=True)
    if(situational_week<old_state[0]):
        #send email
        pass
    topical_str = s.get(topical_discus_page+'&isall=some').text
    topical_week = int(week_patt.search(topical_str).group(1))
    print(str(topical_week), end='\t\t', flush=True)
    if(topical_week<old_state[1]):
        #send email
        pass
    debate_str = s.get(debate_page+'&isall=some').text
    debate_week = int(week_patt.search(debate_str).group(1))
    print(str(debate_week), end='\t', flush=True)
    if(debate_week<old_state[2]):
        #send email
        pass
    drama_week = int(week_patt.search(s.get(drama_page+'&isall=some').text).group(1))
    print(str(drama_week), flush=True)
    if(drama_week<old_state[3]):
        #send email
        pass
    old_state = [situational_week, topical_week, debate_week, drama_week]
pass


