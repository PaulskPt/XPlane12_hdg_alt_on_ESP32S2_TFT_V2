# _*_ coding: utf-8 _*_
# SPDX-FileCopyrightText: 2024 Paulus Schulinck
#
# SPDX-License-Identifier: MIT
##############################
#
# #XPlaneUdpDatagramLCD.py
# Ver 11, 2019-08-13 10h22 UTC
# See: # Original see: I:\Raspberry_Pi\XPlane_datarefs\xp_data_outp_rx\XPlaneUdpDatagramLCDv11.py
#
# Class to get UDP Datagram packets from X-Plane 11 Flight Simulator via a (local area) network.
#
# Original idea for the X-Plane UDP Data Output receiver, "XPlaneUdp.py", by charlylima
# Charlylima's python script was to detect BECN packets and then to ask and receive DataRef packets.
#
# This python script is a modified and extended version of Charlylima's script.
# The target of this script is to detect UDP Datagram packets, sent by an X-Plane host to a Multicast group (LAN).
# Further this script has a functionality to print selected data to a 4x20 char LCD screen.
# This script has been developed and tested on a custom made Raspberry Pi CM IO board by Hasseb.fi, containing a Raspberry CM3 and a LCD from Hitachi.
#
# The XPlaneUdp.py example was downloaded from GitHub: https://github.com/charlylima/XPlaneUDP
# Charlylima states "that he witten it for Python 3 but I, Paulsk, have adapted it for running under Python 2(7.2)
#
# In Version 10 added implementation of LCD writing a string to a line,col. Example:
# lcd.lcd_display_string_pos('', 4, 20)
#
# In version 11 added a line in lcd_cleanup() to switch off the backlight.
#
# Comments, suggestions and feedback is welcome.
# 2019-04-24, Paulsk (mailto: ct7agr@live.com.pt)
# ---------------------------------------------------------
# ToDo: (2023-03-31)
# The Feather ESP32-S2 TFT is often receiving a different LAN IP-address
# for this we have to alter the IP-address in XPlane-12 !
# Resolution could be: have the feather device obtain a fixed IP-address
# ---------------------------------------------------------
# 2023-02-08 On Github I openend Issue https://github.com/adafruit/circuitpython/issues/7556
# 2024-01-22 I closed the issue #7556 because my request was fulfilled.
# 2023-03-27, Adapted for an Adafruit Feather ESP32-S2 TFT
# 2024-01-22 Updated the repo on Github for use with X-Plane 12
#
#type:ignore
import sys
# import string
import time
# import subprocess
# from subprocess import call # subprocess is more flexible than system. You can get stdout, stderr, the "real" status code, better error handling etc.


# ----------------------------------------
# Part for Adafruit Feather ESP32-S2 TFT
# ----------------------------------------
import board
import terminalio
import digitalio
import os, sys, gc
import displayio
from adafruit_display_text import label  # bitmap_label
from displayio import OnDiskBitmap, TileGrid
#from adafruit_bitmap_font import bitmap_font
from adafruit_lc709203f import LC709203F
import terminalio
# from adafruit_displayio_layout.layouts.page_layout import PageLayout  # see common.py
from common import *
from XPlaneDatarefRx import *
from XPlaneUdpDatagram import *

# Most global flags moved to common.py

# =======================
#  Start of Definitions =
# =======================

if use_getopt:
    try:
        import getopt
    except ImportError:
        use_getopt = False # Set flag to false

# Pre-definition
def scan_i2c():
    pass

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

i2c = board.I2C()

scan_i2c()

bat_sensor = LC709203F(i2c)

if use_wifi:
    #import wifi        # Already imported in common.py
    #import socketpool  # idem
    import ssl
    import ipaddress
    import adafruit_requests
    # import adafruit_ntp
    from rtc import RTC

rtc = RTC()

# print(f"Common: dir(display) = {dir(display)}")

# create the page layout
# my_page_layout = PageLayout(x=0, y=0)  # is defined in common.py

if my_have_lcd:
    if Hasseb_lcd:
        # Imports necessary for printing to the LCD
        from lcd4linesv2 import CharLCD_psk
        from lcd4linesv2 import Alignment, CursorMode, ShiftMode # lcd4linesv2 is a modified version of lcd.py
        from contextmanagers import cursor, cleared   # belongs to the Hasseb.fi LCD python library
    elif Loose_lcd:
        import lcddriver

    #  Imports necessary for GPIO handling
    import RPi.GPIO as GPIO
#
# From: https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=49204
#     Send/Receive with TCP sockets
#
# From: https://pymotw.com/2/socket/udp.html
#     User Datagram Client and Server
#
# UDP-Client
#

if my_have_lcd:
    #  Switch off GPIO warnings like "port in use" etcetera.
    GPIO.setwarnings(False)

    if Hasseb_lcd:
        #  PWM control of the backlight
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(41, GPIO.OUT)
        p = GPIO.PWM(41, 200)
        p.start(100)

    # Here were LCD_DISPLAYON definition and other equal definitions moved to common.py

    if Hasseb_lcd:
        lcd = CharLCD_psk()       # Create an instance of the lcd class
        curm = CursorMode()       # Create an instance of the CursorMode class
    elif Loose_lcd:
        lcd = lcddriver.lcd()

def scan_i2c():
    TAG= tag_adjust("scan_i2c(): ")
    if not my_debug:
        dev_list = []
    try:
        while not i2c.try_lock():
            i2c.try_lock()
            time.sleep(0.5)
        print(TAG+f"Start scan for connected I2C devices...")
        dev_list = i2c.scan()
        if dev_list is not None:
            le = len(dev_list)
            print("{}{} I2C device{} found:".format(' '*tag_width, le, "s" if le > 1 else ""), file=sys.stderr)
            for _ in range(le):
                print("{}Device {:d} at address 0x{:02x}".format(' '*tag_width, _, dev_list[_]), file=sys.stderr)
        i2c.unlock()
        print("{}End of i2c scan".format(' '*tag_width), file=sys.stderr)
    except Exception as exc:
        raise

# here was function get_page_name(). Moved to common.py

