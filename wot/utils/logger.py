from __future__ import print_function
import traceback

def print_trace(enable=True):
    ConsoleLogger().set_trace(enable)

def set_log_level(log_level):
    ConsoleLogger().set_level(log_level)
    if log_level == 'debug':
        print_trace(True)

def debug(msg):
    ConsoleLogger().debug("[DEBUG] {}".format(msg))

def warn(msg):
    ConsoleLogger().warn("[WARN] {}".format(msg))

def error(msg):
    ConsoleLogger().error("[ERROR] {}".format(msg))

def log(msg):
    ConsoleLogger().log("[LOG] {}".format(msg))


class Singleton(object):
    _instances = {}
    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
        return class_._instances[class_]

class ConsoleLogger(Singleton):

    def __init__(self):
        # initialize first time only 
        if hasattr(self, 'cur_level') is False:
            self.cur_level = 'warn'
            self.levels = ['debug', 'warn', 'error', 'log']
            self.trace = False

    def set_level(self, log_level):
        if log_level.lower() in self.levels:
            self.cur_level = log_level.lower()

    def set_trace(self, trace):
        self.trace = trace

    def debug(self, msg):
        if self.levels.index(self.cur_level) <= self.levels.index('debug'):
            print(msg)

    def warn(self, msg):
        if self.levels.index(self.cur_level) <= self.levels.index('warn'):
            print(msg)
        if self.trace:
            traceback.print_exc()

    def error(self, msg):
        if self.levels.index(self.cur_level) <= self.levels.index('error'):
            print(msg)
        if self.trace:
            traceback.print_stack()        

    def log(self, msg):
        print(msg)



