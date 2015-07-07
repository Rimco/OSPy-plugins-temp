#!/usr/bin/env python
# This plugin controls OpenSprinkler via 8 buttons. I2C controller MCP23017 on 0x27 address. 

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

class PluginSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop = Event()
        
        self.bus = None
        
        self._sleep_time = 0
        self.start()

    def stop(self):
        self._stop.set()

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop.is_set():
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        try:
            import smbus  
            self.bus = smbus.SMBus(1 if get_rpi_revision() >= 2 else 0)
        except ImportError:
            log.warning(NAME, 'Could not import smbus.')
        
        log.clear(NAME)    
        while not self._stop.is_set():
            try:
                if plugin_options['use_button']:  # if button plugin is enabled
                    self._sleep(1)

            except Exception:
                log.clear(NAME)
                log.error(NAME, 'Button plug-in:\n' + traceback.format_exc())
                self._sleep(60)
                

plugin_sender = None

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global plugin_sender
    if plugin_sender is None:
        plugin_sender = PluginSender()


def stop():
    global plugin_sender
    if plugin_sender is not None:
        plugin_sender.stop()
        plugin_sender.join()
        plugin_sender = None
        
def read_buttons():
    try:
        DEVICE = 0x27 # Device address (A0,A1,A2 to vcc)
        IODIRA = 0x00 # Pin direction register A
        GPIOA  = 0x12 # Register for port input
        # Set 8 GPA pins as input_pullUP
        bus.write_byte_data(DEVICE,IODIRA,0xFF)
        # Read state of GPIOA register
        MySwitch = bus.read_byte_data(DEVICE,GPIOA)
        button_number = 0
        if MySwitch == 0b10000000:
            button_number = 128
            log.debug(NAME, 'Switch 8 pressed')
        if MySwitch == 0b010000000:
            button_number = button_number + 64
            log.debug(NAME, 'Switch 7 pressed')    
        if MySwitch == 0b00100000:
            button_number = button_number + 32
            log.debug(NAME, 'Switch 6 pressed')
        if MySwitch == 0b00010000:
            button_number = button_number + 16
            log.debug(NAME, 'Switch 5 pressed')    
        if MySwitch == 0b00001000:
            button_number = button_number + 8
            log.debug(NAME, 'Switch 4 pressed')    
        if MySwitch == 0b00000100:
            button_number = button_number + 4
            log.debug(NAME, 'Switch 3 pressed')    
        if MySwitch == 0b00000010:
            button_number = button_number + 2
            log.debug(NAME, 'Switch 2 pressed')    
        if MySwitch == 0b00000001:
            button_number = button_number + 1
            log.debug(NAME, 'Switch 1 pressed')    
        return button_number 
        self._sleep(1)
    except:
        log.error(NAME, 'Button plug-in:\n' + 'Read button - FAULT')
        return 0

def led_outputs():
    try:
        DEVICE = 0x27 # Device address (A0,A1,A2 to vcc)
        IODIRB = 0x01 # Pin direction register B
        OLATA  = 0x14 # Register for outputs
        # Set all GPB pins as outputs by setting
        # all bits of IODIRB register to 0
        bus.write_byte_data(DEVICE,IODIRB,0x00)
        # Set output all 8 output bits to 0
        # bus.write_byte_data(DEVICE,OLATA,0)
        # example (DEVICE,IODIRB, from 001 to 111) out 1 to 8
    except:
        log.error(NAME, 'Button plug-in:\n' + 'Set LED - FAULT')
        

################################################################################
# Web pages:                                                                   #
################################################################################

class settings_page(ProtectedPage):
    """Load an html page for entering plugin settings."""

    def GET(self):
        return self.plugin_render.button_control(plugin_options, log.events(NAME))

    def POST(self):
        plugin_options.web_update(web.input())

        if plugin_sender is not None:
            plugin_sender.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(plugin_options)        
