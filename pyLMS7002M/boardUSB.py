#***************************************************************
#* Name:      boardUSB.py
#* Purpose:   Class implementing board USB functions
#* Author:    Lime Microsystems ()
#* Created:   2016-11-24
#* Copyright: Lime Microsystems (limemicro.com)
#* License:
#**************************************************************

import usb.core
import usb.util

class boardUSB(object):
    
    def __init__(self):
        """
        Initialize USB.
        """
        self.dev = None
        self.timeout = 10

    @staticmethod
    def findLMS7002():
        dev = usb.core.find(idVendor=0x04b4, idProduct=0x00f1)
        if dev==None:
            dev = usb.core.find(idVendor=0x1d50, idProduct=0x6108)
        return dev

    def getEndpoints(self):
        """
        Return device endpoints
        """
        configurations = self.dev.configurations()
        conf = configurations[0]
        interfaces = conf.interfaces()
        interface = interfaces[0]
        endpoints = interface.endpoints()
        ep = []
        for endpoint in endpoints:
            ep.append(endpoint.bEndpointAddress)
        return ep
        
    def setDevice(self, dev):
        """
        Set the USB device.
        """
        self.dev = dev

    def findDevice(self, idVendor=0x04b4, idProduct=0x00f1):
        """
        Find the USB device with given VID and PID
        """
        self.dev = usb.core.find(idVendor, idProduct)
        return self.dev

    def setConfiguration(self):
        """
        Set the device configuration
        """
        self.dev.set_configuration()

    def controlTransfer(self, bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength = None, timeout = None):
        """
        USB control transfer
        """        
        return self.dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data_or_wLength, timeout)

    def bulkWrite(self, endpoint, data, timeout=None):
        """
        USB bulk write
        """
        return self.dev.write(endpoint, data, timeout=None)

    def bulkRead(self, endpoint, nBytes, timeout=None):
        """
        USB bulk read
        """
        return self.dev.read(endpoint, nBytes, timeout)
        
    def closeDevice(self):
        """
        Close USB device
        """
        # https://www.mail-archive.com/pyusb-users@lists.sourceforge.net/msg00624.html
        usb.util.dispose_resources(self.dev)
        self.dev = None
        
