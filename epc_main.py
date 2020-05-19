import requests
import re
import io
import json
import yzm_wc
import logger
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
duplicate_flag = js['enable.duplicate']
loop_flag = js['enable.loop']
order_week_beforeequal = js['order_week_beforeequal']
order_week_afterequal = js['order_week_afterequal']
replace_earlier = js['replace.earlier']
replace_candidate = js['replace.candidate']
replaec_forbidden = js['replace.forbidden']
verbose_mode = js['verbose']
course_forbidden = js['course.forbidden']
course_favorite = js['course.favorite']

enable_array = [js['enable.situational_dialog'], js['enable.topical_discuss'], js['enable.debate'], js['enable.drama']]

root_site = 'http://epc.ustc.edu.cn'
main_site = 'http://epc.ustc.edu.cn/main.asp'

situational_dlg_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2001'
topical_discus_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2002'
debate_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2003'
drama_page = 'http://epc.ustc.edu.cn/m_practice.asp?second_id=2004'

nleft_page = 'http://epc.ustc.edu.cn/n_left.asp'
nright_page = 'http://epc.ustc.edu.cn/n_right.asp'
nbottom_page = 'http://epc.ustc.edu.cn/n_bottom.asp'
record_page = 'http://epc.ustc.edu.cn/record_book.asp'

class Course:
    def __init__(self, params, start_time: datetime, name: str, score: int, week: int, order_open=False, selectable=False):
        self.params = params
        self.week = week
        self.start_time = start_time
        self.name = name
        self.score = score
        self.order_open = order_open
        self.selectable = selectable

# all, including planned and finished
selected_courses = []
# only planned
planned_courses = []
# TODO: maintain selected_courses in order, cancel

# visit the site and get cookies
default_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
                    }
s = requests.Session()
s.headers.update(default_headers)

def login():
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
    checkcode = yzm_wc.get_yzm_from_bytes(img)
    login_dict = {'submit_type': 'user_login',
        'name': stuid,
        'pass': passwd,
        'txt_check': checkcode,
        'user_type': 2,
        'Submit': 'LOG IN'
        }
    res = s.post(nleft_page, data=login_dict)
    if(res.status_code == 200 and '点击可注销本次登录' in res.text):
        logger.default_logger.log('Logined.')
        return True
    else:
        logger.default_logger.log('Login failed.')
        return False

if not login():
    exit(0)

course_form_patt = re.compile(r'(<form action="(m_practice.asp\?second_id.*?)".*?</form>)', re.DOTALL)
form_tag_patt = re.compile('(<form action="(.*?)".*?</form>)', re.DOTALL)
td_tag_patt = re.compile('<td.*?</td>',re.DOTALL)
td_content_patt = re.compile('<td.*?>(.*?)</td>',re.DOTALL)
datetime_patt = re.compile(r'(\d+)/(\d+)/(\d+)<br>(\d+):(\d+)-')
name_in_td_patt = re.compile(r'<td.*?<a href.*?>(.*?)</a></td>')

hours_enough = False

# First, check study hours
# Refresh selected_course
def check_study_hours(s):
    selected_courses.clear()
    s.cookies.set('querytype','all')
    res = s.get(record_page)
    status_raw = res.text
    all_hours = int(re.search(r'已预约的交流英语学时:(\d+)', status_raw).group(1))
    # studied_hours  = int(re.search(r'已获得的交流英语学时:(\d+)', status_raw).group(1))
    studied_hours = 0
    disobey_hours = int(re.search(r'预约未上的交流英语学时：(\d+)', status_raw).group(1))
    need_candidate = True # set to True at first
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
            # remove the zoom column
            if 'zoom' in td_list[0]:
                td_list = td_list[1::]
            studied = '已刷卡上课' in td_list[9]
            planned = '预约中' in td_list[9]
            dt_match = datetime_patt.search(td_list[6])
            dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
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
            if(planned):
                planned_courses.append(c)
            if studied:
                studied_hours += c.score
            if need_candidate:
                if(c.name != replaec_forbidden):
                    candidate_courses.append(c)
                if len(replace_candidate)>0:
                    if(planned and replace_candidate in nm):
                        candidate_dt, candidate_params, candidate_name = dt, form[1], nm
                        #candidate = Course(form[1],dt,nm,2,week)
                        candidate = c
                    else:
                        continue
                # By default, choose the latest as the candidate
                elif planned and (candidate is None or dt>candidate.start_time):
                    candidate_dt = dt
                    candidate_params = form[1]
                    candidate_name = name_in_td_patt.search(td_list[0]).group(1)
                    candidate = c
    planned_hours = all_hours - studied_hours - disobey_hours # not greater than 4
    left_hours = 20 - studied_hours
    available_hours = 4 - planned_hours
    available_hours = min(available_hours, left_hours)
    hours_enough = available_hours >= 2
    need_candidate = not hours_enough and replace_flag
    if need_candidate:
        #TODO: sort candidate_courses
        #TODO: code here is WRONG
        if(candidate_name is None):
            print('No course candidate found, fall back to the first course')
            td_list = td_tag_patt.findall(form[0])
            dt_match = datetime_patt.search(td_list[6])
            dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
            candidate_dt, candidate_params, candidate_name = dt, form[1], name_in_td_patt.search(td_list[0]).group(1)
        else:
            logger.default_logger.log('可能会被替换的课程: '+candidate_name+' at '+str(candidate_dt))
    else:
        candidate = None
        if hours_enough:
            print('学时足够，无需被替代课程')
        else:
            print('已禁用换课，无需被替代课程')
    return available_hours, candidate, hours_enough

