import datetime

class Log():
    def __init__(self, log_level = 255, log_file = None):
        self.LOG_LEVEL = log_level
        self.LOG_FILE = log_file
        
    def log(self, main_string, sub_string, level = 5):
        time_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        if self.LOG_LEVEL == 255:
            print("[%s] [%s] %s\n" %(time_str, main_string, sub_string))
        elif level < self.LOG_LEVEL and self.LOG_FILE != None:
            self.LOG_FILE.write()
            self.LOG_FILE.flush()

            
    def log_set(self, log_set_level):
        self.LOG_FILE = open("./log.txt", "a")
        if self.LOG_FILE != None:
            self.LOG_LEVEL = log_set_level
        return