def disp_logo(choice):
    TAG= tag_adjust("disp_logo(): ")
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")

    if my_debug:
        print(TAG+f"Entering...")
    logo_lst = ["Logo1", "Logo2"]

    try:
        if choice >= 1 and choice <= 2:
            if not my_debug:
                print(TAG+"going to display image file: \'{}\'".format(img_lst[choice-1]), file=sys.stderr)
            #display.root_group = main_grp
            if choice == 1:
                logo = myVars.read("logo1_grp")
            elif choice == 2:
                logo = myVars.read("logo1_grp")
                
            display.root_group = main_grp
            my_page_layout.showing_page_name = logo_lst[choice-1]
            #go2_page(logo_lst[choice-1])
            time.sleep(myVars.read("TFT_show_duration")+2) # in seconds
    except OSError as e:
        print(TAG+"Error: {}".format(e), file=sys.stderr)
    except Exception as e:
        print(TAG+"Error: {}".format(e), file=sys.stderr)
        raise

def disp_id():
    TAG= tag_adjust("disp_id(): ")
    id = myVars.read("id")
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")
    ta1_grp = myVars.read("ta1_grp")
    
    if my_debug:
        print(TAG+f"Entering... ")
        print(TAG+f"ta1_grp= {ta1_grp}")
    t_lst = id.split('_') # ['Adafruit', 'feather', 'esp32s2', 'tft']
    if my_debug:
        print(TAG+f"t_lst = {t_lst}")
    if len(t_lst) > 0:
        t_lst[2] = t_lst[2] + ' ' + t_lst[3] # join 3rd and 4th element
        t_lst2 = []
        for _ in range(len(t_lst)-1):  # create new list t_lst2, less the 4th element of t_lst
            t_lst2.append(t_lst[_])
        t_lst = []
        if my_debug:
            print(TAG+f"t_lst2= {t_lst2}") # ['Adafruit', 'feather', 'esp32s2 tft']
        if not my_debug:
            print(TAG+"ID to display: \'", end='')
        le = len(t_lst2)
        if le > 0:
            for _ in range(le):
                #ta1[_].scale = 3
                t = t_lst2[_]
                ta1_grp[_].text = t
                if not my_debug:
                    if _ < le-1:
                        print(t+' ', file=sys.stderr, end='')
                    else:
                        print(t, file=sys.stderr, end='')
            if not my_debug:
                print('\'', file=sys.stderr, end='\n')
            myVars.write("ta1_grp", ta1_grp)  # update ta
            
            display.root_group = main_grp
            my_page_layout.showing_page_name = "ID"
            if my_debug:
                print(TAG+f"showing page index: {my_page_layout.showing_page_index}")
                print(TAG+f"showing page name: {my_page_layout.showing_page_name}")
            time.sleep(myVars.read("TFT_show_duration"))


def disp_author():
    global author_lst
    TAG= tag_adjust("disp_author(): ")
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")
    ta2_grp = myVars.read("ta2_grp")
    if my_debug:
        print(TAG+"Entering...")
        print(TAG+f"ta2_grp= {ta2_grp}")
        print(TAG+f"ta2_grp.hidden= {ta2_grp.hidden}")
    # Update this to change the text displayed.
    if isinstance(author_lst, list):
        le = len(author_lst)
        if le > 0:
            #print("author_lst= {}".format({author_lst), file=sys.stderr)
            # Update this to change the size of the text displayed. Must be a whole number.
            # print(TAG, file=sys.stderr, end='')
            if my_debug:
                print(TAG+"length of author_lst: {}".format(le), file=sys.stderr, end='\n')
                print(TAG+"contents of author_lst:", file=sys.stderr, end='\n')
            for _ in range(le):
                #ta2_grp[_].scale = 2
                ta2_grp[_].text = author_lst[_]
                #myVars.write("ta2", ta2)  # update ta2
                if my_debug:
                    print(TAG+"\'{}\' ".format(author_lst[_]), file=sys.stderr, end='\n')
            if not my_debug:
                for _ in range(le):
                    # print(TAG+f"ta2_grp[{_}].x= {ta2_grp[_].x}, ta2_grp[{_}].y= {ta2_grp[_].y} ")
                    # print(TAG+f"ta2_grp[{_}].text= {ta2_grp[_].text}")
                    print(TAG+f"{ta2_grp[_].text}")
            display.root_group = main_grp
            my_page_layout.showing_page_name = "Author"
            if my_debug:
                print(TAG+f"showing page index: {my_page_layout.showing_page_index}")
                print(TAG+f"showing page name: {my_page_layout.showing_page_name}")    
            time.sleep(myVars.read("TFT_show_duration"))  # don't need to wait here. It takes some time to get XGPS data

def disp_bat():
    #global bitmap_label
    TAG= tag_adjust("disp_bat(): ")
    ba_grp = myVars.read("ba_grp")
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")
    start = myVars.read("start")
    #ba_grp[0].anchored_position=(0,0)  # Change the anchored position
    if my_debug:
        print(TAG+f"Entering...")
        print(TAG+f"ba_grp= {ba_grp}")
        print(TAG+f"ba_grp.hidden= {ba_grp.hidden}")      
        for _ in range(len(ba_grp)):
            print(TAG+f"ba_grp[{_}]= {ba_grp[_]}")
            print(TAG+f"ba_grp[{_}].hidden= {ba_grp[_].hidden}")            
            print(TAG+f"ba_grp[{_}].scale= {ba_grp[_].scale}")
            print(TAG+f"ba_grp[{_}].anchor_point= {ba_grp[_].anchor_point}")
            print(TAG+f"ba_grp[{_}].anchored_position= {ba_grp[_].anchored_position}")
    if start and not my_debug:
        print(TAG+"LC709203F test", file=sys.stderr)
        print(TAG+"Make sure LiPoly battery is plugged into the board!", file=sys.stderr)
        print(TAG+"Battery IC version:", hex(bat_sensor.ic_version), file=sys.stderr)
    s1 = "Battery:" # \n{:.1f} Volts \n{}%"
    s2 = "{:.1f}V, {}% chg"
    #s3 = s1.format(bat_sensor.cell_voltage, bat_sensor.cell_percent)
    s4 = s2.format(bat_sensor.cell_voltage, bat_sensor.cell_percent)
    ba_grp[0].text = s1
    ba_grp[1].text = s4
    #ba_grp[2].text = s4
    myVars.write("ba_grp", ba_grp)  # update

    if start and my_debug:
        for _ in range(len(ba_grp)):
            print(TAG+f"ba_grp[_].text= {ba_grp[_].text}")
    # change page by updating the page name property
    display.root_group = main_grp  #ba_grp
    my_page_layout.showing_page_name = "Battery"
    if my_debug:
        print(TAG+f"showing page index: {my_page_layout.showing_page_index}")
        print(TAG+f"showing page name: {my_page_layout.showing_page_name}")

    print(TAG+s1, file=sys.stderr)
    print(TAG+s4, file=sys.stderr)
    time.sleep(myVars.read("TFT_show_duration")) # in seconds


