# XPlane12_hdg_alt_on_ESP32S2_TFT_V2

Version 2024-01

This is the 2nd edition of an attempt to display XPlane-12 UDP datagram packet data onto an Adafruit Feather ESP32-S2-TFT device.
The scripts are derived from earlier similar projects for other devices.
In this example only the aircraft flight heading and its altitude are displayed on the TFT display of the feather ESP32-S2-TFT.
You can modify the scripts to display other flight parameters e.g.: current position or groundspeed.

The scripts of this project are compatible with:
Adafruit CircuitPython 9.0.0-alpha.6-46-gd7716de968 on 2024-01-25; Adafruit Feather ESP32-S2 TFT with ESP32S2

Within the XPlane-12 flightsimulator, running on a desktop PC or laptop the following settings have to be set for this project to be able to run correctly:

In XPlane-12 > Settings > Data Output > 

OUTPUT RATES:
Adjust slider "UDP Rate" to: 50.2 packets/sec

NETWORK CONFIGURATION, 
    Check "Send network data output";
    Enter the IP-address of your Feather ESP32-S2 TFT board. 
    "Port" enter the value: 49707.
In the left window (General Data Output) in column "Network via UDP" check :
```
    +--------+--------------------------------+-----------------+
    | Index: | Data to Output:                | Network via UDP |
    +--------+--------------------------------+-----------------+
    |    3   | Speeds                         |       v         |
    +--------+--------------------------------+-----------------+
    |   17   | Pitch, roll & headings         |       v         |
    +--------+--------------------------------+-----------------+
    |   20   | Latitude, longitude & altitude |       v         |
    +--------+--------------------------------+-----------------+
    |  102   | DME status                     |       v         |
    +--------+--------------------------------+-----------------+
```

To save these XPlane-12 Data Output settings, click on the blue button "Done" (lower right corner of this page)

See folder /images file: ```image08```.

settings.toml:

You have to set your personal WiFi settings (SSID, PASSWORD) into the file 
Also set your timezone data
and the "WIFI_IP" of your board (in format: WIFI_IP="192.168.x.xxx")

In settings.toml there are also two "interesting" settings:

a) ```SPEED_RUN=```: 
    If this setting is "1" the ```main()``` function in script file ```code.py``` will not call functions like: ```logo```, ```disp_bat```, ```blink_NEO```, ```disp_dt```, ```disp_author```.
    Function ```main()``` will immediately start to call the function ```dg.datagram_test()```, depening the state of the boolean flag ``` do_dg_test```
    and/or call the function  ```dr.dataref_test()```, depening the state of the boolean flag ``` do_dr_test```.

b) ```DEBUG_FLAG```:
    If this setting is "1" all debugging commands starting with:
```
        if my_debug:
            print("...")
```
    will be executed.

In case "no data" received from XPlane 12:
Reasons for this project not receiving packet data from XPlane-12 can be:
    - the PC-app: XPlane12 is not running;
    - necessary settings inside XPlane-12 have not beeen set or contain errors.
In file: ```XPlaneUdpDatagram.py```, class: ```XPlaneUdpDatagram```, function: ```GetUDPDatagram()```,
checks for the event that no data packet has been received. The function will keep count of ```no_data``` events.
When  a ```no_data``` event occurs, the message: ```Waiting for packets to client (IP...)``` will be shown on the display (see: /images/image10).
When the value of counter: ```no_data_cnt``` exceeds the value of variable: ```no_data_max_cnt```, the message 
```
    No data 
    XPlane running? 
    Exiting...
``` 
will be shown on the display (see /images/image11). Next the execution of the scripts will be ended by issuing a KeyboardInterrupt.

In file: ```XPlaneUdpDatagram.py```, class: ```XPlaneUdpDatagram```, function: ```OpenUPDSocket()``` will set: 
```self.my_DataGram_sock.settimeout(10)```. This command sets the socket timeout to 10 seconds.
Inside the function ```GetUDPDatagram()``` socket timeout events will be "catched". These events are then handled to prevent that
such a socket timeout event will crash the execution of the scripts.

Class gVars:
File ```common.py``` contains the class: ```gVars```. In the same file an instance of the gVars class, named: ```myVars``` will be created. The gVars class contains (in this moment) 35 variables. Most functions in this project set a common variable by issuing a command like: ```myVars.write("hdg_old", hdg_old)``` or the opposite: ```hdg_old = myVars.read("hdg_old")```. Some of the variables in file: ```settings.toml``` are written into the gVars class.
This system prevents the use of ```global``` variables, however it has it's overhead. Until this moment the project is running fine on the Adafruit Feather ESP32-S2 TFT.

