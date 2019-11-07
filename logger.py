import datetime
import os

def log(msg:str):
    pass

class Logger:
    def __init__(self, path:str, log_if_diff:bool=False):
        self.path = path
        self.file = open(path,'a+', 1, 'UTF-8') # use line buffering
        self.prev_msg = None
        self.log_if_diff = log_if_diff
    def log(self, msg: str, stdprint = True):
        if self.log_if_diff:
            if msg == self.prev_msg:
                return
        s = str(datetime.datetime.now()) + ' ' + msg
        self.file.write(s+'\n')
        if stdprint:
            print(str(datetime.datetime.now()), end=' ')
            print(msg)
        self.prev_msg = msg

log_path = 'Logs'
if not os.path.exists(log_path):
    os.mkdir(log_path)
now = datetime.datetime.now()
default_logger = Logger(log_path + '/' + str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'.log')