def disp_dt():
    TAG = tag_adjust("disp_dt(): ")
    if my_debug:
        print(TAG+"Entering...")
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")
    dt_grp = myVars.read("dt_grp")
    if my_debug:
        for _ in range(len(dt_grp)):
            print(TAG+f"dt_grp[{_}]= {dt_grp[_]}")
    """
        Get the datetime from the built-in RTC
        After being updated (synchronized) from an NTP server;
        Note: the built-in RTC datetime gives always -1 for tm_isdst
              We determine is_dst from resp_lst[5] extracted from the AIO time server response text
    """
    ct = rtc.datetime  # read datetime from built_in RTC
    # print(TAG+"datetime from built-in rtc= {}".format(ct), file=sys.stderr)
    # weekday (ct[6]) Correct because built-in RTC weekday index is different from the AIO weekday
    #                                                                                                              yd
    sDt = "YearDay: {}, WeekDay: {} {:4d}-{:02d}-{:02d}, {:02d}:{:02d}, timezone offset: {} Hr, is_dst: {}".format(ct[7],
    #                yy     mo     dd     hh     mm            is_dst
    weekdays[ct[6]], ct[0], ct[1], ct[2], ct[3], ct[4], tz_offset, ct[8])
    #                               yy     mo     dd
    dt0 = "{}-{:02d}-{:02d}".format(ct[0], ct[1], ct[2])
    dt_grp[0].text = dt0
    #tm = "{:02d}:{:02d}".format(ct[4], ct[5])
    #                           hh     mm
    tm = "{:02d}:{:02d}".format(ct[3], ct[4])
    dt_grp[1].text = tm
    myVars.write("dt_grp", dt_grp)  # update dt
    
    
    display.root_group = main_grp  # dt_grp
    my_page_layout.showing_page_name = "Datetime"
    if my_debug:
        print(TAG+f"showing page index: {my_page_layout.showing_page_index}")
        print(TAG+f"showing page name: {my_page_layout.showing_page_name}")
        for _ in range(len(dt_grp)):
            print(TAG+f"dt_grp[{_}].text= {dt_grp[_].text}")
        print(TAG+f"date time from built-in rtc: {dt0}")
    else:
        print(TAG+"date: {}, time: {}".format(dt0, tm), file=sys.stderr)
    time.sleep(myVars.read("TFT_show_duration")) # in seconds

def blink():
    for _ in range(blink_cycles):
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.5)

def blink_NEO():
    TAG= tag_adjust("blink_NEO(): ")
    pixel.brightness = 0.3
    print(TAG+"Testing Neopixel led...")
    for _ in range(blink_cycles):
        pixel.fill(NEO_red)
        time.sleep(0.5)
        pixel.fill(NEO_grn)
        time.sleep(0.5)
        pixel.fill(NEO_blu)
        time.sleep(0.5)
    pixel.fill(NEO_blk)

def wifi_is_connected():
    global ip, s_ip
    TAG= tag_adjust("wifi_is_connected(): ")
    ret = False

    ip = wifi.radio.ipv4_address

    if ip:
        s_ip = str(ip)
        le_s_ip = len(s_ip)

    if s_ip is not None and len(s_ip) > 0 and s_ip != '0.0.0.0':
        if not my_debug:
            print(TAG+f"s_ip = {s_ip}")
        myVars.write("client_IP", s_ip) # Save the client IP
        ret = True
    return ret

