#!/usr/bin/env python
# this plugins check pressure in pipe if master station is switched on

import json
import time
import sys
import traceback

from threading import Thread, Event

import web
from ospy.stations import stations
from ospy.options import options
from ospy.log import log
from plugins import PluginOptions, plugin_url
from ospy.webpages import ProtectedPage
from ospy.helpers import datetime_string

NAME = 'Pressure Monitor'
LINK = 'settings_page'

pressure_options = PluginOptions(
    NAME,
    {
        "time": 10,
        "use_press_monitor": False,
        "normally": False,
        "sendeml": True
    }
)

################################################################################
# GPIO input pullup:                                                           #
################################################################################

import RPi.GPIO as GPIO  # RPi hardware

pin_pressure = 12

try:
    GPIO.setup(pin_pressure, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except NameError:
    pass


################################################################################
# Main function loop:                                                          #
################################################################################

class PressureSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop_event = Event()

        self._sleep_time = 0
        self.start()

    def stop(self):
        self._stop_event.set()

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop_event.is_set():
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        send = False

        once_text = True
        two_text = True
        three_text = True
        four_text = True
        five_text = True

        last_time = int(time.time())
        actual_time = int(time.time())

        while not self._stop_event.is_set():
            try:
                if pressure_options['use_press_monitor']:                           # if pressure plugin is enabled
                    four_text = True
                    if get_master_is_on():                                           # if master station is on
                        three_text = True
                        if once_text:                               # text on the web if master is on
                            log.clear(NAME)
                            log.info(NAME, 'Master station is ON.')
                            once_text = False
                        if get_check_pressure():                                     # if pressure sensor is on
                            actual_time = int(time.time())
                            count_val = int(pressure_options['time'])
                            log.clear(NAME)
                            log.info(NAME, 'Time to test pressure sensor: ' + str(
                                count_val - (actual_time - last_time)) + ' sec')
                            if actual_time - last_time > int(
                                    pressure_options['time']): # wait for activated pressure sensor (time delay)
                                last_time = actual_time
                                if get_check_pressure():                              # if pressure sensor is actual on
                                #  options.scheduler_enabled = False                  # set scheduler to off
                                    log.finish_run(None)                               # save log
                                    stations.clear()                                   # set all station to off
                                    log.clear(NAME)
                                    log.info(NAME,
                                             'Pressure sensor is not activated in time -> stops all stations and send email.')
                                    if pressure_options['sendeml']:                    # if enabled send email
                                        send = True

                        if not get_check_pressure():
                            last_time = int(time.time())
                            if five_text:
                                once_text = True
                                five_text = False

                    if not get_master_is_on():                                    # text on the web if master is off
                        if stations.master is not None:
                            if two_text:
                                log.clear(NAME)
                                log.info(NAME, 'Master station is OFF.')
                                two_text = False
                                five_text = True
                            last_time = int(time.time())

                else:
                    once_text = True
                    two_text = True
                    if four_text:                                                # text on the web if plugin is disabled
                        log.clear(NAME)
                        log.info(NAME, 'Pressure monitor plug-in is disabled.')
                        four_text = False

                if stations.master is None:                                      # text on the web if master station is none
                    if three_text:
                        log.clear(NAME)
                        log.info(NAME, 'Not used master station.')
                        three_text = False

                if send:
                    TEXT = (datetime_string() + ': System detected error: pressure sensor.')
                    try:
                        from plugins.email_notifications import email
                        email(TEXT)                                     # send email without attachments
                        log.info(NAME, 'Email was sent: ' + TEXT)
                        send = False
                    except Exception as err:
                        log.error(NAME, 'Email was not sent! ' + str(err))

                self._sleep(1)

            except Exception:
                log.error(NAME, 'Pressure monitor plug-in:\n' + traceback.format_exc())
                self._sleep(60)


pressure_sender = None

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global pressure_sender
    if pressure_sender is None:
        pressure_sender = PressureSender()


def stop():
    global pressure_sender
    if pressure_sender is not None:
        pressure_sender.stop()
        pressure_sender.join()
        pressure_sender = None


def get_check_pressure():
    try:
        if pressure_options['normally']:
            if GPIO.input(pin_pressure):  # pressure detected
                press = 1
            else:
                press = 0
        elif pressure_options['normally'] != 'on':
            if not GPIO.input(pin_pressure):
                press = 1
            else:
                press = 0
        return press
    except NameError:
        pass


def get_master_is_on():
    if stations.master is not None and not options.manual_mode:              # if is use master station and not manual control
        for station in stations.get():
            if station.is_master:                                              # if station is master
                if station.active:                                              # if master is active
                    return True
                else:
                    return False

################################################################################
# Web pages:                                                                   #
################################################################################


class settings_page(ProtectedPage):
    """Load an html page for entering pressure adjustments."""

    def GET(self):
        return self.plugin_render.pressure_monitor(pressure_options, log.events(NAME))

    def POST(self):
        pressure_options.web_update(web.input())

        if pressure_sender is not None:
            pressure_sender.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(pressure_options)