available_hours, candidate_course, hours_enough = check_study_hours(s)

old_state = [0,0,0,0]

week_patt = re.compile(r'<td align="center">第(\d+)周</td>')

order_msg_patt = re.compile(r'<tr><td colspan="2" style="padding-left:20px; padding-right:20px;color:#000000; font-weight:bold;">\s*(.*?)\s*</td', re.DOTALL)

def check_unfull_courses(s:requests.Session, page_url:str):
    pass

def check_earliest_course(s:requests.Session, page_url:str, retry_num = 3):
    week_patt = re.compile(r'<td align="center">第(\d+)周</td>')
    page_res = s.get(page_url+'&isall=some')
    page_raw = page_res.text
    try:
        earliest_week = int(week_patt.search(page_raw).group(1))
        course_params = course_form_patt.search(page_raw).group(2)
        course_form = course_form_patt.search(page_raw).group(1)
        td_list = td_tag_patt.findall(course_form)
        course_name = name_in_td_patt.search(td_list[0]).group(1)
        dt_match = datetime_patt.search(td_list[5])
        dt = datetime(int(dt_match.group(1)),int(dt_match.group(2)),int(dt_match.group(3)),int(dt_match.group(4)),int(dt_match.group(5)))
        order_open = not '预约时间未到' in course_form
        selectable = True # TODO: need to figure out!
    except Exception as eee:
        # is kicked out?
        if('登录后可以查看详细信息' in page_raw):
            if(retry_num==0):
                logger.default_logger.log('重新登录失败')
                exit(-1)
            logger.default_logger.log('已被踢下线，正在重新登录')
            login()
            return check_earliest_course(s, page_url, retry_num-1)
        else:
            if(page_res.status_code != 200):
                logger.default_logger.log(str(page_res.status_code)+' 连接出现问题，网站可能暂时挂掉了...')
            print(str(eee))
            return None
    else:
        return Course(course_params, dt, course_name, 2, earliest_week, order_open, selectable)
        #return [earliest_week, dt, course_params, course_name]

def course_duplicate(cc: Course, allowdup = False):
    ls = None
    if allowdup:
        ls = planned_courses
    else:
        ls = selected_courses
    for c in ls:
        if cc.name == c.name:
            if replace_flag and c in planned_courses and cc.start_time<c.start_time:
                return False, c
            return True, c
    return False, None

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

def smart_order(course_params: str, cdd = candidate_course):
    # TODO: check the field selectable, and report error if false
    # we shouldn't have reached here if it's false
    global available_hours
    if(available_hours == 1):
        logger.default_logger.log('Now we don\'t consider 1 point course.')
        return
    if available_hours>=2 and cdd is None:
        logger.default_logger.log('可用预约学时足够，直接选课')
        order_res = order(course_params)
        if(order_res[0]):
            return True
        else:
            logger.default_logger.log('选课失败，原因：'+order_res[1])
            return False
    elif(replace_flag):
        # we're NOT considering the score being ONE!
        logger.default_logger.log('正在换课， 将退课程：'+str(cdd.start_time)+' '+cdd.name)
        if(not cancel(cdd.params)):
            logger.default_logger.log('退课失败。仍尝试选课')
        # if(available_hours>=2):
        logger.default_logger.log('正在选课...')
        order_res = order(course_params)
        if(order_res[0]):
            return True
        else:
            # first roll back
            logger.default_logger.log('选课失败，原因：' + order_res[1])
            logger.default_logger.log('正在回滚...')
            candidate_params_order = cdd.params.replace('record_book.asp','m_practice.asp')
            rb_res = order(candidate_params_order)
            if(not rb_res[0]):
                logger.default_logger.log('回滚失败! 原因：'+rb_res[1])
            else:
                logger.default_logger.log('回滚成功.')
            return False
    else:
        logger.default_logger.log('可用预约学时不足')