def create_groups():
    global img_lst
    TAG= tag_adjust("create_groups(): ")
    
    main_grp = myVars.read("main_grp")
    my_page_layout = myVars.read("my_page_layout")
    #font = bitmap_font.load_font("/Helvetica-Bold-16.bdf")
    tile_grid0 = None
    tile_grid1 = None
    tile_grid2 = None
    
    if my_debug:
        print(TAG+"Entering...")
    tmp_grp = None
    k = ''
    if use_avatar:
        ax = 156
    else:
        ax = 120
    grp_dict = {  # ba = battery, dt = datetime, ta1 = ID, ta2 = Author, xp = XPlane
        #'ba': {'nr_items': 1, 'scale': 2, 'anchor_point': (0.5, 0.5),
        #    'anchored_position': (display.width // 2, display.height // 2), 'vpos_increase': 0},
        'ba':  {'nr_items': 2, 'scale': 2, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 40), 'vpos_increase': 30},
        'dt':  {'nr_items': 2, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 50), 'vpos_increase': 40},
        'ta1': {'nr_items': 3, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 40), 'vpos_increase': 30},
        'ta2': {'nr_items': 3, 'scale': 2, 'anchor_point': (0.5, 0.5), 'anchored_position': (ax,  40), 'vpos_increase': 30},
        'xp':  {'nr_items': 3, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 40), 'vpos_increase': 40},
        'msg': {'nr_items': 3, 'scale': 2, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 40), 'vpos_increase': 30},
    }

    for _ in range(len(img_lst)):
        fn = "bmp/" + img_lst[_] + ".bmp" # Or use a general image: bmp/blinka.bmp"
        if not my_debug:
            print(TAG+"loading image \'{}\'".format(fn), file=sys.stderr)
        logo_img = OnDiskBitmap(fn)
        if _ == 0:
            # Titegrid to use in disp_author()
            if use_avatar:
                tile_grid0 = TileGrid(bitmap=logo_img, pixel_shader=logo_img.pixel_shader)
                tile_grid0.x = 0 # display.width // 2 - logo_img.width // 2
                tile_grid0.y = 20

            # Tielegrid to use in disp_logo()
            tile_grid1 = TileGrid(bitmap=logo_img, pixel_shader=logo_img.pixel_shader)
            tile_grid1.x = display.width // 2 - logo_img.width // 2
            tile_grid1.y = 20  # was: 20    (avatar size is 68 x 100 px)
            logo1_grp = myVars.read("logo1_grp")
            logo1_grp.append(tile_grid1)
            myVars.write("logo1_grp", logo1_grp)
            my_page_layout.add_content(logo1_grp, "Logo1")   # = group index # 0
            if my_debug:
                print(TAG+f"logo1_grp = {myVars.read("logo1_grp")}")
        elif _ == 1:
            tile_grid2 = TileGrid(bitmap=logo_img, pixel_shader=logo_img.pixel_shader)
            tile_grid2.x = display.width // 2 - logo_img.width // 2
            tile_grid2.y = 10 # was: 20  (but blinka size is: 100 x 117 px)
            logo2_grp = myVars.read("logo2_grp")
            logo2_grp.append(tile_grid2)
            myVars.write("logo2_grp", logo2_grp)
            my_page_layout.add_content(logo2_grp, "Logo2")  # = group index # 1
            if my_debug:
                print(TAG+f"logo2_grp = {myVars.read("logo2_grp")}")

    grp_lst = []
    for k in grp_dict.keys():
        grp_lst.append(k)
    if my_debug:
        print(TAG+"grp_lst={}".format(grp_lst), file=sys.stderr)

    le = len(grp_lst)
    if le > 0:
        for i in range(le):
            tmp_grp = displayio.Group()
            nr_items = grp_dict[grp_lst[i]]['nr_items']
            sc =       grp_dict[grp_lst[i]]['scale']
            vpi =      grp_dict[grp_lst[i]]['vpos_increase']
            if my_debug:
                print(TAG+"nr_items= {}, scale= {}, vpos_increase= {}".format(nr_items, sc, vpi), file=sys.stderr)
            for j in range(nr_items):
                #text_area = bitmap_label.Label(font, text='', scale=sc, color=0x00FF00, save_text=True)
                text_area = label.Label(terminalio.FONT, text='', x = 10, y = 10, scale=sc, color=0x00FF00, save_text=True)
                apt = grp_dict[grp_lst[i]]['anchor_point']
                if my_debug:
                    print(TAG+"j= {}, anchor_point= {}".format(j, apt), file=sys.stderr)
                #print(TAG+f"j= {j}, nr_items= {nr_items}")
                text_area.anchor_point = apt
                apos = (grp_dict[grp_lst[i]]['anchored_position'][0], grp_dict[grp_lst[i]]['anchored_position'][1] + (j*vpi))
                if my_debug:
                    print(TAG+"j= {}, anchored_position= {}".format(j, apos), file=sys.stderr)
                text_area.anchored_position = apos
                tmp_grp.append(text_area)
            if my_debug:
                for _ in range(len(tmp_grp)):
                    print(TAG+f"tmp_grp[{_}] {tmp_grp[_]}")
            if grp_lst[i] == 'xp':
                xp_grp = tmp_grp       # = group index # 2
                myVars.write("xp_grp", xp_grp)
                if my_debug:
                    print(TAG+f"xp_grp = {myVars.read("xp_grp")}")
                my_page_layout.add_content(xp_grp, "XPlane")  
            elif grp_lst[i] == 'ta1':      #  used by disp_id()
                ta1_grp = tmp_grp       # = group index # 3
                myVars.write("ta1_grp", ta1_grp)
                if my_debug:
                    print(TAG+f"ta1_grp = {myVars.read("ta1_grp")}")
                my_page_layout.add_content(ta1_grp, "ID")
            elif grp_lst[i] == 'ta2':      #  used by disp_author()
                ta2_grp = tmp_grp       # = group index # 4
                if use_avatar:
                    ta2_grp.append(tile_grid0)  # add the tilegrid containing the avatar.bmp
                myVars.write("ta2_grp", ta2_grp)
                if my_debug:
                    print(TAG+f"ta2_grp = {myVars.read("ta2_grp")}")
                my_page_layout.add_content(ta2_grp, "Author")
            elif grp_lst[i] == 'ba':        # used by disp_bat()
                # Setup the file as the bitmap data source
                ba_grp = tmp_grp       # = group index # 5
                myVars.write("ba_grp", ba_grp)
                if my_debug:
                    print(TAG+f"ba_grp = {myVars.read("ba_grp")}")
                #s = "myVars.read(\'ba_grp\') = {}".format(myVars.read("ba_grp"))
                my_page_layout.add_content(ba_grp, "Battery")
            elif grp_lst[i] == 'msg':      #  used by disp_msg()
                msg_grp = tmp_grp       # = group index # 6
                myVars.write("msg_grp", msg_grp)
                if my_debug:
                    print(TAG+f"msg_grp = {myVars.read("msg_grp")}")
                my_page_layout.add_content(msg_grp, "Message")
            elif grp_lst[i] == 'dt':      # used by disp_dt()
                dt_grp = tmp_grp       # = group index # 7
                myVars.write("dt_grp", dt_grp)
                if my_debug:
                    print(TAG+f"dt_grp = {myVars.read("dt_grp")}")
                my_page_layout.add_content(dt_grp, "Datetime")

        # add it to the group that is showing on the display
        main_grp.append(my_page_layout)
        if my_debug:
            for _ in range(len(main_grp)):
                print(TAG+f"main_grp[{_}]= {main_grp[_]}")
                for i in range(len(main_grp[_])):
                    print(TAG+f"main_grp[{_}][{i}]= {main_grp[_][i]}")
        myVars.write("main_grp", main_grp)

def get_options():
    TAG= tag_adjust("get_options(): ")
    m_grp = m_port = None
    hlp = None
    sHlp = ''
    sDme = ''
    sGs = ''
    dme = None
    gs = None
    for i in range(0, 1):
        if i == 0:
            sHlp = os.getenv("HELP") # secrets.get("HELP", None)
            if my_debug:
                print(TAG+"sHlp= \'{}\'".format(sHlp), file=sys.stderr)
            if sHlp is not None:
                hlp = int(sHlp)
                if hlp == True:
                    dg.usage()
                    return True

        if i == 1:
            sDme = os.getenv("lDME") # secrets.get("lDME", None) # Boolean
            sGs = os.getenv("lGROUNDSPEED") # secrets.get("lGROUNDSPEED", None) # Boolean
            assert(sDme is not None), f"settings.toml: lDME cannot be None. Got {sDme}"
            assert(sGs is not None), f"settings.toml: lGROUNDSPEED cannont be None. Got {sGs}"

            dme = int(sDme)
            gs = int(sGs)
            if dme == True:
                dg.dme3_or_gs = dme # The flag is set. We're going to display the DME3 frequency.
            elif gs == True:
                dg.dme3_or_gs = False  # The flag is cleared. We're going to display the groundspeed.

    return True


