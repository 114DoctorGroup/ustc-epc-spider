import datetime
import os

def log(msg:str):
    pass

class Logger:
    def __init__(self, path:str):
        self.path = path
        self.file = open(path,'a+', 1, 'UTF-8') # use line buffering
    def log(self, msg: str, stdprint = True):
        s = str(datetime.datetime.now()) + ' ' + msg
        self.file.write(s+'\n')
        if stdprint:
            print(str(datetime.datetime.now()), end=' ')
            print(msg)

log_path = 'Logs'
if not os.path.exists(log_path):
    os.mkdir(log_path)
now = datetime.datetime.now()
default_logger = Logger(log_path + '/' + str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'.log')