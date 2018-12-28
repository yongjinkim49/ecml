from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

import argparse

import commons.hp_cfg as hconf
from commons.logger import * 

from interface import create_name_server


HP_CONF_PATH = './hp_conf/'
ALL_LOG_LEVELS = ['debug', 'warn', 'error', 'log']

