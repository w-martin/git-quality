import glob
import logging
import os
from configparser import ConfigParser

try:
    CONFIG_INI = os.path.abspath(glob.glob('quality_config.ini')[0])
except:
    # try default path
    CONFIG_INI = '/opt/git-quality/quality_config.ini'


def read_config(section):
    parser = ConfigParser()
    parser.read(CONFIG_INI)
    config_params = {param[0]: param[1] for param in parser.items(section)}
    logging.debug("Loaded %d parameters for section %s", len(config_params), section)
    return config_params
