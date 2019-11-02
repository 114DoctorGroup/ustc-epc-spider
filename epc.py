import requests
import re
import os
import json
from os import system
from datetime import datetime, timedelta
import check


# constant parameter of epc website
root_site = 'http://epc.ustc.edu.cn'
main_site = 'http://epc.ustc.edu.cn/main.asp'
situational_dlg_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2001'
topical_discus_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2002'
debate_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2003'
drama_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2004'
nleft_page = 'http://epc.ustc.edu.cn/n_left.asp'
record_page = 'http://epc.ustc.edu.cn/record_book.asp'
checkcode_path = 'http://epc.ustc.edu.cn/checkcode.asp'

# regular pattern 
course_form_patt = re.compile(r'(<form action="(m_practice.asp\?second_id.*?)".*?</form>)', re.DOTALL)
course_form_patt2 = re.compile(r'<form action="m_practice.asp\?second_id.*?".*?</form>', re.DOTALL)
form_tag_patt = re.compile('(<form action="(.*?)".*?</form>)', re.DOTALL)
td_tag_patt = re.compile('<td.*?</td>',re.DOTALL)
datetime_patt = re.compile(r'(\d+)/(\d+)/(\d+)<br>(\d+):(\d+)-')
name_in_td_patt = re.compile(r'<td.*?<a href.*?>(.*?)</a></td>')
week_patt = re.compile(r'<td align="center">第(\d+)周</td>')
weekday_patt = re.compile(r'<td align="center">周(\S)</td>')
class_type = ["Situational Dialogue",  "Drama", "Topical Discussion", "Debate"]

# visit the site and get cookies
default_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
}
 
# First, check study hours
def check_study_hours(s):
    s.cookies.set('querytype','all')
    res = s.get(record_page)
    status_raw = res.text

    all_hours = int(re.search(r'已预约的交流英语学时:(\d+)', status_raw).group(1))
    studied_hours  = int(re.search(r'已获得的交流英语学时:(\d+)', status_raw).group(1))
    absent_hours  = int(re.search(r'预约未上的交流英语学时：(\d+)', status_raw).group(1))
    planned_hours = all_hours - studied_hours - absent_hours # not greater than 4
    available_hours = 4 - planned_hours
    #print(all_hours, studied_hours, absent_hours)

    # Check the earliest course that has been planned
    candidate_dt = datetime.now() + timedelta(days = 365) # 默认时间为明年同一天，标识未选上任何课程
    candidate_params = None
    candidate_name = None

    form_list_raw = form_tag_patt.findall(status_raw)[1::] # remove the first form, which is not a course
    for form in form_list_raw:
        td_list = td_tag_patt.findall(form[0])
        dt_match = datetime_patt.search(td_list[6])
        dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
        planned = '预约中' in td_list[9]
        if len(replace_scandidate) > 0:
            nm = name_in_td_patt.search(td_list[0]).group(1)
            if(planned and replace_scandidate in nm):
                candidate_dt, candidate_params, candidate_name = dt, form[1], nm
            else:
                continue
        elif planned :
            if candidate_params is None: # 当前还没有替换对象
                candidate_dt = dt
                candidate_params = form[1]
                candidate_name = name_in_td_patt.search(td_list[0]).group(1)
            elif dt > candidate_dt: # 用时间最晚的来作为替换对象
                candidate_dt = dt
                candidate_params = form[1]
                candidate_name = name_in_td_patt.search(td_list[0]).group(1)
            else:
                pass
            
    return available_hours, candidate_dt, candidate_params, candidate_name

def check_earliest_course(s:requests.Session, page_url:str):
    # TODO: return course params and a datetime obj
    week_patt = re.compile(r'<td align="center">第(\d+)周</td>')
    page_raw = s.get(page_url+'&isall=some').text
    earliest_week = int(week_patt.search(page_raw).group(1))
    course_params = course_form_patt.search(page_raw).group(2)
    course_form = course_form_patt.search(page_raw).group(1)
    td_list = td_tag_patt.findall(course_form)

    dt_match = datetime_patt.search(td_list[5])
    dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))

    weekday_patt = re.compile(r'<td align="center">周(\S)</td>')
    weekday = weekday_patt.search(td_list[2]).group(1)

    return [earliest_week, dt, course_params, weekday]

