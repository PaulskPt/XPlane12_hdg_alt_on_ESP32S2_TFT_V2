# _*_ coding: utf-8 _*_
# SPDX-FileCopyrightText: 2024 Paulus Schulinck
#
# SPDX-License-Identifier: MIT
##############################
# This file contains common global variables for:
# Files:
# - code.py
# - XPlaneUdpDatagram.py
# - XPlaneDatarefRx.py
#
# This file also contains the following shared functions:
# - tag_adjust()
# - make_pool()
# - blink_NEO_color()
# - get_page_name()
# - disp_msg()
# - go2_page()
# - NEO_pixel_test()
# - blink_NEO_v2()
# - clr_disp()
#
# This file contains the Class gVars
# and creates a gVars object: myVars
#
# Original see: I:\Raspberry_Pi\XPlane_datarefs\xp_data_outp_rx\XPlaneUdpDatagramLCDv11.py
# For the LCD 4x20 (e.g. used in the Hasseb.fi CMIO device) see file:
# I:\Raspberry_Pi\08th Raspberry pi - CM IO Hasseb FI\Files downloaded fm website Hassab\Sample_programs\RPLCD-master\RPLCD\lcd.py
# 2023-03-27, Adapted for an Adafruit Feather ESP32-S2 TFT
#
#type:ignore
import os, sys
import time
import board
import displayio
# import busio
from adafruit_displayio_layout.layouts.page_layout import PageLayout
import neopixel
import rtc

TX = board.TX
RX = board.RX
uart = None
#uart = busio.UART(TX, RX, baudrate=4800, timeout=0, receiver_buffer_size=151)  # board.RX, board.TX)

# release any currently configured displays
#displayio.release_displays()

# built-in display
display = board.DISPLAY
display.auto_refresh = False
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

# Define which type of LCD is connected:
# a) the Hitachi LCD 4x20 in the enclosure with the custom made Raspberry Pi CMIO and the CM3 connected;
Hasseb_lcd = False
# b) the loose Hitachi LCD 4x20 with only 4 lines connected to the Raspberry Pi: Vcc, GND, SDA to GPIO Pin 3 and SCL to GPIO Pin 5.
# The value of the flag Loose_lcd is alway the contrary of the value of Hasseb_lcd
Loose_lcd = False

# Important flag definitions:

my_have_tft = True
my_have_lcd = False # no, we're using an Adafruit Feather ESP32 S2 TFT display  (and not a raspberry pi (cmio + cm3) that has an 4x20 LCD builtin)
my_debug = False #  Debug / Printing flag
my_DoCheckCPUTemp = False # Flag to determine if we have to monitor the CPU temperature

use_getopt = True
my_debug = False
use_wifi = True
use_ping = False
use_tmp_sensor = False
use_logo = True
use_avatar = True
pool = None

if use_wifi:
    # Next 2 lines. See file 'settings.toml'
    ssid = os.getenv('CIRCUITPY_WIFI_SSID')
    password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
else:
    ssid = None
    password = None

tag_width = 30 # was: 25

page_dict = {
    0: 'Logo1',
    1: 'Logo2',
    2: 'XPlane',
    3: 'ID',
    4: 'Author',
    5: 'Battery',
    6: 'Message',
    7: 'Datetime'
}

if my_have_lcd:
    #  Flags for display on/off control (COPIED FROM Hasseb.fi, file: lcd.py)
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00
    LCD_DISPLAYCONTROL = 0x08
    LCD_ENTRYSHIFTDECREMENT = 0x00 # = cursor shift
    LCD_ENTRYSHIFTINCREMENT = 0x01 # = display shift

def tag_adjust(s):
    global tag_width
    le = len(s)
    if my_debug:
        print("tag_adjust(): param s= \'{}\', len(s)= {}, global tag_width= {}".format(s, le, tag_width), file=sys.stderr)
    if le >= tag_width:
        s2 = s[:tag_width]
    else:
        s2 = (s + ' '*(tag_width-le))
    # print("tag_adjust: returning \'{}\'".format(s2), file=sys.stderr)
    return s2

def make_pool():
    global pool
    TAG= tag_adjust("common.make_pool(): ")

    """
    # return if pool is already an object of SocketPool class
    if isinstance(pool, socketpool.SocketPool):
        print(TAG+f"returning because type(pool) = {type(pool)}")
        return pool
    """
    
    try:
        if pool is None:
            if not my_debug:
                print(TAG+'pool is None. Going to create it', file=sys.stderr)
            import socketpool
    except NameError:
        import socketpool

    pool = socketpool.SocketPool(wifi.radio)
    if my_debug:
        print(TAG+'type(pool)= {}'.format(type(pool)), file=sys.stderr)
    return pool

