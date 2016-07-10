
#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'
# This plugin sends data to I2C for LCD 16x2 or 16x1 char with PCF8574.
# Visit for more: www.pihrt.com/elektronika/258-moje-rapsberry-pi-i2c-lcd-16x2.
# This plugin requires python pylcd2.py library


import json
import time
import traceback
from datetime import datetime

from threading import Thread, Event

import web
from ospy import helpers
from ospy import version
from ospy.inputs import inputs
from ospy.options import options
from ospy.log import log
from plugins import PluginOptions, plugin_url
from ospy.webpages import ProtectedPage
from ospy.helpers import ASCI_convert

import i18n

NAME = 'LCD Display'
LINK = 'settings_page'

lcd_options = PluginOptions(
    NAME,
    {
        "use_lcd": True,
        "two_lines": True,
        "debug_line": False,
        "address": 0
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################
class LCDSender(Thread):
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
        report_index = 0
        while not self._stop.is_set():
            try:
                if lcd_options['use_lcd']:  # if LCD plugin is enabled
                    if lcd_options['debug_line']:
                        log.clear(NAME)
                    line1 = get_report(report_index)
                    line2 = get_report(report_index + 1)

                    if line1 is None:
                        report_index = 0
                        line1 = get_report(report_index)
                        line2 = get_report(report_index + 1)

                    update_lcd(line1, line2)
                    
                    if lcd_options['debug_line']:
                        log.info(NAME, line1)
                    if lcd_options['two_lines']:
                        if lcd_options['debug_line']:
                            log.info(NAME, line2)
                        report_index += 2
                    else:
                        report_index += 1
                self._sleep(4)

            except Exception:
                log.error(NAME, _('LCD display plug-in:\n') + traceback.format_exc())
                self._sleep(60)


lcd_sender = None


class DummyLCD(object):
    def __init__(self):
        self._lines = (' ' * 17) + '/' + (' ' * 17)

    lcd_clear = __init__

    def lcd_puts(self, text, line):
        text = text[:16]
        if line == 1:
            self._lines = text + self._lines[len(text):]
        elif line == 2:
            self._lines = self._lines[:20] + text + self._lines[20 + len(text):]
        #log.debug('LCD', self._lines)


dummy_lcd = DummyLCD()

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global lcd_sender
    if lcd_sender is None:
        lcd_sender = LCDSender()


def stop():
    global lcd_sender
    if lcd_sender is not None:
        lcd_sender.stop()
        lcd_sender.join()
        lcd_sender = None


def get_report(index):
    result = None
    if (options.lang == 'cs_CZ'):
        if index == 0:  # start text to 16x1
             result = "ID systemu:"
        elif index == 1:
             result = options.name
        elif index == 2:
             result = "Verze OSPy:"
        elif index == 3:
             result = version.ver_date
        elif index == 4:
             result = "IP adresa:"
        elif index == 5:
             ip = helpers.get_ip()
             result = str(ip)
        elif index == 6:
             result = "Port:"
        elif index == 7:
             result = str(options.web_port)
        elif index == 8:
             result = "Teplota CPU:"
        elif index == 9:
             result = helpers.get_cpu_temp(options.temp_unit) + ' ' + options.temp_unit
        elif index == 10:
             result = datetime.now().strftime('Dat %d-%m-%Y')
        elif index == 11:
             result = datetime.now().strftime('Cas %H:%M:%S')
        elif index == 12:
             result = "V provozu:"
        elif index == 13:
             result = helpers.uptime()
        elif index == 14:
             result = "Cidlo deste:"
        elif index == 15:
             if inputs.rain_sensed():
                 result = "aktivni"
             else:
                 result = "neaktivni"
        elif index == 16:
            result = 'Naposledy bezel'
        elif index == 17:
            finished = [run for run in log.finished_runs() if not run['blocked']]
            if finished:
                result = finished[-1]['start'].strftime('%d-%m-%Y v %H:%M:%S program: ') + finished[-1]['program_name']
            else:
                result = 'zadny program'
        elif index == 18:
            result = "Cidlo tlaku:"
        elif index == 19:
            try:
                from plugins import pressure_monitor
                state_press = pressure_monitor.get_check_pressure()
                if state_press:
                    result = "neaktivni"
                else:
                    result = "aktivni"

            except Exception:
                result = "neni k dispozici"
        elif index == 20:        
            result = "Nadrz s vodou:"
        elif index == 21:
            try:
                from plugins import tank_humi_monitor
                cm = tank_humi_monitor.get_sonic_tank_cm()
                if cm > 0: 
                    result = str(cm) + ' cm'
                else:
                    result = "chyba - I2C zarizeni nenalezeno!"

            except Exception:
                result = "neni k dispozici"

        return ASCI_convert(result)


    if (options.lang == 'en_US') or (options.lang == 'default'):
        if index == 0:  # start text to 16x1
             result = options.name
        elif index == 1:
             result = "Irrigation system"
        elif index == 2:
             result = "OSPy version:"
        elif index == 3:
             result = version.ver_date
        elif index == 4:
             result = "My IP is:"
        elif index == 5:
             ip = helpers.get_ip()
             result = str(ip)
        elif index == 6:
             result = "My port is:"
        elif index == 7:
             result = str(options.web_port)
        elif index == 8:
             result = "CPU temperature:"
        elif index == 9:
             result = helpers.get_cpu_temp(options.temp_unit) + ' ' + options.temp_unit
        elif index == 10:
             result = datetime.now().strftime('Date: %d.%m.%Y')
        elif index == 11:
             result = datetime.now().strftime('Time: %H:%M:%S')
        elif index == 12:
             result = "System uptime:"
        elif index == 13:
             result = helpers.uptime()
        elif index == 14:
             result = "Rain sensor:"
        elif index == 15:
             if inputs.rain_sensed():
                 result = "Active"
             else:
                 result = "Inactive"
        elif index == 16:
            result = 'Last program:'
        elif index == 17:
            finished = [run for run in log.finished_runs() if not run['blocked']]
            if finished:
                result = finished[-1]['start'].strftime('%H:%M: ') + finished[-1]['program_name']
            else:
                result = 'None'
        elif index == 18:
            result = "Pressure sensor:"
        elif index == 19:
            try:
                from plugins import pressure_monitor
                state_press = pressure_monitor.get_check_pressure()
                if state_press:
                    result = "GPIO is HIGH"
                else:
                    result = "GPIO is LOW"

            except Exception:
                result = "Not available"
        elif index == 20:        
            result = "Water Tank Level:"
        elif index == 21:
            try:
                from plugins import tank_humi_monitor
                cm = tank_humi_monitor.get_sonic_tank_cm()
                if cm > 0: 
                    result = str(cm) + ' cm'
                else:
                    result = "Error - I2C device not found!"

            except Exception:
                result = "Not available"

        return result


def find_lcd_address():
    search_range = {addr: 'PCF8574' for addr in range(32, 39)}
    search_range.update({addr: 'PCF8574A' for addr in range(56, 63)})

    try:
        import smbus

        bus = smbus.SMBus(0 if helpers.get_rpi_revision() == 1 else 1)
        # DF - alter RPi version test fallback to value that works on BBB
    except ImportError:
        log.warning(NAME, _('Could not import smbus.'))
    else:

        for addr, pcf_type in search_range.iteritems():
            try:
                # bus.write_quick(addr)
                bus.read_byte(addr) # DF - write_quick doesn't work on BBB
                log.info(NAME, 'Found %s on address 0x%02x' % (pcf_type, addr))
                lcd_options['address'] = addr
                break
            except Exception:
                pass
        else:
            log.warning(NAME, _('Could not find any PCF8574 controller.'))


def update_lcd(line1, line2=None):
    """Print messages to LCD 16x2"""

    if lcd_options['address'] == 0:
        find_lcd_address()

    if lcd_options['address'] != 0:
        import pylcd2  # Library for LCD 16x2 PCF8574

        lcd = pylcd2.lcd(lcd_options['address'], 0 if helpers.get_rpi_revision() == 1 else 1)
        # DF - alter RPi version test fallback to value that works on BBB
    else:
        lcd = dummy_lcd

    lcd.lcd_clear()
    sleep_time = 1
    while True:
        lcd.lcd_puts(line1[:16], 1)

        if line2 is not None:
            lcd.lcd_puts(line2[:16], 2)

        if max(len(line1), len(line2)) <= 16:
            break

        if len(line1) > 16:
            line1 = line1[1:]
        if line2 is not None:
            if len(line2) > 16:
                line2 = line2[1:]

        time.sleep(sleep_time)
        sleep_time = 0.5


################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for entering lcd adjustments."""

    def GET(self):
        return self.plugin_render.lcd_display(lcd_options, log.events(NAME))

    def POST(self):
        lcd_options.web_update(web.input())

        lcd_sender.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(lcd_options)