def setup():
    global lcd, uart, ssid, ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY, TIME_URL, location, tz_offset, author_lst, ssid, password, dg, dr
    TAG = tag_adjust("setup():")
    if my_debug:
        print(TAG+"...", file=sys.stderr)

    dg = XPlaneUdpDatagram()  # Create an instance of the XPlaneUdpDatagram class object
    #main(sys.argv[1:]
    dr = XPlaneDatarefRx()    # Create an instance of the XPlaneDatarefRx class object

    # Get our username, key and desired timezone
    ADAFRUIT_IO_USERNAME = os.getenv("ADAFRUIT_IO_USERNAME")
    ADAFRUIT_IO_KEY = os.getenv("ADAFRUIT_IO_KEY")
    location = os.getenv("timezone") # secrets.get("timezone", None)

    TIME_URL = "https://io.adafruit.com/api/v2/{:s}/integrations/".format(ADAFRUIT_IO_USERNAME)
    TIME_URL += "time/strftime?x-aio-key={:s}&tz={:s}".format(ADAFRUIT_IO_KEY, location)
    TIME_URL += "&fmt=%25Y-%25m-%25d+%25H%3A%25M%3A%25S.%25L+%25j+%25u+%25z+%25Z"
    #open_socket()

    # ['help', 'group=', 'port=', 'dme', 'gs', 'groundspeed']

    author_lst = []
    s = ''
    for _ in range(3):
        if _ == 0:
            s = os.getenv("AUTHOR1") #secrets.get("AUTHOR1", None)
        elif _ == 1:
            s = os.getenv("AUTHOR2") # secrets.get("AUTHOR2", None)
        elif _ == 2:
            s = os.getenv("AUTHOR3") # secrets.get("AUTHOR3", None)
        author_lst.append(s)
    if my_debug:
        print(TAG+"author_lst= {}".format(author_lst), file=sys.stderr)

    # This part copied from I:/PaulskPt/Adafruit_DisplayIO_FlipClock/Examples/displayio_flipclock_ntp_test2_PaulskPt.py
    lt = os.getenv("LOCAL_TIME_FLAG") #secrets.get("LOCAL_TIME_FLAG", None)
    if lt is None:
        use_local_time = False
    else:
        lt2 = int(lt)
        if my_debug:
            print("lt2= {}".format(lt2), file=sys.stderr)
        use_local_time = True if lt2 == 1 else False

    if use_local_time:
        location = os.getenv("timezone") # secrets.get("timezone", None)
        if location is None:
            location = 'Not set'
            tz_offset = 0
        else:
            tz_offset0 = os.getenv("tz_offset") # secrets.get("tz_offset", None)
            if tz_offset0 is None:
                tz_offset = 0
            else:
                tz_offset = int(tz_offset0)
    else:
        location = 'Etc/GMT'
        tz_offset = 0

    if use_wifi:
        if my_debug:
            wifi_lst = []
            wifi_ch = []
            wifi_rssi = []
            for network in wifi.radio.start_scanning_networks():
                if network.ssid not in wifi_lst:
                    wifi_lst.append(network.ssid)
                    wifi_ch.append(network.channel)
                    wifi_rssi.append(network.rssi)
            wifi.radio.stop_scanning_networks()
            le = len(wifi_lst)
            print(TAG+"Wifi.AuthMode = {}".format(wifi.AuthMode), file=sys.stderr)
            if le > 0:
                for _ in range(le):
                    print(TAG+"network ssid: \'{:25s}\', channel: {:2d}, rssi: {:5d}".format(wifi_lst[_], wifi_ch[_], wifi_rssi[_]), file=sys.stderr)
            # Cleanup
            wifi_lst = []
            wifi_ch = []
            wifi_rssi = []
        if wifi_is_connected():
            print(TAG+"WiFi already connected to: \'{}\'".format(ssid), file=sys.stderr)
        else:
            print(TAG+"Going to connect to WiFi SSID \'{}\' using PW: \'{}\' ...".format(ssid, password), file=sys.stderr)
            wifi.radio.connect(ssid, password)
            if wifi_is_connected():
                print(TAG+'WiFi now connected', file=sys.stderr)
    #check if any (former commandline) options were passed (in secrets.py)
    if not get_options():
        print(TAG+'Call to get_options() returned with fail')
        raise RuntimeError
    else:
        if my_debug:
            print(TAG+"cmd line options successfully loaded from file \'settings.toml\'", file=sys.stderr)

    create_groups()

def open_socket():
    global pool, requests
    TAG = tag_adjust("open_socket(): ")
    print(TAG+"Entering...")
    if pool is None:
        pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
    if not my_debug:
        print(TAG+f"pool = {pool}, requests = {pool}")

def free_socket():
    global pool, requests
    TAG = tag_adjust("free_socket(): ")
    print(TAG+"Entering...")
    try:
        requests._free_sockets()
    except exception as e:
        print(TAG+f"Error: {e}")
        raise

def wifi_connect():
    global ip, s_ip, pool, ssid, password
    TAG = tag_adjust("wifi_connect(): ")
    if my_debug:
        print(TAG+"Entering...")
    connected = False
    s2=''
    wifi_ip = os.getenv("WIFI_IP")
    wifi_netmask = os.getenv("WIFI_NETMASK")
    wifi_gateway = os.getenv("WIFI_GATEWAY")
    wifi_dns = os.getenv("WIFI_DNS")
    
    if pool is None:
        pool = make_pool()

    print(TAG+"Connecting to \'{}\'".format(ssid), file=sys.stderr)

    # Next lines added on 2023-03-31
    # See: https://github.com/adafruit/circuitpython/issues/6274
    # and: https://github.com/adafruit/circuitpython/pull/6441

    if wifi_is_connected():
        if s_ip == wifi_ip:
            print(TAG+'WiFi already connected and IP is wanted IP: {}'.format(s_ip), file=sys.stderr)
        else:
            print(TAG+'WiFi IP wanted= {}. WiFi IP current: {}'.format(wifi_ip, s_ip), file=sys.stderr)
            try:
                wifi.radio.stop_dhcp()
                # ipv4_address, ipv4_subnet, ipv4_gateway, (optional: ipv4_dns)
                wifi.radio.set_ipv4_address(
                    ipv4=ipaddress.ip_address(wifi_ip),
                    netmask=ipaddress.ip_address(wifi_netmask),
                    gateway=ipaddress.ip_address(wifi_gateway),
                    ipv4_dns=ipaddress.ip_address(wifi_dns)
                )
                wifi.radio.connect(ssid=ssid, password=password)
                pool = socketpool.SocketPool(wifi.radio)
            except OSError as e:
                print(TAG+'OSError {}'.format(e), file=sys.stderr)
            except Exception as e:
                print(TAG+'Error {}'.format(e), file=sys.stderr)
    else:
        try:
            wifi.radio.stop_dhcp()
            # ipv4_address, ipv4_subnet, ipv4_gateway, (optional: ipv4_dns)
            wifi.radio.set_ipv4_address(
                ipv4=ipaddress.ip_address(wifi_ip),
                netmask=ipaddress.ip_address(wifi_netmask),
                gateway=ipaddress.ip_address(wifi_gateway),
                ipv4_dns=ipaddress.ip_address(wifi_dns)
            )
            wifi.radio.connect(ssid=ssid, password=password)
            pool = socketpool.SocketPool(wifi.radio)
        except OSError as e:
            print(TAG+'OSError {}'.format(e), file=sys.stderr)
        except Exception as e:
            print(TAG+'Line 625. Error {}'.format(e), file=sys.stderr)

    if wifi_is_connected():
        connected = True
        s2 = ''
    else:
        s2 = "Not "

    print(TAG+"{}connected to: \'{}\'".format(s2, ssid), file=sys.stderr)

    if my_debug:
        print(TAG+"s_ip= \'{}\'".format(s_ip), file=sys.stderr)

    # Note PaulskPt 2023-03-31: after forcing DHCP to OFF, it seems that it is not possible to perform PING.
    # See discussion on: https://github.com/adafruit/circuitpython/pull/6441
    if use_ping and connected:
        if not pool:
            pool = socketpool.SocketPool(wifi.radio)
        #print(TAG+'type(pool)= {}'.format(type(pool)), file=sys.stderr)
        addr_idx = 1
        addr_dict = {0:'LAN gateway', 1:'google.com'}
        host_name = addr_dict[addr_idx]
        t = "Trying again to get addrinfo of: {}".format(host_name)
        info = None
        msg_shown = False
        for _ in range(1):
            try:
                info = pool.getaddrinfo(host_name, 80)
                if info is not None:
                    break
            except OSError as e:
                if not msg_shown:
                    print(TAG+f"pool.getaddrinfo(\'{host_name}\') OSError: {e}", file=sys.stderr)
                    print(TAG+t)
                    msg_shown = True
                else:
                    print(TAG+t)
                time.sleep(0.5)
        if info is not None:
            addr = info[0][4][0]
            print(TAG+"Resolved google address: \'{}\'".format(addr), file=sys.stderr)
            ipv4 = ipaddress.ip_address(addr)
            for _ in range(10):
                result = wifi.radio.ping(ipv4)
                if result:
                    print(TAG+"Ping google.com [{:s}]:{:.0f} ms".format(addr, result*1000), file=sys.stderr)
                    break
                else:
                    print(TAG+"Ping no response", file=sys.stderr)
                    
