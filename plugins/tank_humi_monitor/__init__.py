#!/usr/bin/env python
# this plugins check humidity and water level in tank via ultrasonic sensor
__author__ = 'Martin Pihrt'

import json
import time
import datetime
import sys
import traceback

from threading import Thread, Event

import smbus
import web
from ospy.options import level_adjustments
from ospy.stations import stations
from ospy.options import options
from ospy.log import log
from plugins import PluginOptions, plugin_url
from ospy.webpages import ProtectedPage
from ospy.helpers import datetime_string


NAME = 'Water Tank and Humidity Monitor'
LINK = 'settings_page'

tank_options = PluginOptions(
    NAME,
    {
       "use_sonic": True,      # default use sonic sensor
       "distance_bottom": 33,  # default 33 cm sensor <-> bottom tank
       "distance_top": 2,      # default 2 cm sensor <-> top tank
       "water_minimum": 6,     # default 6 cm water level <-> bottom tank
       "use_send_email": True, # default send email
       "use_freq_1": False,    # default not use freq sensor 1
       "use_freq_2": False,    # default not use freq sensor 2
       "use_freq_3": False,    # default not use freq sensor 3
       "use_freq_4": False,    # default not use freq sensor 4
       "use_freq_5": False,    # default not use freq sensor 5
       "use_freq_6": False,    # default not use freq sensor 6
       "use_freq_7": False,    # default not use freq sensor 7
       "use_freq_8": False,    # default not use freq sensor 8
       "minimum_freq": 400000, # default freq from sensor for 0% humi
       "maximum_freq": 100000  # default freq from sensor for 100% humi	
    }
)

bus = smbus.SMBus(1)# Raspberry Pi I2C bus 0 for old RPi, 1 for new RPi
address_ping = 0x04 # device address for sonic ping HW board
address_humi = 0x05 # device address for humidity HW board

################################################################################
# Main function loop:                                                          #
################################################################################

class Sender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop = Event()

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
        once_text = True
        two_text = True
        send = False
        mini = True
        last_level = 0
        
        while not self._stop.is_set():
            try:
                if tank_options['use_sonic']: 
                    if two_text:
                        log.clear(NAME)
                        log.info(NAME, 'Water tank monitor is enabled.')
                        once_text = True
                        two_text = False

                    level_in_tank = get_sonic_tank_cm()

                    if level_in_tank != last_level: # only if level is changed
                        last_level = level_in_tank
                        if level_in_tank == -1:
                            log.info(NAME, datetime_string() + ' Water level sensor is faulty!')
                        else:
                            log.info(NAME, datetime_string() + ' Water level: ' + str(level_in_tank) + ' cm.')

                    if level_in_tank <= int(tank_options['water_minimum']) and mini and not options.manual_mode and level_in_tank > -1:
                        
                        if tank_options['use_send_email']: 
                            send = True
                            mini = False 
    
                        log.info(NAME, datetime_string() + ' ERROR: Water in Tank < ' + str(tank_options['water_minimum']) + ' cm! ')
                        options.scheduler_enabled = False                  # disable scheduler
                        log.finish_run(None)                               # save log
                        stations.clear()                                   # set all station to off  
                                          

                    if level_in_tank > int(tank_options['water_minimum']) + 5 and not mini: 
                        mini = True
                
                else:
                    if once_text:
                       log.info(NAME, 'Water tank monitor is disabled.')
                       once_text = False
                       two_text = True
                       last_level = 0

                       
                if tank_options['use_freq_1']:
                    print get_freq(1), get_freq(2), get_freq(3), get_freq(4), get_freq(5), get_freq(6), get_freq(7), get_freq(8)

                if send:
                    TEXT = (datetime_string() + '\nSystem detected error: Water Tank has minimum Water Level: ' + str(tank_options['water_minimum']) + 'cm.\nScheduler is now disabled and all Stations turn Off.')
                    try:
                        from plugins.email_notifications import email
                        email(TEXT)
                        log.info(NAME, 'Email was sent: ' + TEXT)
                        send = False
                    except Exception as err:
                        log.error(NAME, 'Email was not sent! ' + str(err))

                self._sleep(10)

            except Exception:
                log.error(NAME, 'Water tank and humidity Monitor plug-in:\n' + traceback.format_exc())
                self._sleep(60)


sender = None

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global sender
    if sender is None:
        sender = Sender()

def stop():
    global sender
    if sender is not None:
        sender.stop()
        sender.join()
        sender = None
        if NAME in level_adjustments:
           del level_adjustments[NAME]

def get_sonic_cm():
    try:
        data = [2]
        data = bus.read_i2c_block_data(address_ping,2)
        cm = data[1] + data[2]*255
        return cm
    except:
        return -1   

def get_sonic_tank_cm():
    try:
        cm = get_sonic_cm()
        tank_cm = maping(cm,int(tank_options['distance_bottom']),int(tank_options['distance_top']),int(tank_options['distance_top']),int(tank_options['distance_bottom']))
        if tank_cm > 0:
           return tank_cm
        else:
           return 0
    except:
        return -1

def get_freq(freq_no):
    try:
        data = [24]
        data = bus.read_i2c_block_data(address_humi,24)
        if freq_no == 1:
           f = data[3]<<16 + data[2]<<8 + data[1]    # freq 1
           print  data[8], data[7], data[6]
        elif freq_no == 2:
           f = data[6]<<16 + data[5]<<8 + data[4]    # freq 2
        elif freq_no == 3:
           f = data[9]<<16 + data[8]<<8 + data[7]  # freq 3
        elif freq_no == 4:
           f = data[12]<<16 + data[11]<<8 + data[10] # freq 4
        elif freq_no == 5:
           f = data[15]<<16 + data[14]<<8 + data[13] # freq 5
        elif freq_no == 6:
           f = data[18]<<16 + data[17]<<8 + data[16] # freq 6
        elif freq_no == 7:
           f = data[21]<<16 + data[20]<<8 + data[19] # freq 7
        elif freq_no == 8:
           f = data[24]<<16 + data[23]<<8 + data[22] # freq 8
        else:
           f = -2
        return f

    except:
        return -1           

def maping(x, in_min, in_max, out_min, out_max):
    # return value from map. example (x=1023,0,1023,0,100) -> x=1023 return 100
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
 
def get_station_is_on():
        for station in stations.get():
            if station.active:                                              
                return True
            else:
                return False

################################################################################
# Web pages:                                                                   #
################################################################################


class settings_page(ProtectedPage):
    """Load an html page for entering adjustments."""

    def GET(self):
        return self.plugin_render.tank_humi_monitor(tank_options, log.events(NAME))

    def POST(self):
        tank_options.web_update(web.input())

        if sender is not None:
            sender.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(tank_options)

