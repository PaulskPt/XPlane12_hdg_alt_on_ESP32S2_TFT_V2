# _*_ coding: utf-8 _*_
# SPDX-FileCopyrightText: 2024 Paulus Schulinck @PaulskPt
#
# SPDX-License-Identifier: MIT
##############################
#
# Extracted from @PaulskPt's XPlaneUdpDatagramLCD.py
# Ver 11, 2019-08-13 10h22 UTC
# See: # Original see: I:\Raspberry_Pi\XPlane_datarefs\xp_data_outp_rx\XPlaneUdpDatagramLCDv11.py
#
# Class to get UDP Datagram packets from X-Plane 11 Flight Simulator via a (local area) network.
#
# Original idea for the X-Plane UDP Data Output receiver, "XPlaneUdp.py", by charlylima
# See: https://github.com/charlylima/XPlaneUDP
# Charlylima's python script was to detect BECN packets and then to ask and receive DataRef packets.
#
# This python script is a modified and extended version of Charlylima's script.
# The target of this script is to detect UDP Datagram packets, sent by an X-Plane host to a Multicast group (LAN).
# The script also has a RaspiCheckCPUTemp Class to retrieve and print on the LCD the temperature of the CPU.
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
#
#
# Update 2023-10-23: 
# See lines 320 and 322: Advice from: @aceg00 (https://gist.github.com/todbot/877b2037b6c7b2c4c11545c83c6e2182) to prevent printing unwanted characters
#
# 2023-02-08 On Github I openend Issue https://github.com/adafruit/circuitpython/issues/7556
# 2024-01-22 I closed the issue #7556 because my request was fulfilled.
# 2023-03-27, Adapted for an Adafruit Feather ESP32-S2 TFT
# 2024-01-22 Updated the repo on Github for use with X-Plane 12
#
#type:ignore
from common import *
import struct
import sys
import binascii
#import socketpool

# Class downloaded from Charlylima
class XPlaneIpNotFound(Exception):
  args="Could not find any running XPlane instance in network."

# Class downloaded from Charlylima
class XPlaneTimeout(Exception):
  args="XPlane timeout."