def find_alternative(s:requests.Session, page_url:str, type_code:int):
    page_raw = s.get(page_url+'&isall=some').text

    all_course_form = course_form_patt2.findall(page_raw)
    
    for course_form in all_course_form:
        course_params = course_form_patt.search(course_form).group(2)
        td_list = td_tag_patt.findall(course_form)
    
        dt_match = datetime_patt.search(td_list[5])
        dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
    
        weekday = weekday_patt.search(td_list[2]).group(1)

        course = [dt, course_params, weekday]

        if "预约时间未到" in course_form: # 预约时间未到
            break
        elif "您已经预约过该时间段的课程" in course_form \
            or "已选择过该教师与话题相同的课程，不能重复选择" in course_form \
            or "取 消" in course_form:
            pass
        elif is_wanted_dt(course, class_type[type_code]): # find the first(earliest) course in this type
            return course
        else:
            pass

    return None

def order(course_params: str):
    book_form = {'submit_type':'book_submit',
                '截止日期':'end_date'}
    course_path = root_site + '/' + course_params
    res = s.post(course_path,book_form)
    succeed= not '操作失败' in res.text
    return succeed

def cancel(cancel_params: str):
    cancel_form = {'submit_type':'book_cancel',
                '截止日期':'end_date'}
    course_path = root_site + '/' + cancel_params
    res = s.post(course_path,cancel_form)
    succeed= not '操作失败' in res.text
    global available_hours
    if(succeed):
        # TODO: add support for 1 point courses
        available_hours += 2
    return succeed

def smart_order(course_params: str):
    global available_hours, candidate_dt, candidate_params, candidate_name

    if(available_hours == 1):
        print('Now we don\'t consider 1 point course.')
        return
    if(available_hours >= 2):
        print('可用预约学时足够，直接选课')
        if(order(course_params)):
            return True
        else:
            return False
    elif(replace_flag):
        # we're NOT considering the score being ONE!
        print('正在换课，将退课程：'+ str(candidate_dt)+' '+candidate_name)
        if(not cancel(candidate_params)):
            return False
        if(available_hours>=2):
            print('正在选课...')
            if(order(course_params)):
                return True
            else:
                # first roll back
                print('Failed. Rolling back...')
                candidate_params_order = candidate_params.replace('record_book.asp','m_practice.asp')
                if(not order(candidate_params_order)):
                    print('Roll back failed!')
                else:
                    print('Roll back succeed.')
                return False
    else:
        print('可用预约学时不足')

def is_wanted_dt(course: tuple, type) :
    course_date_str = '周' + course[2]
    
    if course[0].hour == 8 or course[0].hour == 9:
        course_date_str += '上午'
    if course[0].hour == 14:
        course_date_str += '下午'
    if course[0].hour == 19:
        course_date_str += '晚上'

    if course_date_str in banned_time :
        print("时间需求不满足：" + type + " " + str(course[0]) + "(" + course_date_str + ")")
        return False
    else :
        return True

def OrderCourseLoop(s):
    print('Situ(1)\tTopi(2)\tDeba(2)\tDrama(2)')
    
    global available_hours, candidate_dt, candidate_params, candidate_name
    
    available_hours, candidate_dt, candidate_params, candidate_name = check_study_hours(s)

    while True:
        for i, page in enumerate([situational_dlg_page, drama_page, topical_discus_page, debate_page]):
            if(not enable_array[i]):
                continue
                
            res = find_alternative(s, page+'&isall=some', i)

            if res is not None:
                if available_hours > 0:
                    smart_order(res[1])
                    available_hours, candidate_dt, candidate_params, candidate_name = check_study_hours(s)
                elif res[0].day < candidate_dt.day:
                    print('发现日期更早的可替代课程：' + class_type[i] + " " + str(res[0]))
                    smart_order(res[1])
                    available_hours, candidate_dt, candidate_params, candidate_name = check_study_hours(s)
                elif res[0].day == candidate_dt.day:
                    print('发现同一天的替代课程：' + class_type[i] + " " + str(res[0]))
                else:
                    pass
            
if __name__ == "__main__":
    # read the configuration in the json file
    json_str = ''
    with open('config.json', encoding = 'utf-8') as f:
        json_str = f.read()
    js = json.loads(json_str)
    stuid = js['stuno']
    passwd = js['passwd']
    order_flag = js['enable.order']
    replace_flag = js['enable.replace']
    replace_scandidate = js['replace_candidate']
    banned_time = js['banned_time']
    enable_array = [js['enable.situational_dialog'], js['enable.drama'], js['enable.topical_discuss'], js['enable.debate']]
    
    # candidate course to replace, global parameters
    available_hours = 0
    candidate_dt = None
    candidate_params = None
    candidate_name = ''
    
    while True:     
        try:
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
            img = s.get(checkcode_path, params = {timestamp:None}).content
            with open('checkcode.png','wb') as f:
                f.write(img)

            checkcode = check.Checkcode()
            print("checkcode: " + checkcode)
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
            
            OrderCourseLoop(s)
        except AttributeError:
            pass
        
        except:
            os.system("pause")
            exit(-1)