Remote Notifications Readme
====

This plugin can send Notifications on the Remote Webserver. This plugin requre SQL server and Webserver with PHP.  
This plugin send data as get command to remote PHP web pages.  
This plugin requred correct settings this plugins: UPS Monitor, Tank Humi Monitor.  

Plugin setup
-----------
* Check Use plugin.    
  If checked send data to remote server is active. 

* Remote server address:  
  Type your remote server address where are the php files.  
  Ex: https://server.com/automatOSPy/

* API for access:  
  Type your API key, that is stored in a file save.php on the server.  
  Ex: msd455fsvv4sd5dv445s5s6d5vsdvdsv

* Status:
  Status window from the plugin.  
  
Visit [Martin Pihrt's blog](https://pihrt.com/automatOSPy/). for to demonstrate the function of watering my flowers.  

Note: For this plugin we need a public web server with PHP support and access to SQL database into which data is written from this plugin.

Server setup
-----------  
* On the Web server will place these files (after unpacking the zip file).  
  <a href="/plugins/remote_notifications/static/automatOSPy.zip">download automatOSPy.zip files</a>
* On the SQL server we create new database with new table: ospy as in imagge:  
  <a href="/plugins/remote_notifications/static/images/sql.png"><img src="/plugins/remote_notifications/static/images/sql.png" width="100%"></a>
* On the WEB server we places files as in imagge:  
  <a href="/plugins/remote_notifications/static/images/web.png"><img src="/plugins/remote_notifications/static/images/web.png" width="100%"></a>
* In file save.php we type own API key same as use this plugin.
* in file connect.php we type:  
  $server="address SQL server"; 
	$user="user name SQL server";
	$pass="password SQL server";    
	$db="ospy"; // name of table on the SQL server
  
  