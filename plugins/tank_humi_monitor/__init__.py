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

options = PluginOptions(
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

bus = smbus.SMBus(1)
address = 0x04 # device address for humi and ping plugin HW board

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
        send = False
        mini = True
	   
        while not self._stop.is_set():
            try:
                if options['use_sonic']: 
                    log.clear(NAME)
                    #print get_sonic_cm(), get_sonic_tank_cm() #test

                    level_in_tank = get_sonic_tank_cm()
                    log.info(NAME, 'Water in Tank: ' + str(level_in_tank) + ' cm.')

                    if level_in_tank <= int(options['water_minimum']) and mini: 
                        log.clear(NAME)
                        if options['use_send_email']: 
                            send = True
                        mini = False                                       # run once 1x if level is small (for send email, disable scheduler....)
                        log.info(NAME, 'ERROR: Water in Tank < ' + str(options['water_minimum']) + ' cm! ')
                        log.finish_run(None)                               # save log
                        stations.clear()                                   # set all station to off
                        # todo options disabled scheduler                                                

                    if level_in_tank > int(options['water_minimum']) + 5 and not mini: 
                        mini = True
                        

                if send:
                    TEXT = (datetime_string() + '\nSystem detected error: Water Tank has minimum Water Level: ' + str(options['water_minimum']) + 'cm.\nScheduler is now disabled and all Stations turn Off.')
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
        data = bus.read_i2c_block_data(address,2)
        cm = data[1] + data[2]*255
        return cm
    except:
        return -1   

def get_sonic_tank_cm():
    try:
        cm = get_sonic_cm()
        tank_cm = maping(cm,int(options['distance_bottom']),int(options['distance_top']),int(options['distance_top']),int(options['distance_bottom']))
        if tank_cm > 0:
           return tank_cm
        else:
           return 0
    except:
        return -1

def get_freq(freq_no):
    try:
        data = [26]
        data = bus.read_i2c_block_data(address,26)
        if freq_no == 1:
           f = data[5]<<16 + data[4]<<8 + data[3]    # freq 1
        elif freq_no == 2:
           f = data[8]<<16 + data[7]<<8 + data[6]    # freq 2
        elif freq_no == 3:
           f = data[11]<<16 + data[10]<<8 + data[9]  # freq 3
        elif freq_no == 4:
           f = data[14]<<16 + data[13]<<8 + data[12] # freq 4
        elif freq_no == 5:
           f = data[17]<<16 + data[16]<<8 + data[15] # freq 5
        elif freq_no == 6:
           f = data[20]<<16 + data[19]<<8 + data[18] # freq 6
        elif freq_no == 7:
           f = data[23]<<16 + data[22]<<8 + data[21] # freq 7
        elif freq_no == 8:
           f = data[26]<<16 + data[25]<<8 + data[24] # freq 8
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
        return self.plugin_render.tank_humi_monitor(options, log.events(NAME))

    def POST(self):
        options.web_update(web.input())

        if sender is not None:
            sender.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(options)

