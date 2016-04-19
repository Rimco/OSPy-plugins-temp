# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'
# This plugin use library rtc_DS1307


import subprocess

import datetime
import time, struct
import sys, os

import rtc_DS1307

from threading import Thread, Event
import socket
from socket import AF_INET, SOCK_DGRAM
import traceback
import json

import web
from ospy.log import log
from ospy.options import options
from ospy.webpages import ProtectedPage
from ospy.helpers import datetime_string
from plugins import PluginOptions, plugin_url

NAME = 'Real Time and NTP time'
LINK = 'settings_page'

plugin_options = PluginOptions(
    NAME,
    {
        'enabled': False,
        'use_ntp': True,
        'ntp_server': '195.113.144.201', # tik.cesnet.cz
        'ntp_port': 123                  # 123 default 
    })


################################################################################
# Main function loop:                                                          #
################################################################################
class RealTimeChecker(Thread):
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
        dis_text = True
        while not self._stop.is_set():
            rtc_time = None
            ntp_time = None  

            try:
                log.clear(NAME)
                if plugin_options['enabled']:
                    dis_text = True
                    log.info(NAME, 'Local time: ' + datetime_string())
                    try:                                                                 # try use library rtc_DS1307
                       ds1307 = rtc_DS1307.rtc_DS1307(1)

                    except:
                       log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())

                    if plugin_options['use_ntp']:
                       try:
                           ntp_time = getNTPtime()                                       # try read NTP time from web

                       except:
                           log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())

                       log.info(NAME, 'NTP time ' + str(plugin_options['ntp_server']) + ': ' + str(ntp_time))
              
                    try:
                       rtc_time = ds1307.read_datetime()                                 # try read RTC time from DS1307
                       log.info(NAME, 'RTC time: ' + str(rtc_time))

                    except:
                       log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())
                    

                    if ntp_time is not None and rtc_time is not None and ntp_time != rtc_time:   # try save NTP time to RTC DS1307 if NTP!=RTC
                       try:
                          log.info(NAME, 'Saving NTP time to RTC time.')                 
                          ds1307.write_datetime(getNTPtime())
                          rtc_time = ds1307.read_datetime()                                 
                          log.info(NAME, 'RTC time is now: ' + str(rtc_time))

                       except:
                          log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())

                    if ntp_time is not None and ntp_time != datetime_string():           # try sync local time from NTP time if NTP!=local time
                       try:
                          log.info(NAME, 'Saving NTP time to local system time.')                                       
                          subprocess.call("sudo date -s '{:}'".format(ntp_time.strftime('%Y/%m/%d %H:%M:%S')), shell=True) # Sets system time (Requires root, obviously)
                          
                       except:
                          log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())
                    else:                                                                 # try sync local time from RTC time
                       try: 
                          if rtc_time is not None: 
                             log.info(NAME, 'Read RTC time and save to local system time.') 
                             # example for set time:
                             # date -s hh:mm:ss
                             # date 021415232015 (Sun Feb 14 15:23:31 PST 2015)
                             # date --set='20150125 09:17:00'
                                            
                             set_time = rtc_time.strftime('"%Y%m%d ') + rtc_time.strftime('%H:%M:%S"')
                             os.system('sudo date --set=' + set_time)  

                       except:
                          log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())                         

                    self._sleep(3600)

                else:
                    if dis_text:
                        log.clear(NAME)
                        log.info(NAME, 'Plug-in is disabled.')
                        dis_text = False

            except Exception:
                log.error(NAME, 'Real Time plug-in:\n' + traceback.format_exc())
                self._sleep(60)


checker = None


################################################################################
# Helper functions:                                                            #
################################################################################

def getNTPtime():
    """Return NTP time as datetime"""
    buf = 1024
    port = int(plugin_options['ntp_port'])
    host = plugin_options['ntp_server']

    address = (host,port)
    msg = '\x1b' + 47 * '\0'

    # reference time (in seconds since 1900-01-01 00:00:00)
    TIME1970 = 2208988800L # 1970-01-01 00:00:00

    # connect to server
    client = socket.socket( AF_INET, SOCK_DGRAM)
    client.sendto(msg, address)
    msg, address = client.recvfrom( buf )

    t = struct.unpack( "!12I", msg )[10]
    t -= TIME1970
    try:
        t = datetime.datetime.strptime(time.ctime(t), "%a %b %d %H:%M:%S %Y")
        return t
    except Exception:    
        return None
    
    
    
def start():
    global checker
    if checker is None:
        checker = RealTimeChecker()


def stop():
    global checker
    if checker is not None:
        checker.stop()
        checker.join()
        checker = None
    
################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for entering real time adjustments"""

    def GET(self):
        return self.plugin_render.real_time(plugin_options, log.events(NAME))

    def POST(self):
        plugin_options.web_update(web.input())
        if checker is not None:
            checker.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format"""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(plugin_options)
