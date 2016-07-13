Air Temperature and Humidity Monitor Readme
====

This plugin needs DHT11 sensor connected to GPIO 10 (pin 19 MOSI).
Range for Humidity: 20 - 90 % Relative Humidity  
Range for Temperature: 0 - 50 Celsius    

Plugin setup
-----------

* Check Enabled:  
  If checked enabled plugin is enabled.

* Check Enable logging:  
  If checked enabled logging save measure value to logfile (format .csv for Excel).

* Maximum number of log records:  
  Type maximum records in log file. 0 is unlimited.  

* Interval for logging:  
  Type interval for logging in minutes (minimum is 1).

* Label for sensor:  
  Type label for Your probe.

* Status:  
  Status window from the plugin.


The hardware should be connected as follows (without separate I2C Bus):
<a href="/plugins/air_temp_humi/static/images/schematics.png"><img src="/plugins/air_temp_humi/static/images/schematics.png" width="100%"></a>

Visit [Martin Pihrt's blog](http://www.pihrt.com). for more information.