TAG= tag_adjust("common.global: ")

if use_wifi:
    try:
        if wifi is None:
            import wifi
    except NameError: # this error occurrs when 'wifi' is not defined
        import wifi # so we going to try to import wifi
        if my_debug:
            print(TAG+'type(wifi)= {}'.format(type(wifi)), file=sys.stderr)

    if pool is None:
        pool = make_pool()
        
    import adafruit_ntp
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)


dg = None

dr = None

udp_packet_types = {
    0: b"BECN",
    1: b"DATA",
    2: b"XATT",
    3: b"XGPS",
    4: b'XTRA'}

udp_packet_types_rev = {
    b"BECN" : 0,
    b"DATA": 1,
    b"XATT": 2,
    b"XGPS": 3,
    b'XTRA': 4}

ADAFRUIT_IO_KEY = None
ADAFRUIT_IO_USERNAME = None
author_lst = None
blink_cycles = 2
degs_sign = '' # chr(186)  # I preferred the real degrees sign which is: chr(176)
ip = None
location = None
old_temp = 0.00
requests = None
rtc = rtc.RTC()  # create internal RTC object
s_ip = None
SCRIPT_NAME = ''
temp_sensor_present = None
temp_update_cnt = 0
TIME_URL = None
tmp117 = None
tt = None
tz_offset = None
XPlane_version = "X-Plane 12"

# hdg_alt_lst = None

neo_brill = 50
neo_black = (0, 0, 0)
neo_blue = (0, 0, neo_brill)
neo_green = (0, neo_brill, 0)
neo_red = (neo_brill, 0, 0)
neo_led_blue = 3
neo_led_green = 2
neo_led_red = 1

"""
Logo1_dict    = { "name": "Logo1",    "items": {} }
Logo2_dict    = { "name": "Logo2",    "items": {} }
XPlane_dict   = { "name": "XPlane",   "items": {"Label0": {}, "Label1": {} } }
ID_dict       = { "name": "ID",       "items": {"Label0": {} } }
Author_dict   = { "name": "Author",   "items": {"Label0": {}, "Label1": {}, "Label2": {} } }
Battery_dict  = { "name": "Battery",  "items": {"Label0": {} } }
Message_dict  = { "name": "Message",  "items": {"Label0": {}, "Label1": {} } }
Datetime_dict = { "name": "Datetime", "items": {"Label0": {}, "Label1": {} } }


my_page_layout_dict = {0: Logo1_dict, 
    1: Logo2_dict,
    2: XPlane_dict,
    3: ID_dict,
    4: Author_dict,
    5: Battery_dict,
    6: Message_dict,
    7: Datetime_dict}


grp_dict = { 0: my_page_layout_dict }

print(f"Common: grp_dict.items()= {grp_dict.items()}")
"""

weekdays = {0:"Monday", 1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}

# release any currently configured displays
#displayio.release_displays()
start_t= time.monotonic()
start_0 = start_t # remember (and don't change this value!!!)
time_received = False

lcd = None

# unichr used to print a degrees sign from the Hitachi LCD ROM A00. See: class RaspiCheckCPUTemp()
try:
    unichr = unichr
except NameError:  # Python 3
    unichr = chr

def blink_NEO_color(color):

    pixel.brightness = 0.3

    if color is None:
        for _ in range(blink_cycles):
            pixel.fill(neo_red)
            time.sleep(0.5)
            pixel.fill(neo_green)
            time.sleep(0.5)
            pixel.fill(neo_blue)
            time.sleep(0.5)
        pixel.fill((0, 0, 0))
    else:
        if color == neo_led_red:
            c = neo_led_red # red
        elif color == neo_led_green:
            c = neo_green  # green
        elif color == neo_led_blue:
            c = neo_blue  # blue
        else:
            print('blink_NEO_color(): color undefine. Got {}'.format(color), file=sys.stderr)
            return

        if color > 0:
            # blink in the chosen color
            for _ in range(blink_cycles):
                pixel.fill(c)
                time.sleep(0.5)
                pixel.fill(neo_black)
                time.sleep(0.5)

# +-------------------------------------------------------+
# | Definition for variables in the past defined as global|
# +-------------------------------------------------------+
# The gVars class is created
# to elminate the need for global variables.