def ck_NTP():
    TAG = tag_adjust("ck_NTP(): ")
    ret = False
    dt = None
    if my_debug:
        print(TAG+"Entering...")
        print(TAG+f"ntp = {ntp}")
    
    if not wifi_is_connected():
        print(TAG+"Wifi was not connected. Going to connect...")
        wifi_connect()
    try:
        if ntp is not None:
            if not myVars.read("NTP_dt_is_set"):
                dt = ntp.datetime
                if dt:
                    rtc.datetime = dt
                    myVars.write("NTP_dt",dt)
                    myVars.write("NTP_dt_is_set", True)
                    if not my_debug:
                        mv_dt = myVars.read("NTP_dt")
                        print(TAG+f"myVars(\'NTP_dt\'): {mv_dt}")
            ret = True if dt is not None else False
        else:
            print(TAG+f"ntp = {ntp}")
    except OSError as e:
        print(TAG+f"Error: {e.strerror}. Errno: {e.errno}")
    return ret


def get_dt_AIO():
    global time_received, TIME_URL, kbd_intr
    TAG = tag_adjust("get_dt_AIO(): ")
    print(TAG+"Entering...")
    stop = False
    dst = ''
    if my_debug:
        print(TAG+"ip= {}".format(ip), file=sys.stderr)
    if not wifi_is_connected():
        wifi_connect()
    if wifi_is_connected():
        gc.collect()
        response = None
        open_socket()
        time.sleep(0.5)
        try_cnt = 0
        if my_debug:
            print(TAG+f"TIME_URL = \'{TIME_URL}\'")
        while response is None:
            try:
                if try_cnt >= 5:
                    print(TAG+f"failed to get timestamp from AIO. Tried {try_cnt} times. Exiting...")
                    stop = True
                    break
                response = requests.get(TIME_URL)
                print(TAG+f"response = {response}")
                if response:
                    n = response.text.find("error")
                    if n >= 0:
                        print(TAG+f"AIO returned an error: {response}")
                        try_cnt += 1
                    else:
                        break
            except OSError as exc:
                try_cnt += 1
                if try_cnt == 1:
                    print(TAG+f"OSError occurred: {exc}. Trying again. Wait...", file=sys.stderr, end='\n')
        try:
            if not stop and response:
                print(" " *tag_width+"-" * 47)
                print(TAG+"Time= ", response.text)
                print(" "*tag_width+"-" * 47)
                time_received = True
                s = response.text
                s_lst = s.split(" ")
                #print("s_lst= {}".format(s_lst), file=sys.stderr)
                n = len(s_lst)
                if n > 0:
                    dt1 = s_lst[0]
                    tm = s_lst[1]
                    yday = s_lst[2]
                    wday = s_lst[3]
                    tz = s_lst[4]
                    dst = -1  # we don't use isdst
                    yy =int(dt1[:4])
                    mo = int(dt1[5:7])
                    dd = int(dt1[8:10])
                    #print("tm= {}".format(tm), file=sys.stderr)
                    hh = int(tm[:2])
                    mm = int(tm[3:5]) # +mm_corr # add the correction
                    ss = int(round(float(tm[6:8])))
                    if my_debug:
                        print("ss= {}".format(ss), file=sys.stderr)
                    yd = int(yday) # day of the year
                    wd = int(wday)-1 # day of the week -- strftime %u (weekday base Monday = 1), so correct because CPY datetime uses base 0
                    #sDt = "Day of the year: "+str(yd)+", "+weekdays[wd]+" "+s_lst[0]+", "+s_lst[1][:5]+" "+s_lst[4]+" "+s_lst[5]
                    sDt = "Day of the year: {}, {} {} {} {} {}".format(yd, weekdays[wd], s_lst[0], s_lst[1][:5], s_lst[4], s_lst[5])
                    if my_debug:
                        print(TAG+"sDt= {}".format(sDt), file=sys.stderr)
                    # Set the internal RTC
                    tm2 = (yy, mo, dd, hh, mm, ss, wd, yd, dst)
                    if my_debug:
                        print(TAG+"tm2= {}".format(tm2), file=sys.stderr)
                    tm3 = time.struct_time(tm2)
                    if my_debug:
                        print(TAG+"dt1= {}".format(dt1), file=sys.stderr)
                        print(TAG+"yy ={}, mo={}, dd={}".format(yy, mm, dd), file=sys.stderr)
                        print(TAG+"tm2= {}".format(tm2), file=sys.stderr)
                        print(TAG+"tm3= {}".format(tm3), file=sys.stderr)
                    rtc.datetime = tm3 # set the built-in RTC
                    print(TAG+"built-in rtc synchronized with Adafruit Time Service date and time", file=sys.stderr)
                    if my_debug:
                        print(TAG+" Date and time splitted into:", file=sys.stderr)
                        for i in range(len(s_lst)):
                            print("{}: {}".format(i, s_lst[i]), file=sys.stderr)
                response.close()
                
        except OSError as exc:
            print(TAG+"OSError occurred: {}, errno: {}".format(exc, exc.args[0]), file=sys.stderr, end='\n')
        except KeyboardInterrupt:
            kbd_intr = True
        finally:
            free_socket()

