#***************************************************************
#* Name:      LimeSDR_FPGA.py
#* Purpose:   Class implementing LimeSDR FPGA functions
#* Author:    Lime Microsystems ()
#* Created:   2016-11-24
#* Copyright: Lime Microsystems (limemicro.com)
#* License:
#**************************************************************

import numpy

# Try to import the LimeAPI library
try:
    from cyLimeLib import *
    cyLimeLibPresent = True
except:
    cyLimeLibPresent = False

class LimeSDR_FPGA(object):
    
    def __init__(self, spiRead, spiWrite, usb):
        """
        Initialize data structures.
        """
        self.spiRead = spiRead
        self.spiWrite = spiWrite
        self.usb = usb

    def getInfo(self):
        res = self.spiRead([0, 1, 2])
        boardID = res[0]
        gwFunction = res[1]
        gwRevision = res[2]
        return (boardID, gwFunction, gwRevision)
        
    def strInfo(self):
        boardID, gwFunction, gwRevision = self.getInfo()
        res = ""
        res += "Board ID         : "+str(boardID)+"\n"
        res += "GW Function      : "+str(gwFunction)+"\n"
        res += "GW Revision      : "+str(gwRevision)+"\n"
        return res                


