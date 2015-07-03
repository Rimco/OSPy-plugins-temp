#!/usr/bin/env python
# This plugin controls OpenSprinkler via 8 buttons. I2C controller MCP23017. 

import time
import traceback
import os
from threading import Thread, Event

import web

from ospy.log import log
from plugins import PluginOptions, plugin_url, plugin_data_dir
from ospy.webpages import ProtectedPage
from ospy.helpers import get_rpi_revision
from ospy.helpers import datetime_string


NAME = 'Button Control'
LINK = 'settings_page'

plugin_options = PluginOptions(
    NAME,
    {'use_button': False,
     'button1': 'reboot',
     'button2': 'restart',
     'button3': 'power',
     'button4': 'manual',
     'button5': 'stop',
     'button6': 'p1',
     'button7': 'p2',
     'button8': 'p3'
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################