# Class created by Paulsk, content almost all by Charlylima
class XPlaneDatarefRx():

    def __init__(self):
        TAG = tag_adjust("dr.__init__(): ")
        self.my_DataRef_sock = None

        # list of requested datarefs with index number
        self.datarefidx = 0
        self.datarefs = {} # key = idx, value = dataref
        self.values = {}
        self.headerlen = 4
        self.packet_length = 191
        self.packet = {}

        #self.MCAST_GRP = "239.255.1.1"
        #self.MCAST_PORT = 49707
        self.UDP_PORT = 49000

        self.udp_host = str(wifi.radio.ipv4_address)
        self.use_udp_host = True if myVars.read("use_udp_host") == "1" else False
        print(TAG+'self.use_udp_host= {}'.format(self.use_udp_host), file=sys.stderr)
        if self.use_udp_host:
            self.MCAST_GRP = myVars.read("multicast_group1")
            self.MCAST_PORT = myVars.read("multicast_port1")
        else:
            self.MCAST_GRP = myVars.read("multicast_group2")
            self.MCAST_PORT = myVars.read("multicast_port2")
        if not my_debug:
            print(TAG+'self.MCAST_GRP= {}'.format(self.MCAST_GRP), file=sys.stderr)
            print(TAG+'self.MCAST_PORT= {}'.format(self.MCAST_PORT), file=sys.stderr)

        # values from xplane
        self.BeaconData = {}
        self.xplaneValues = {}
        self.defaultFreq = 1

    # Function created by Charlylima
    def __del__(self):
        TAG = tag_adjust("dr.__del__(): ")
        for i in range(len(self.datarefs)):
            self.AddDataRef(next(iter(self.datarefs.values())), freq=0)
        # Next line additions by Paulsk for type-checking and thus avoiding an AttributeError
        t = type(self.my_DataRef_sock)

        if not t is None:
            if my_debug:
               print(TAG+'type(my_DataRef_sock) = {}'.format(t), file=sys.stderr)
            pass
        else:
            if my_debug:
                print(TAG+'Closing my_DataRef_sock', file=sys.stderr)
            self.my_DataRef_sock.close()

    # The socket definitions in function OpenDatarefSocket() weere before inside FindIp()
    def OpenDatarefSocket(self):
        global pool
        TAG = tag_adjust("dr.OpenDatarefSocket: ")
        # Open a UDP Socket to receive on Port 49000
        if not my_debug:
            print(TAG+'We are going to open a socket for Dataref request and answers', file=sys.stderr)

        print(TAG+'type(pool)= {}'.format(type(pool)), file=sys.stderr)
        if pool is None:
            pool = make_pool()
            print(TAG+'type(pool) (after call to make_pool())= {}'.format(type(pool)), file=sys.stderr)
        if pool is not None:
            self.my_DataRef_sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
            #self.my_DataRef_sock.settimeout(3.0)
            if my_debug:
                print(TAG+'type(self.my_DataRef_sock= {})'.format(self.my_DataRef_sock), file=sys.stderr)
        else:
            raise ValueError(f"pool must be not None. Got {pool}")

    # Function created by Paulsk
    def CloseDatarefSocket(self): # , socket):
        #self.my_DataRef_sock = socket
        self.my_DataRef_sock.close()

    def GetDatarefSocket(self):
        return self.my_DataRef_sock

    # Function created by Charlylima
    def AddDataRef(self, dataref, freq = None):
        global my_debug
        '''
        Configure XPlane to send the dataref with a certain frequency.
        You can disable a dataref by setting freq to 0.
        '''
        TAG = tag_adjust("dr.AddDataRef: ")
        if my_debug:
            print(TAG+'We are going to add the following X-Plane DataRef(s):', file=sys.stderr)
            print(TAG+'DataRef: {}\n'.format(dataref), file=sys.stderr)
        idx = -9999

        if freq == None:
          freq = self.defaultFreq

        if dataref in self.datarefs.values():
          idx = list(self.datarefs.keys())[list(self.datarefs.values()).index(dataref)]
          if freq == 0:
            if dataref in self.xplaneValues.keys():
              del self.xplaneValues[dataref]
            del self.datarefs[idx]
        else:
          idx = self.datarefidx
          self.datarefs[self.datarefidx] = dataref
          self.datarefidx += 1

        cmd = b"RREF\x00"
        string = dataref.encode()
        message = struct.pack("<5sii400s", cmd, freq, idx, string)
        assert(len(message)==413)
        t = type(self.my_DataRef_sock)
        if my_debug:
            print(TAG+'We are going to sent a DataRef request to:', self.BeaconData["IP"], ', Port: {}'.format(self.UDP_PORT), file=sys.stderr)
            print(TAG+'Message to send: {}, the cmd = {}'.format(message, binascii.hexlify(cmd)), file=sys.stderr)
            print(TAG+'Type of the self.my_DataRef_sock = {}'.format(t), file=sys.stderr)

        self.my_DataRef_sock.sendto(message, (self.BeaconData["IP"], self.UDP_PORT))

    # Function created by Charlylima
    def GetValues(self):
        TAG = tag_adjust("dr.GetValues: ")
        try:
            #if my_debug:
            #    print('dr.GetValues() -- We are entering GetValues', file=sys.stderr)
            # Receive packet
            data, addr = self.my_DataRef_sock.recvfrom(1024) # buffer size is 1024 bytes
            # Decode Packet
            retvalues = {}
            # * Read the Header "RREF".
            header=data[0:4]
            if (header==b"DATA"): # 2 lines added by Paulsk. The DATA packets we handle in another function
                pass
            elif (header==b"RREF"):
                # * We get 8 bytes for every dataref sent:
                #   An integer for idx and the float value.
                values =data[5:]
                lenvalue = 8
                numvalues = int(len(values)/lenvalue)
                #if my_debug:
                #    print('values of data packet = {}'.format(values), file=sys.stderr)
                #    print('number of values = {}'.format(numvalues), file=sys.stderr)
                for i in range(0,numvalues):
                    singledata = data[(5+lenvalue*i):(5+lenvalue*(i+1))]
                    (idx,value) = struct.unpack("<if", singledata)
                    #if my_debug:
                    #    print('value (unpacked) = {}'.format(value), file=sys.stderr)
                    if idx in self.datarefs.keys():
                       # convert -0.0 values to positive 0.0
                       if value < 0.0 and value > -0.001 :
                           value = 0.0
                    retvalues[self.datarefs[idx]] = value
                    #if my_debug:
                    #    print('retvalues = {}'.format(retvalues), file=sys.stderr)
            else:
                # if(header!=b"RREF,"): # (was b"RREFO" for XPlane10)
                print(TAG+'Unknown packet: {}'.format(binascii.hexlify(data)), file=sys.stderr) # Unknown packet: 525245462c0000000000582c460100000000000000  -- Note Paulsk: 42 digits
            self.xplaneValues.update(retvalues)
        except:
            raise XPlaneTimeout()
        if my_debug:
            print(TAG+'Exiting and returning self.xplaneValues: {}\n'.format(self.xplaneValues), file=sys.stderr)
        return self.xplaneValues


    def packet_has_data(self, packet):
        TAG = tag_adjust("dg.packet_has_data(): ")
        b_cnt = 0
        le = len(packet)
        if not my_debug:
            print(TAG+'packet contents= {}'.format(packet), file=sys.stderr)
        if le >= 0:
            for _ in range(le):
                if not my_debug:
                    print(TAG+'value byte nr {} is {}'.format(_, packet[_]), file=sys.stderr)
                if packet[_] == 0:
                    b_cnt += 1
                if b_cnt > 5:
                    if not my_debug:
                        print(TAG+'{} nr of 0x00 bytes found. Packet doesn\'t contain data.'.format(b_cnt), file=sys.stderr)
                    return False
        return True

    # Function created by Charlylima
    def FindIp(self):
        global pool
        '''
        Find the IP of XPlane Host in the Local Area Network.
        It takes the first one it can find.
        '''
        TAG = tag_adjust("dr.FindIp(): ")
        self.BeaconData = {}

        # open socket for multicast group.

        try:
            if pool is None:
                make_pool()
            if pool is None:
                raise ValueError(f"pool must be not None. Got {pool}")

            self.my_DataRef_sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM) # SocketPool has no attribute IPPROTO_UDP !!!
            #self.my_DataRef_sock.settimeout(5)
            #self.my_DataRef_sock.setblocking(True)

            if my_debug:
                print(TAG+'type(self.my_DataRef_sock)= {}'.format(type(self.my_DataRef_sock)), file=sys.stderr)

            #self.my_DataRef_sock.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
            ###    self.my_DataRef_sock.bind((self.MCAST_GRP, self.MCAST_PORT))     <<<<=====================
            self.my_DataRef_sock.bind((self.udp_host, self.MCAST_PORT))

            #self.my_DataRef_sock.connect((self.MCAST_GRP, self.MCAST_PORT))

            if not my_debug:
                print(TAG+'type(self.BeaconData)= {}'.format(type(self.BeaconData)), file=sys.stderr)
                print(TAG+'self.BeaconData= {}'.format(self.BeaconData), file=sys.stderr)
        except ValueError as e:
            print(TAG+'Error: {}'.format(e), file=sys.stderr)
            raise
        except Exception as e:
            print(TAG+'Error: {}'.format(e), file=sys.stderr)
            raise

        # frame_fmt = "4sl"
        packet_size = 71 # dec 61 = hex 0x3D -- dec 181 = hex 0xB5      struct.calcsize(frame_fmt)
        print(TAG+'packet_size= {}'.format(packet_size), file=sys.stderr)
        packet = bytearray(packet_size)  # stores our incoming packet

        if not my_debug:
            # print(TAG+'packet= {}'.format(packet), file=sys.stderr)
            #print(TAG+'waiting for beacon packets, group {}, port {}'.format("192.168.1.96", self.MCAST_PORT), file=sys.stderr)
            print(TAG+'waiting for beacon packets, udp_host {}, port {}'.format(self.udp_host, self.MCAST_PORT), file=sys.stderr)

        while True: # le_BeaconData == 0:
            # receive data
            try:
                # From Wireshark capture:
                # Frame 499: 61 bytes on wire (488 bits), 61 bytes captured (488 bits) on interface \Device\NPF_Loopback, id 0 Null/Loopback

                #size = self.my_DataRef_sock.recv_into(packet)  # ToDo: solve the 'hanging' of this command !!!

                size, addr = self.my_DataRef_sock.recvfrom_into(packet)

                # Convert packet header (bytearray) to string
                header0 = packet[:self.headerlen]
                if my_debug:
                    print(TAG+'header0 = {}'.format(header0), file=sys.stderr)
                header = ''
                for _ in range(len(header0)):
                    header += chr(header0[_])
                print(TAG+'header= {}'.format(header), file=sys.stderr)

                print(TAG+'nr bytes received= {} from {}'.format(size, addr[0]), file=sys.stderr)

                if my_debug:
                    print(TAG+'Received packet (raw) {}'.format(packet), file=sys.stderr)
                # msg = packet.decode('utf-8')  # assume a string, so convert from bytearray
                # Advice from: @aceg00 (https://gist.github.com/todbot/877b2037b6c7b2c4c11545c83c6e2182) to prevent printing unwanted characters
                # msg = packet.decode[:size]('utf-8')  # assume a string, so convert from bytearray
                #print(TAG+'Received packet from {}, packet {},\n size {}'.format(addr[0], packet, size), file=sys.stderr)

                #packet, sender = self.my_DataRef_sock.recvfrom(packet_size)  # was (15000)
                #print(TAG+'packet= \'{}\', sender= {}'.format(packet, sender[0]), file=sys.stderr)
                # decode data
                # * Header

                # Strip unused bytes:
                # If packet_size = 61 then the sliced size will be 29 (0x3D - 0x20 = 0x1D = dec 21 )

                if header == 'DATA': # 2 lines added by Paulsk. The DATA packet we handle in the XPlaneUdpDatagram Class object.
                    # pass
                    break
                elif header == 'BECN':
                    blink_NEO_color(neo_led_green) # blink the Neopixel led in green (see: common.py)
                    data = packet[5:21]
                    print(TAG+'first 8 bytes of data= {}'.format(data[:8]), file=sys.stderr)

                    if not my_debug:
                        print(TAG+'Entering...', file=sys.stderr)
                        print('packet header = {}'.format(header), file=sys.stderr)
                        #print('packet received = {}'.format(packet), file=sys.stderr)
                        print('packet data part = {}'.format(data), file=sys.stderr)
                    # * Data
                    # data = msg[5:]  # was: packet[5:21]
                    # struct becn_struct
                    # {
                    # 	uchar beacon_major_version;		// 1 at the time of X-Plane 10.40
                    # 	uchar beacon_minor_version;		// 1 at the time of X-Plane 10.40
                    # 	xint application_host_id;		// 1 for X-Plane, 2 for PlaneMaker
                    # 	xint version_number;			// 104014 for X-Plane 10.40b14 - 113201 for X-Plane 11.32
                    # 	uint role;				        // 1 for master, 2 for extern visual, 3 for IOS
                    # 	ushort port;				    // port number X-Plane is listening on
                    # 	xchr	computer_name[strDIM];  // the hostname of the computer
                    # };
                    beacon_major_version = 0
                    beacon_minor_version = 0
                    application_host_id = 0
                    xplane_version_number = 0
                    role = 0
                    port = 0
                    (
                      beacon_major_version,  # 1 at the time of X-Plane 10.40
                      beacon_minor_version,  # 1 at the time of X-Plane 10.40, 2 at the time of X-Plane 11
                      application_host_id,   # 1 for X-Plane, 2 for PlaneMaker
                      xplane_version_number, # 104014 for X-Plane 10.40b14 - 113201 for X-Plane 11.32
                      role,                  # 1 for master, 2 for extern visual, 3 for IOS
                      port,                  # port number X-Plane is listening on
                    ) = struct.unpack("<BBiiIH", data)


                    if my_debug:
                        print('beacon_major_version = {}'.format(beacon_major_version), file=sys.stderr)
                        print('beacon_minor_version = {}'.format(beacon_minor_version), file=sys.stderr)
                        print('application_host_id = {}'.format(application_host_id), file=sys.stderr)

                    # Originally beacon_minor_version was checked for a value of 1 but investigation by Paulsk revealed that X-Plane 11 returns a value of  2
                    computer_name = packet[21:-1]   # packet[21:-1]
                    if beacon_major_version == 1 \
                       and beacon_minor_version == 2 \
                       and application_host_id == 1:
                        self.BeaconData["IP"] = sender[0]
                        self.BeaconData["Port"] = port
                        self.BeaconData["hostname"] = computer_name.decode()
                        self.BeaconData["XPlaneVersion"] = xplane_version_number
                        self.BeaconData["role"] = role

                        if not my_debug:
                            print('\n'+TAG+'-- Beacon UDP packet received:', file=sys.stderr)
                            print('Host IP         = {}'.format(self.BeaconData["IP"]), file=sys.stderr)
                            print('Port            = {}'.format(self.BeaconData["Port"]), file=sys.stderr)
                            print('Hostname        = {}'.format(self.BeaconData["hostname"]), file=sys.stderr)
                            print('X-Plane version = {}'.format(self.BeaconData["XPlaneVersion"]), file=sys.stderr)
                            print('Role            = {}'.format(self.BeaconData["role"]), file=sys.stderr)

                    le_BeaconData = len(self.BeaconData)
                    if not my_debug:
                        print(TAG+'le_BeaconData= {}'.format(le_BeaconData), file=sys.stderr)
                    if le_BeaconData > 0:
                        break
                else:
                    print(TAG+'-- Unknown packet from {]'.format(sender[0]), file=sys.stderr)
                    print('{} bytes'.format(str(len(packet))), file=sys.stderr)
                    print(packet, file=sys.stderr)
                    print(binascii.hexlify(packet), file=sys.stderr)

            except self.my_DataRef_sock.timeout:
                print(TAG+'UDP rx socket timed out', file=sys.stderr)
                raise XPlaneIpNotFound()
            except OSError as e:
                if e.errno == 11:
                    print(TAG+'Resource temporarily unavailable (EAGAIN)', file=sys.stderr)
                else:
                    print(TAG+'OSError {}'.format(e), file=sys.stderr) # [Errno 11] EAGAIN
            except KeyboardInterrupt:
                myVars.write("kbd_intr", True)

        #self.my_DataRef_sock.setblocking(False)
        self.my_DataRef_sock.close()
        return self.BeaconData

    # Idea to put the content of this function in a separate function by Paulsk
    # content by Charlylima
    def dataref_test(self):
        TAG= tag_adjust("dr.dataref_test(): ")
        nCnt = 0
        if my_debug:
            print(TAG+'Entering...')
        self.OpenDatarefSocket() # Open the socket
        if my_debug:
            print(TAG+'type(self.my_DataRef_sock)= {} '.format(type(self.my_DataRef_sock)), file=sys.stderr)
        if self.my_DataRef_sock is None:
            return False
        try:
            beacon = self.FindIp()
            if beacon == {}:
                print(TAG+f"beacon: {beacon}", file=sys.stderr)
                return True
            if my_debug:
                print('{}\n'.format(beacon), file=sys.stderr)

            self.AddDataRef("sim/flightmodel/position/indicated_airspeed", freq=1)
            #self.AddDataRef("sim/flightmodel/position/latitude")
            #self.AddDataRef("sim/cockpit/radios/dme_freq_hz", freq=1)  # return an int
            #self.AddDataRef("sim/cockpit2/radios/indicators/dme_has_dme") # Is there a DME signal from standalone DME? 1 if yes, 0 if no. Returns an int

            # 2023-02-07 DataRefs selected with DataRefTool:
            # sim/flightmodel/position/longitude
            # sim/flightmodel/position/latitude
            # sim/flightmodel/position/groundspeed
            # sim/flightmodel/position/elevation

            while True:
                try:
                    values = self.GetValues()
                    le = len(values)
                    nCnt = nCnt + 1
                    if not my_debug:
                        print(TAG+'nr: {} -- len(values) = {}'.format(nCnt, le), file=sys.stderr)
                        print(TAG+'values received = {}\n'.format(values), file=sys.stderr)
                except XPlaneTimeout:
                    print(TAG+'XPlane Timeout', file=sys.stderr)
                    raise XPlaneTimeout() # (alteration by Paulsk because we have the Class raise XPlaneTimeout

        except XPlaneIpNotFound:
            print(TAG+'XPlane IP not found. Probably there is no XPlane running in your local network.', file=sys.stderr)
            raise XPlaneIpNotFound()
        except KeyboardInterrupt:
                myVars.write("kbd_intr", True)

        finally:
            self.CloseDatarefSocket() # (self.my_DataRef_sock) # Close the socket
            #self.__del__() # Cleanup initiated dataref objects -- NOT SURE IF I NEED TO CALL THIS FUNCTION.
            return True