logger.default_logger.log('开始捡漏')
logger.default_logger.log('可用预约学时：'+ str(available_hours))

print('Situ(1)\tTopi(2)\tDeba(2)\tDrama(2)')

def time_conflict(c: Course, curr_ccd: Course):
    # compare with planned_courses
    for p in planned_courses:
        if p.start_time==c.start_time:
            if replace_flag and p is curr_ccd:
                # candidate_coures not None, so replace enabled
                return False
            return True
                # not conflicted
                # TODO: return false and use p as the replace candidate
                # return False, p
    return False

while True:
    for i, page in enumerate([situational_dlg_page, topical_discus_page, debate_page, drama_page]):
        if(not enable_array[i]):
            if verbose_mode:
                print('', end='\t')
            continue
        res = check_earliest_course(s, page+'&isall=some')
        if res is None:
            logger.default_logger.log('未查找到课程 稍后重试')
            continue
        if verbose_mode:
            print(str(res.week), end='\t', flush=True)
        if not res.order_open:
            continue
        range_valid = order_week_afterequal <= order_week_beforeequal and order_week_afterequal >= 0
        in_range = res.week >= order_week_afterequal and res.week <= order_week_beforeequal and range_valid
        
        if not range_valid:
            logger.default_logger.log('最小周与最大周非法，请在config.json重新设置order_week_beforeequal与order_week_afterequal')
            exit(0)
        curr_candidate = None # None represents NOT replacing
        if not (in_range and (hours_enough or replace_flag)):
            if not hours_enough and not replace_flag:
                logger.default_logger.log('学时不足，且已禁用换课。请到config.json内将enable.replace设为true，或空出足够学时。')
                exit(0)
            continue
        # Now we know in_range, either hours_enough, or replace enabled
        if not hours_enough:
            curr_candidate = candidate_course
        # Check if we could shift the course to an earlier time
        duplicate, newcandidate = course_duplicate(res, duplicate_flag)
        if not duplicate and newcandidate and replace_flag:
            logger.default_logger.log('已预约课程'+newcandidate.name+'存在更早的时间段，将作为被替代课程')
            curr_candidate = newcandidate
        if not hours_enough:
            earlier2cdd = curr_candidate and res.start_time<curr_candidate.start_time
            if replace_earlier and not earlier2cdd:
                # not earlier than candidate
                continue
        forbidden = res.name in course_forbidden
        favorite = len(course_favorite)==0 or res.name in course_favorite
        if not favorite:
            logger.default_logger.log('发现符合条件的可选课程:' +str(res.start_time)+' '+ res.name + '，但这门课不是想要的')
            continue
        contradict = time_conflict(res, curr_candidate)
        
        if duplicate:
            logger.default_logger.log('发现符合条件的可选课程:' +str(res.start_time)+' '+ res.name + '，但这门课已经上过/选过了')
            continue
        if contradict:
            logger.default_logger.log('发现符合条件的可选课程:' +str(res.start_time)+' '+ res.name + '，但这门课与已预约的课程时间冲突')
            continue
        if forbidden:
            logger.default_logger.log('发现符合条件的可选课程:' +str(res.start_time)+' '+ res.name + '，但这门课被禁选')
            continue
        logger.default_logger.log('发现符合条件的可选课程：'+str(res.start_time)+' '+ res.name)
        if smart_order(res.params, curr_candidate):
            logger.default_logger.log('选课成功！')
            if not loop_flag:
                exit(0)
        else:
            logger.default_logger.log('选课失败')
            if not loop_flag:
                exit(0)
        # update candidate. replace_candidate shouldn't be set.
        available_hours, candidate_course, hours_enough = check_study_hours(s)
    if verbose_mode:
        print('')

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