# =======================================================
# Here were:                                            =
# - XPlaneIpNotFound class                              =
# - XPlaneTimout class                                  =
# - XPlaneDataref class                                 =
# - XPlaneUdpDatagram class                             =
# The first 3 classes moved to file XplaneDatarefRx.py  =
# The 4th class moved to file XPlaneUpdDatagram.py      =
# =======================================================

# =======================
#   Start of main()     =
# =======================

# by Paulsk
def main():
    global my_have_lcd, my_debug, SCRIPT_NAME, Hasseb_lcd, Loose_lcd, start_t, use_logo
    TAG = tag_adjust("main(): ")
    values = {}
    beacon = None
    my_UDP_sock = None
    data = []
    n = 0
    ln = 0
    t = ''
    t_grp = ''
    t_prt = 0
    o = a = None
    t_loop_begin = None
    
    # ===================+
    # Bypass several     |
    # functions          |
    speed_run = myVars.read("speed_run")
    # ===================+
    
    interval_t = 600  # 10 minutes
    # print("type(TAG)= {}".format(type(TAG)), file=sys.stderr)
    print(TAG+"Date time sync interval set to: {} minutes".format(int(float(interval_t//60))), file=sys.stderr)
    delay = 3
    setup()
    avatar = 1
    blinka = 2
    dt_shown = False
    cnt = 1
    kbdi = None
    stop = False
    opts = []
    do_dr_test = False
    do_dg_test = True
    start = myVars.read("start")
    start = True
    myVars.write("start", start)
    
    res = ck_NTP()
                        
    if my_debug:
        print("\n")
        myVars.list()  # Show all the global variables
        print("\n")

    if not my_debug:
        # print(TAG+'We entered main()', file=sys.stderr)
        print(TAG+'We are running Python version: {}.{}.{} '.format(sys.version_info[0], sys.version_info[1], sys.version_info[2]), file=sys.stderr)

    if my_have_lcd:
        global LCD_DISPLAYOFF, LCD_DISPLAYON, lcd

    t_max_time = 60 # max loop time in seconds
    t_loop_begin = time.time()

    use_udp_host = True if myVars.read("use_udp_host") == "1" else False
    if my_debug:
        print(TAG+'The following values will be used:', file=sys.stderr)
        if use_udp_host:
            print(TAG+'<IP-address> of this device: {}'.format(str(wifi.radio.ipv4_address)), file=sys.stderr)
            print(TAG+'and <Multicast Port>: {}'.format(myVars.read("multicast_port1")), file=sys.stderr)
        else:
            print(TAG+'<Multicast Group>: {}'.format(myVars.read("multicast_group2")), file=sys.stderr)
            print(TAG+'and <Multicast Port>: {}'.format(myVars.read("multicast_port2")), file=sys.stderr)

    if dg.dme3_or_gs:
        dme_gs_txt = 'dme3 frequency'
    else:
        dme_gs_txt = 'groundspeed'
    if my_debug:
        print(TAG+'The value of the dme3_or_gs flag is: \"{}\"'.format(dg.dme3_or_gs), file=sys.stderr)
        print(TAG+'So, we will display the: {}'.format(dme_gs_txt), file=sys.stderr)
    #sys.exit(2)

    try:

        """UDP/SOCK_DGRAM is a datagram-based protocol. You send one datagram and get one reply and then the connection terminates.
        The UDP echo client is similar the server, but does not use bind() to attach its socket to an address.
        It uses sendto() to deliver its message directly to the server, and recvfrom() to receive the response.
        This is an extract from X-Plane 11 log.txt while "Network data to log.txt" was activated in settings:
        SEND label=DATA to IP 192.168.1.103 port_int=49000. Length to sent=113
        We have loaded up 3 DATA structures, at size 36 each. A total of 108 bytes to send!
        RECV label=BECN, sent from IP=<IP of your X-Plane host PC>-<Port: 49707>, length after packaging removal=24"""

        if start:
            clr_disp()  # Clear the Window
            if speed_run:
                print(TAG+"We\'re doing a \'speed\' run. Not calling several functions like \'disp_bat()\'")
            else:
                if use_logo:
                    disp_logo(blinka) # (avatar or blinka)
            #display.refresh()
        gc.collect()
        if myVars.read("kbd_intr"):
            stop = True
            #break
        print('-'*89, file=sys.stderr)
        # NEO_pixel_test()
        curr_t = time.monotonic()
        elapsed_t = int(float(curr_t - start_t))
        start_t = curr_t
        if my_debug:
            print(TAG+"elapsed_t {}, interval_t =  {}".format(elapsed_t, interval_t), file=sys.stderr)
        if not speed_run:
            disp_id()
        # gc.collect()
        # First sync datetime with AIO Time Service and update the built-in RTC
        # ================================================================================

        if wifi_is_connected() and not myVars.read("NTP_dt_is_set"):
            tmod = elapsed_t % interval_t
            sync_dt = True if tmod <= 20 else False
            if not my_debug:
                print(TAG+f"sync_dt= {sync_dt}", file=sys.stderr)
            if sync_dt:  # leave a margin  # was: if (lapsed_t >= 20 and ...):
                print(TAG+f"dt_shown = {dt_shown}")
                if not dt_shown:
                    dt_shown = True
                    res = ck_NTP()
                    # gc.collect()
                    # time.sleep(0.1)
                    # get_dt_AIO()
                    print(TAG+f"result ck_NTP(): {res}")
                    if myVars.read("kbd_intr"):
                        stop = True
                        # break
                else:
                    dt_shown = False
        #time.sleep(delay)

        if start and not speed_run:
            disp_bat()
            gc.collect()

        #blink()
        """
        time.sleep(delay)
        if use_tmp_sensor:
            if temp_sensor_present:
                # disp_temp()
                if myVars.read("kbd_intr"):
                    stop = True
                    # break
                gc.collect()
                time.sleep(delay)
        """
        if start and not speed_run:
            disp_dt()
            time.sleep(delay)
            blink_NEO()
            time.sleep(delay)
            disp_author()
            #time.sleep(60)
            gc.collect()

            # change page by next page function. It will loop by default
            # my_page_layout.next_page()

            """
            while True:
                # Show the LCD init screen for 5 seconds
                t_elapsed = int(round(time.time() - t_loop_begin))
                # print(TAG+'t_elapsed= {}'.format(t_elapsed), file=sys.stderr)
                if t_elapsed >= 5:
                    break
            """
        """
        if not my_debug:
            print(TAG+'Calling dr.FindIp()', file=sys.stderr)
            while True:
                beacon = dr.FindIp() # Print beacon transmission info, if any rcvd
                t = type(beacon)
                print(TAG+'-- type(beacon) = {}'.format(t), file=sys.stderr)
                if not (t is None):
                    print(TAG+'-- beacon = {}'.format(beacon), file=sys.stderr)
                    break
        """
        # ================================================================================
        if not wifi_is_connected():
            wifi_connect()
        while True:
            myVars.write("main_loop_nr", cnt)
            myVars.write("kbd_intr", False)
            #if not my_debug:
            #    print(TAG+'Loop nr: {:03d}'.format(cnt), file=sys.stderr)
            if myVars.read("no_data"):
                stop = True
                break
            if not my_debug:
                print(TAG+'We are going to run a data{} test...'.format("ref" if do_dr_test else "gram" if do_dg_test else " ?"), file=sys.stderr)
            try:
                if do_dg_test:
                    if my_debug:
                        print(TAG+'type(dg)= {}'.format(type(dg)), file=sys.stderr)
                        print(TAG+'contents dg= {}'.format(dg), file=sys.stderr)
                    lResult = dg.datagram_test() # Do the datagram test. This also opens a DataRef socket
                    if not lResult:
                        print(TAG+'call to dg.datagram_test() failed', file=sys.stderr)
                        if myVars.read("no_data"):
                            print(TAG+f"reason: no data received for a while")
                        # raise RuntimeError
                    else:
                        print(TAG+'call to dg.datagram_test() successful', file=sys.stderr)
                        #print(TAG+'contents datagram = {}'.format(dg.retval), file=sys.stderr)
                    kbdi = myVars.read("kbd_intr")
                    if kbdi:
                        print(TAG+f"kbdintr = {kbdi}")
                        raise KeyboardInterrupt
                
                if do_dr_test:
                    print(TAG+'type(dr)= {}'.format(type(dr)), file=sys.stderr)
                    print(TAG+'contents dr= {}'.format(dr), file=sys.stderr)
                    if not dr.dataref_test(): # Do the dataref test. This also opens a DataRef socket
                        print(TAG+'call to dr.dataref_test() failed', file=sys.stderr)
                        # raise RuntimeError
                    else:
                        print(TAG+'call to dr.dataref_test() sucdessful', file=sys.stderr)

                if my_have_lcd:
                    dg.LCDFill() # Fill the LCD flight parameters frame

                #if my_have_tft:
                    # pass  # ToDo fill in
                #    dg.disp_hdg_alt()
                
                cnt += 1
                if cnt > 999:
                    cnt = 1

                kbdi = myVars.read("kbd_intr")
                if kbdi:
                    print(TAG+f"kbdintr = {kbdi}")
                    raise KeyboardInterrupt

            #except socket.timeout:
            except pool.timeout:
                # X-Plane 11 data output reception failed
                print('{} data output reception failed. Exiting script.\n'.format(XPlane_version), file=sys.stderr)
                break
                #sys.exit(1)
            except KeyboardInterrupt:
                print('\nKeyboardInterrupt occurred. Quitting script.\n', file=sys.stderr)
                break

            except Exception as e:
                print('Main() Error: {}'.format(e), file=sys.stderr) #[0], 'Message: ', e[1]
                raise
                # break

            # sys.exc_clear() # clear the internal traceback (see: https://cosmicpercolator.com/2016/01/13/exception-leaks-in-python-2-and-3/)

    except KeyboardInterrupt:
        stop = True
        # break

    # except Exception, msg:
    #    print('Main() - 1st try: - except block - exception error:\n', file=sys.stderr)
    #    print('Error: {}, 'Message: {}'.format(msg[0], msg[1]), file=sys.stderr)
    #    raise
    finally:
        if stop:
            print(TAG+"KeyboardInterrupt. Exiting...", file=sys.stderr)
            if my_have_lcd:
                lcd_init_time = time.time()
                if Hasseb_lcd:
                    lcd._set_display_enabled = LCD_DISPLAYOFF
                    lcd.clear()
                    lcd._set_display_enabled = LCD_DISPLAYON
                    #lcd.cursor_mode = crm.blink # set the cursor of the LCD to blink
                    lcd.cursor_mode = LCD_CURSOROFF | LCD_BLINKOFF # hide the cursor
                    # Display init text on LCD
                    lcd._set_cursor_pos((0, 0))
                    lcd.write_string(XPlane_version)
                    lcd._set_cursor_pos((1,0))
                    lcd.write_string('UDP Datagram client')
                elif Loose_lcd:
                    #lcd.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYOFF)
                    lcd.lcd_clear()
                    #lcd.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
                    #lcd.lcd_write(LCD_CURSOROFF) # hide the cursor
                    # Display init text on LCD
                    lcd.lcd_display_string(XPlane_version,1)

        #if use_logo:
        #    disp_logo(blinka) # display blinka
        #    gc.collect()

        if my_have_lcd:
            pass    # temporary put 'pass' here because the 2 lines below are commented-out for the moment
            dg.my_lcd_up()

        t = type(my_UDP_sock)
        if not (t is None):  # Check is my_socket exists
            pass
        else:
            print('We are going to close the socket.', file=sys.stderr)
            dg.CloseUDPSocket(my_UDP_sock) # Close the socket
            #print('We are doing final cleanup.', file=sys.stderr)
            #dg = None # Cleanup the instance
            #print('type(dg)= {}'.format(type(dg)), file=sys.stderr)
        try:
            sys.stdout.close()
        except:
            pass

        try:
            sys.stderr.close()
        except:
            pass

        try:
            sys.exit(0)
        except SystemExit:
            raise  # os._exit(0)


# =======================
#   End of main()       =
# =======================

if __name__ == "__main__":
    main()

### END OF THIS PYTHON SCRIPT ###
