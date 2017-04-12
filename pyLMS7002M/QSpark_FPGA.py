#***************************************************************
#* Name:      QSpark_FPGA.py
#* Purpose:   Class implementing QSpark FPGA functions
#* Author:    Lime Microsystems ()
#* Created:   2016-11-24
#* Copyright: Lime Microsystems (limemicro.com)
#* License:
#**************************************************************

import numpy

class QSpark_FPGA(object):
    
    def __init__(self, spiRead, spiWrite, usb):
        """
        Initialize data structures.
        """
        self.spiRead = spiRead
        self.spiWrite = spiWrite
        self.usb = usb
        self.MIMO = False
        self.format = "STREAM_12_BIT_COMPRESSED"
        self.samples = { "A" : IQSamples(),
                         "B" : IQSamples()
                       }

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

    #
    # Waveform functions
    #
            
    def readWFM(self, fileName, channel='A'):
        """
        Read samples from WFM file to the specified channel
        """        
        with open(fileName, mode='rb') as file:
            data = file.read()
        i=0
        isamples = [0]*int(len(data)/2)
        qsamples = [0]*int(len(data)/2)
        while i<len(data)/4:
            if data[4*i]>0x7f:
                isam = -1*(1<<15)+(ord(data[4*i])<<8)+ord(data[4*i+1])
            else:
                isam = (ord(data[4*i])<<8)+ord(data[4*i+1])
            if data[4*i+2]>0x7f:
                qsam = -1*(1<<15)+(ord(data[4*i+2])<<8)+ord(data[4*i+3])
            else:
                qsam = (ord(data[4*i+2])<<8)+ord(data[4*i+3])
            isamples[i] = isam/4    # Reduce to 12 bits
            qsamples[i] = qsam/4    # Reduce to 12 bits
            i += 1
        self.samples[channel].I = isamples
        self.samples[channel].Q = qsamples

    def uploadWFM(self):
        """
        Uploads samples to FPGA for waveform playback.
        If MIMO = False only channel A samples are uploaded, and zeros to channel B
        """
        self.spiWrite([(0x000C, 0x03)]) # channels 0,1
        self.spiWrite([(0x000E, 0x02)]) # 12 bit samples
        self.spiWrite([(0x000D, 0x04)]) # WFM_LOAD
        
        toSend = self.samples2FPGAPacket()        
        cmdWFMLoad = 1<<5
        while len(toSend)>0:
            if len(toSend)>4080:
                packet = toSend[0:4080]
                toSend = toSend[4080:]
            else:
                packet = toSend
                toSend = []
            self.bulkSend(cmdWFMLoad, packet)

    def samples2FPGAPacket(self):
        """
        Pack samples to FPGA payload packet format.
        Returns an array with packed FPGA payload.
        """
        format = self.format
        chCount = 2
        isamplesA = self.samples['A'].I
        qsamplesA = self.samples['A'].Q
        isamplesB = self.samples['B'].I
        qsamplesB = self.samples['B'].Q

        if format=="STREAM_12_BIT_COMPRESSED":
            frameSize = 3
            stepSize = frameSize * 2
            res = [0]*int(stepSize*len(isamplesA))
            pos = 0
            for i in range(0, len(isamplesA)):
                res[pos] = isamplesA[i] & 0xFF
                res[pos+1] = ((isamplesA[i]>>8) & 0xFF) | ((qsamplesA[i]<<4) & 0xF0)
                res[pos+2] = (qsamplesA[i] >> 4) & 0xFF
                if self.MIMO:
                    res[pos+3] = isamplesB[i] & 0xFF
                    res[pos+4] = ((isamplesB[i]>>8) & 0xFF) | ((qsamplesB[i]<<4) & 0xF0)
                    res[pos+5] = (qsamplesB[i] >> 4) & 0xFF
                else:
                    res[pos+3] = 0
                    res[pos+4] = 0
                    res[pos+5] = 0
                pos += stepSize
        elif format=="STREAM_12_BIT_IN_16":
            frameSize = 4
            stepSize = frameSize * 2
            res = [0]*int(chCount*stepSize*len(isamples))
            for i in range(0, len(isamples)):
                res[pos] = isamplesA[i] & 0xFF
                res[pos+1] = (isamplesA[i]>>8) & 0xFF
                res[pos+2] = qsamplesA[i] & 0xFF
                res[pos+3] = (qsamplesA[i] >> 8) & 0xFF
                if self.MIMO:
                    res[pos+4] = isamplesB[i] & 0xFF
                    res[pos+5] = (isamplesB[i]>>8) & 0xFF
                    res[pos+6] = qsamplesB[i] & 0xFF
                    res[pos+7] = (qsamplesB[i] >> 8) & 0xFF
                else:
                    res[pos+4] = 0
                    res[pos+5] = 0
                    res[pos+6] = 0
                    res[pos+7] = 0
                pos += stepSize        
        else:
            raise ValueError("Format must be 'STREAM_12_BIT_COMPRESSED' or 'STREAM_12_BIT_IN_16'")
        return res            

    #
    # USB I/O
    #

    def bulkSend(self, command, data):
        """
        Sends data to FPGA via synchronous bulk USB transfer
        """
        if len(data)>4080:
            raise ValueError("Max packet size is 4080, given "+str(len(data))+" bytes")
        packet = [0]*4096
        packet[0] = command
        packet[1] = (len(data)>>8) & 0xFF
        packet[2] = len(data) & 0xFF
        
        for i in range(0, len(data)):
            packet[16+i] = data[i]
        
        n = self.usb.bulkWrite(1, packet, self.usb.timeout)
        if n!=len(packet):
            raise IOError("Bulk transfer failed")

class IQSamples(object):
    def __init__(self):
        self._I = None
        self._Q = None

    @property
    def I(self):
        return self._I
        
    @I.setter
    def I(self, value):
        self._I = value
        
    @property
    def Q(self):
        return self._Q
        
    @I.setter
    def Q(self, value):
        self._Q = value
   
    @property
    def Complex(self):
        """
        Return array of I+j*Q
        """
        ni = len(self.I)
        nq = len(self.Q)
        if ni!=nq:
            raise ValueError("Number of I and Q samples must be equal")
        res = numpy.array(self.I, dtype=complex)
        res.imag = self.Q
        return res
        
