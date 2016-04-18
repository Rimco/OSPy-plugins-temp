#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'
# This plugin read data from probe DHT11 (temp and humi). # Raspberry Pi pin 19 as GPIO 10

import json
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

import RPi.GPIO as GPIO

NAME = 'Air Temperature and Humidity Monitor'
LINK = 'settings_page'

plugin_options = PluginOptions(
    NAME,
    {'enabled': False,
     'enable_log': False,
     'log_interval': 1,
     'log_records': 0,
     'label': 'Air Probe'
     }
)


################################################################################
# Main function loop:                                                          #
################################################################################


class Sender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop = Event()

        self.status = {}
        self.status['temp'] = 0
        self.status['humi'] = 0

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
        Temperature = 0
        Humidity = 0    
        while not self._stop.is_set():
            log.clear(NAME)
            try:
                if plugin_options['enabled']:  # if plugin is enabled      
                    try:
                       Temperature, Humidity = DHT11_read_data()
                    except:
                       self._sleep(0.3)                                     
                      
                    if Humidity and Temperature != 0:
                       self.status['temp'] = Temperature
                       self.status['humi'] = Humidity
                       log.info(NAME, datetime_string())
                       log.info(NAME, 'Temperature: ' + u'%.1f \u2103' % Temperature)
                       log.info(NAME, 'Humidity: ' + u'%.1f' % Humidity + ' %RH')

                       if plugin_options['enable_log']:
                          update_log(self.status)

                       self._sleep(max(60, plugin_options['log_interval'] * 60))

            except Exception:
                log.error(NAME, 'Air Temperature and Humidity Monitor plug-in:\n' + traceback.format_exc())
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

def bin2dec(string_num):
    return str(int(string_num, 2))

def DHT11_read_data():
    data = []        
   
    GPIO.setup(19,GPIO.OUT) # pin 19 GPIO10
    GPIO.output(19,True)
    time.sleep(0.025)
    GPIO.output(19,False)
    time.sleep(0.02)
    GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for i in range(0,500):
       data.append(GPIO.input(19))
 
    bit_count = 0
    tmp = 0
    count = 0
    HumidityBit = ""
    TemperatureBit = ""
    crc = ""

    try:
        while data[count] == 1:
          tmp = 1
          count = count + 1

        for i in range(0, 32):
          bit_count = 0

          while data[count] == 0:
             tmp = 1
             count = count + 1
          
          while data[count] == 1:
             bit_count = bit_count + 1
             count = count + 1 

          if bit_count > 3:
             if i>=0 and i<8:
                HumidityBit = HumidityBit + "1"
             if i>=16 and i<24:
                TemperatureBit = TemperatureBit + "1"
          else:
             if i>=0 and i<8:
                HumidityBit = HumidityBit + "0"
             if i>=16 and i<24:
                TemperatureBit = TemperatureBit + "0"
   
        for i in range(0,8):
          bit_count = 0

          while data[count] == 0: 
              tmp = 1
              count = count + 1

          while data[count] == 1:
              bit_count = bit_count + 1
              count = count + 1

          if bit_count > 3:
              crc = crc + "1"
          else:
              crc = crc + "0"

          Humidity = bin2dec(HumidityBit)
          Temperature = bin2dec(TemperatureBit)

          if int(Humidity) + int(Temperature) - int(bin2dec(crc)) == 0:
             return int(Temperature),int(Humidity)              
    except:
       time.sleep(0.5)
            

   
def read_log():
    """Read log from json file."""
    try:
        with open(os.path.join(plugin_data_dir(), 'log.json')) as logf:
            return json.load(logf)
    except IOError:
        return []


def write_log(json_data):
    """Write json to log file."""
    with open(os.path.join(plugin_data_dir(), 'log.json'), 'w') as outfile:
        json.dump(json_data, outfile)


def update_log(status):
    log_data = read_log()
    data = {'datetime': datetime_string()}
    data['temp'] = str(status['temp'])
    data['humi'] = str(status['humi'])
    log_data.insert(0, data)
    if plugin_options['log_records'] > 0:
        log_data = log_data[:plugin_options['log_records']]
    write_log(log_data)


################################################################################
# Web pages:                                                                   #
################################################################################

class settings_page(ProtectedPage):
    """Load an html page for entering adjustments."""

    def GET(self):
        return self.plugin_render.air_temp_humi(plugin_options, log.events(NAME))

    def POST(self):
        plugin_options.web_update(web.input())

        if sender is not None:
            sender.update()                
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(plugin_options)


class log_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(read_log())


class log_csv(ProtectedPage):  # save log file from web as csv file type
    """Simple Log API"""

    def GET(self):
        log_records = read_log()
        data = "Date/Time"
        data += ";\t Temperature C"
        data += ";\t Humidity %RH" 
        data += '\n'

        for record in log_records:
            data += record['datetime']
            data += ";\t" + record["temp"]
            data += ";\t" + record["humi"]
            data += '\n'

        web.header('Content-Type', 'text/csv')
        return data


class delete_log_page(ProtectedPage):  # delete log file from web
    """Delete all log_records"""

    def GET(self):
        write_log([])
        log.info(NAME, 'Deleted log file')
        raise web.seeother(plugin_url(settings_page), True)