class gVars:
    def __init__(self):

        self.gVarsDict = {
            0: "my_debug",
            1: "id",
            2: "rtc",
            3: "disp_width",
            4: "disp_height",
            5: "xp_lst",
            6: "TFT_show_duration",
            7: "kbd_intr",
            8: "use_udp_host",
            9: "multicast_group1",
           10: "multicast_group2",
           11: "multicast_port1",
           12: "multicast_port2",
           13: "packet_types_used",
           14: "xplane_version",
           15: "main_loop_nr",
           16: "hdg_old",
           17: "alt_old",
           18: "main_grp",
           19: "my_page_layout",
           20: "logo1_grp",
           21: "logo2_grp",
           22: "ba_grp",
           23: "dt_grp",
           24: "ta1_grp",
           25: "ta2_grp",
           26: "xp_grp",
           27: "msg_grp",
           28: "current_page",
           29: "Main",
           30: "NTP_dt",
           31: "NTP_dt_is_set",
           32: "client_IP",
           33: "start",
           34: "no_data",
           35: "pool_socket_timeout_set",
           36: "speed_run"
        }

        self.gVars_rDict = {
            "my_debug": 0,
            "id": 1,
            "rtc": 2,
            "disp_width": 3,
            "disp_height": 4,
            "xp_lst": 5,
            "TFT_show_duration": 6,
            "kbd_intr": 7,
            "use_udp_host": 8,
            "multicast_group1": 9,
            "multicast_group2": 19,
            "multicast_port1": 11,
            "multicast_port2": 12,
            "packet_types_used": 13,
            "xplane_version": 14,
            "main_loop_nr": 15,
            "hdg_old": 16,
            "alt_old": 17,
            "main_grp": 18,
            "my_page_layout": 19,
            "logo1_grp": 20,
            "logo2_grp": 21,
            "ba_grp": 22,
            "dt_grp": 23,
            "ta1_grp": 24,
            "ta2_grp": 25,
            "xp_grp": 26,
            "msg_grp": 27,
            "current_page": 28,
            "Main": 29,
            "NTP_dt": 30,
            "NTP_dt_is_set": 31,
            "client_IP": 32,
            "start": 33,
            "no_data": 34,
            "pool_socket_timeout_set": 35,
            "speed_run": 36
        }

        self.g_vars = {}

        # self.clean()
        
        my_debug = True if "1" == os.getenv("DEBUG_FLAG") else False
        speed_run = True if "1" == os.getenv("SPEED_RUN") else False
        
        # -------------- Setting myVars elements ----------------------------------
        self.write("my_debug", my_debug)
        self.write("id", board.board_id ) # 'adafruit_feather_esp32s2_tft'
        self.write("rtc", None)
        self.write("disp_width", display.width)
        self.write("disp_height", display.height)
        self.write("xp_lst", None)
        self.write("TFT_show_duration", 5)
        self.write("kbd_intr", False)
        self.write("use_udp_host", os.getenv("USE_UDP_HOST"))
        self.write("multicast_group1", os.getenv("MULTICAST_GROUP1"))
        self.write("multicast_group2", os.getenv("MULTICAST_GROUP2"))
        self.write("multicast_port1", int(os.getenv("MULTICAST_PORT1")))
        self.write("multicast_port2", int(os.getenv("MULTICAST_PORT2")))
        # self.write("packet_types_used", ['XGPS']) # or ['XGPS', 'XATT', 'XTRA']
        self.write("packet_types_used", os.getenv("PACKET_TYPES_USED"))
        self.write("xplane_version", os.getenv("XPLANE_VERSION"))
        self.write("main_loop_nr", 0)
        self.write("hdg_old",0)
        self.write("alt_old",0)
        self.write("main_grp", None)
        self.write("my_page_layout", None)
        self.write("logo1_grp", None)
        self.write("logo2_grp", None)
        self.write("ba_grp", None)
        self.write("dt_grp", None)
        self.write("ta1_grp", None)
        self.write("ta2_grp", None)
        self.write("xp_grp", None)
        self.write("msg_grp", None)
        self.write("current_page", None)
        self.write("Main", None)
        self.write("NTP_dt", None)
        self.write("NTP_dt_is_set", False)
        self.write("client_IP", None)
        self.write("client_IP", False)
        self.write("no_data",False)
        self.write("pool_socket_timeout_set", False)
        self.write("speed_run", speed_run)

    def write(self, s, value):
        if isinstance(s, str):
            if s in self.gVars_rDict:
                n = self.gVars_rDict[s]
                if my_debug:
                    print("myVars.write() \'{:" ">20s}\' found in self.gVars_rDict, key: {}".format(s, n), file=sys.stderr)
                self.g_vars[n] = value
            else:
                raise KeyError(
                    "variable '{:" ">20s}' not found in self.gVars_rDict".format(s)
                )
        else:
            raise TypeError(
                "myVars.write(): param s expected str, {} received".format(type(s))
            )

    def read(self, s):
        RetVal = None
        if isinstance(s, str):
            if s in self.gVars_rDict:
                n = self.gVars_rDict[s]
                if my_debug:
                    print("myVars.write() \'{:" ">20s}\' found in self.gVars_rDict, key: {}".format(s, n), file=sys.stderr)
                if n in self.g_vars:
                    RetVal = self.g_vars[n]
        return RetVal

    def clean(self):
        self.g_vars = {
            0: None,
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None,
            7: None,
            8: None,
            9: None,
            10: None,
            11: None,
            12: None,
            13: None,
            14: None,
            15: None,
            16: None,
            17: None,
            18: None,
            19: None,
            20: None,
            21: None,
            22: None,
            23: None,
            24: None,
            25: None,
            26: None,
            27: None,
            28: None,
            29: None,
            30: None,
            31: None,
            32: None,
            33: None,
            34: None,
            35: None,
            36: None
    }

    def list(self):
        for i in range(0, len(self.g_vars) - 1):
            print(
                "self.g_vars['{:"
                ">20s}'] = {}".format(
                    self.gVarsDict[i], self.g_vars[i] if i in self.g_vars else "None"
                )
            )


