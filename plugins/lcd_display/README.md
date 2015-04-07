LCD Settings Readme
====

This plugin shows information on a 16x2 or 16x1 character LCD with PCF8574(A).  
Automatically detects the display at the following I2C addresses: 0x20-0x27, 0x38-0x3F.  
Compatible with the HD44780 controller.  

Plugin setup
-----------
* Check Use I2C LCD:  
  If checked use i2c lcd plugin is enabled and print messages on the LCD display.

* Check Use two lines:  
  If checked use two lines LCD display is 2x16 or 1x16 character.

* Check Use print lines to debug files:  
  If checked use print lines to debug files line 1 or line 2 print to debug files.  
  (warning: If you enable this debug file will have a huge size).  

* Status:
  Status window from the plugin.  
  Example message on the LCD display:  
  OpenSprinkler Py (text on line 1)
  Irrigation system (text on line 2)    
  CPU temperature:  
  42.8 C  
  Date: 17.02.2015  
  Time: 12:22:57  
  OSPy version:  
  2015-02-17  
  System uptime:  
  5:12:11  
  My IP is:  
  192.168.4.184  
  My port is:  
  8080  
  Rain sensor:  
  Inactive  
  Last program:  
  None  
  Pressure sensor:  
  Not available  

The hardware should be connected as follows:
<a href="/plugins/lcd_display/static/images/schematics.png"><img src="/plugins/lcd_display/static/images/schematics.png" width="100%"></a>

Visit [Martin Pihrt's blog](http://www.pihrt.com/elektronika/258-moje-rapsberry-pi-i2c-lcd-16x2
). for more information.
