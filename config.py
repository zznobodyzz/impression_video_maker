import collections
from utils import *

class CfgNotFound(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        print("config name: %s not found in cfg file" %(self.name))

class CfgDecoder():
    def __init__(self):
        self.default_config_file = './config.ini'
        self.config = collections.OrderedDict()
        f = open(self.default_config_file, "r", encoding='utf8')
        lines = f.readlines()
        status = 0
        seg = ""
        for line in lines:
            if line[0] == "#":
                continue
            if "#" in line:
                line = line[:line.index("#")]
            line = line.rstrip().lstrip()
            if status == 0:
                if line[0] == "[" and line[-1] == "]":
                    seg = line[1:-1]
                    if seg == "":
                        continue
                    self.config[seg] = collections.OrderedDict()
                    status = 1
            else:
                if "=" in line:
                    if line.count("=") == 1:
                        [key, value] = line.split("=")
                        self.config[seg][key.rstrip()] = value.lstrip()
                        continue
                if line == "":
                    status = 0
                
    def get_cfg(self, config_section, config_name):
        if config_section not in self.config.keys():
            raise CfgNotFound(config_section)
        if config_name not in self.config[config_section].keys():
            raise CfgNotFound(config_name)
        config_value = self.config[config_section][config_name]
        if config_value[0] == "(" and config_value[-1] == ")":
            #tuple
            return tuple((param.lstrip().rstrip() if param.lstrip().rstrip().isdigit() == False else int(param.lstrip().rstrip()))for param in config_value[1:-1].split(","))
        elif config_value.isdigit() == True:
            #digit
            return int(config_value)
        elif len(config_value.split(".")) == 2 and len(set([param.isdigit() for param in config_value.split(".")])) == 1 and \
            list(set([param.isdigit() for param in config_value.split(".")]))[0] == True:
            #float
            return float(config_value)
        elif config_value == "None":
            #None
            return None
        else:
            return config_value
            