# ---------- End of class gVars ------------------------

myVars = gVars()  # create an instance of the gVars class

print("\nThis script is running on an \'{}\'".format(myVars.read("id")), file=sys.stderr)

# create and show main_group
main_grp = displayio.Group()
myVars.write("main_grp", main_grp)
print(TAG+f"display= {display}, main_grp= {main_grp}")
display.root_group = main_grp

# create the page layout
my_page_layout = PageLayout(x=0, y=0)
myVars.write("my_page_layout", my_page_layout)
# Cleanup
main_grp = None
my_page_layout = None 


if use_logo:
    img_lst = ["avatar", "blinka"]  # ["paulskpt", "blinka"]   # Note: these images are 100 x ca. 100 px
    # from displayio import OnDiskBitmap, TileGrid
    myVars.write("logo1_grp", displayio.Group())
    myVars.write("logo2_grp", displayio.Group())
else:
    img_lst = None
    logo1_grp = None
    logo2_grp = None
    
def get_page_name(page_index):
    le = len(page_dict)
    # print("get_page_number(): param page_index = {}".format(page_index), file=sys.stderr)
    if page_index >= 0 and page_index < le:
        if page_index in page_dict.keys():
            return page_dict[page_index]
    return ''

def disp_msg(msg_lst):
    TAG = tag_adjust("disp_msg(): ")
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")
    msg_grp = myVars.read("msg_grp")
    if not my_debug:
        print(TAG+"Entering...")
    if my_debug:
        print(TAG+f"msg_grp= {msg_grp}")
        print(TAG+f"msg_grp.hidden= {msg_grp.hidden}")
    # Update this to change the text displayed.
    if isinstance(msg_lst, list):
        le = len(msg_lst)
        if le > 0:
            if not my_debug:
                print(TAG+f"param msg_lst= {msg_lst}", file=sys.stderr)
            # Update this to change the size of the text displayed. Must be a whole number.
            # print(TAG, file=sys.stderr, end='')
            if my_debug:
                print(TAG+f"length of msg_lst: {le}", file=sys.stderr, end='\n')
                print(TAG+"contents of msg_lst:", file=sys.stderr, end='\n')
            for _ in range(le):
                msg_grp[_].text = msg_lst[_]
                if my_debug:
                    print(TAG+"\'{}\' ".format(msg_lst[_]), file=sys.stderr, end='\n')
            if not my_debug:
                for _ in range(le):
                    # print(TAG+f"msg_grp[{_}].x= {msg_grp[_].x}, msg_grp[{_}].y= {msg_grp[_].y} ")
                    # print(TAG+f"msg_grp[{_}].text= {msg_grp[_].text}")
                    print(TAG+f"{msg_grp[_].text}")
            display.root_group = main_grp
            my_page_layout.showing_page_name = "Message"
            if my_debug:
                print(TAG+f"showing page index: {my_page_layout.showing_page_index}")
                print(TAG+f"showing page name: {my_page_layout.showing_page_name}")    
        time.sleep(1)  # Display message just for a short time

def go2_page(srch_name):
    global myVars
    TAG= tag_adjust("go2_page_name(): ")
    page_names = ["Logo1",     "Logo2",     "Battery", "Datetime", "ID",      "Author",  "XPlane"]
    grp_names =  ["logo1_grp", "logo2_grp", "ba_grp",  "dt_grp",   "ta1_grp", "ta2_grp", "xp_grp"]
    my_page_layout = myVars.read("my_page_layout") 
    cpg = None
    grp = None
    if my_debug:
        print(TAG+"Entering...")
    if srch_name in page_names:
        my_page_layout.show_page(page_name=srch_name)
        cp = get_page_name(my_page_layout.showing_page_index)
        if my_debug:
            print(TAG+f"current page name = {cp}")
        if cp != srch_name:
            while srch_name != get_page_name(my_page_layout.showing_page_index):
                my_page_layout.next_page(True)
                cp = get_page_name(my_page_layout.showing_page_index)
                if my_debug:
                    print(TAG+f"current page name = {cp}")
                if cp == srch_name:
                    myVars.write("current_page", cp)  # remember the page shown
                    break
        if not my_debug:
            print(TAG+f"showing page: {cp}")
            print(TAG+f"showing page index: {my_page_layout.showing_page_index}")
            print(TAG+f"showing page name: {my_page_layout.showing_page_name}")   
    else:
        display.root_group = my_page_layout  # myVars.read("main_grp")
        if not my_debug:
            print(TAG+f"showing page: Main")

br = 50  # was 255
RED = 0
GREEN = 1
BLUE = 2
NEO_red = (br,  0,  0)
NEO_grn = ( 0, br,  0)
NEO_blu = ( 0,  0, br)
NEO_blk = ( 0,  0,  0)

colors_dict = {
    RED : "RED",
    GREEN: "GREEN",
    BLUE: "BLUE"
}

def NEO_pixel_test():
    TAG= tag_adjust("NEO_pixel_test(): ")
    runs = 3
    blink_it = 2
    for _ in range(runs):
        if not my_debug:
            print(TAG+f"test nr: {_} of {runs}")
            print(TAG+f"calling blink_NEO_v2() with params: times= {blink_it}, color= {_}")
        blink_NEO_v2(blink_it, _)

def blink_NEO_v2(nr_times, color_c):
    TAG= tag_adjust("blink_NEO_v2(): ")
    max_times = 3
    if nr_times == None:
        nr_times = blink_cycles
    elif nr_times < 1:
        nr_times = 1
    elif nr_times > max_times:
        nr_times = max_times
        
    if color_c == None:
        color = NEO_red
    elif color_c == GREEN:
        color = NEO_grn
    elif color_c == RED:
        color = NEO_red
    elif color_c == BLUE:
        color = NEO_blu
    pixel.brightness = 0.3
    if nr_times == 1:
        t = "time"
    else:
        t = "times"
    print(TAG+f"Blinking Neopixel led {nr_times} {t} in color {colors_dict[color_c]}")
    for _ in range(nr_times):
        pixel.fill(color)
        time.sleep(0.2)
        pixel.fill(NEO_blk)
        time.sleep(0.2)

# See: https://github.com/adafruit/circuitpython/pull/2756
def clr_disp():
    TAG= tag_adjust("clr_disp(): ")
    print(TAG+"Entering...")
    WIDTH = display.width
    HEIGHT = display.height

    COLORS = (0xFF0000, 0x00FF00, 0x0000FF)

    bitmap = displayio.Bitmap(WIDTH, HEIGHT, len(COLORS))

    palette = displayio.Palette(len(COLORS))
    for i, color in enumerate(COLORS):
        palette[i] = color

    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

    splash = displayio.Group()
    splash.append(tile_grid)

    #display.show(splash)
    display.root_group = splash

    # print(TAG+"Fill 1")
    display.auto_refresh = False
    start_t = time.monotonic()
    for i in range(WIDTH*HEIGHT):
        bitmap[i] = 1
    #print(time.monotonic() - start_t)
    display.auto_refresh = True
    display.root_group = main_grp
    time.sleep(1)
    #print(TAG+"Fill 2")
    start_t = time.monotonic()
    bitmap.fill(2)
    #print(time.monotonic() - start_t)