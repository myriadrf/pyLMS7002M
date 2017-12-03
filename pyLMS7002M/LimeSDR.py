#***************************************************************
#* Name:      LimeSDR.py
#* Purpose:   Class implementing LimeSDR functions
#* Author:    Lime Microsystems ()
#* Created:   2016-11-14
#* Copyright: Lime Microsystems (limemicro.com)
#* License:
#**************************************************************

from weakproxy import *
from copy import copy
from LMS7002 import *
from ADF4002 import *
from Si5351 import *
from boardUSB import *
from LimeSDR_FPGA import *
from timeit import default_timer as timer
import atexit

# Try to import the LimeAPI library
try:
    from cyLimeLib import *
    cyLimeLibPresent = True
except:
    cyLimeLibPresent = False    
    
class LimeSDR(object):

    def __init__(self, fRef = 30.72e6, verbose=0, usbBackend=None):
        """
        Initialize communication with LimeSDR.
        The value of usbBackend determines the type of connection:
            None - try with LimeAPI, fallback to PyUSB
            LimeAPI - only use LimeAPI
            PyUSB - only use PyUSB
        """
        if usbBackend==None:
            if cyLimeLibPresent:
                self.usbBackend = "LimeAPI"
            else:
                self.usbBackend = "PyUSB"
        else:
            if usbBackend == "LimeAPI" or usbBackend=="PyUSB":
                self.usbBackend = usbBackend
            else:
                raise ValueError("Unknown USB backend given : "+str(usbBackend))
        if self.usbBackend=="PyUSB":
            self.usb = boardUSB()
            dev = self.findLMS7002(self.usbBackend)
            if dev is None:
                raise ValueError("LimeSDR not found")
            self.usb.setDevice(dev)
        else:
            boards = cyLimeLib.getDeviceList()
            if len(boards)==0:
                raise ValueError("LimeSDR not found")
            self.cyDev = None
            for i in range(0,len(boards)):
                if "LimeSDR" in boards[i]:
                    self.cyDev = cyLimeLib(boards[i])
                    break
            if self.cyDev==None:
                raise ValueError("LimeSDR not found")            
            self.usb = self.cyDev
            
        # http://stackoverflow.com/questions/8907905/del-myclass-doesnt-call-object-del
        # https://docs.python.org/3/reference/datamodel.html#object.__del__
        # solution is to avoid __del__, define an explict close() and call it atexit
        atexit.register(self.close)

        #self.usb.setConfiguration()
        self.verbose = verbose
        self.bulkControl = False
        self.fRef = fRef # reference frequency
        FW_VER, DEV_TYPE, LMS_PROTOCOL_VER, HW_VER, EXP_BOARD = self.getInfo()
        if DEV_TYPE!=14:
            ret = "FW_VER           : "+str(FW_VER)+"\n"
            ret += "DEV_TYPE         : "+str(DEV_TYPE)+"\n"
            ret += "LMS_PROTOCOL_VER : " + str(LMS_PROTOCOL_VER)+"\n"
            ret += "HW_VER           : " + str(HW_VER)+"\n"
            ret += "EXP_BOARD        : " + str(EXP_BOARD)+"\n"
            raise ValueError("The board is not LimeSDR.\nBoard info:\n"+ret)
        if verbose>0:
            self.printInfo()
        
        #
        # Check if board has bulk transfers
        #
        if self.usbBackend=="PyUSB":        
            endpoints = self.usb.getEndpoints()
            
            # Bulk control endpoint addresses
            self.ctrlBulkOutAddr = 0x0F
            self.ctrlBulkInAddr = 0x8F
            
            if (self.ctrlBulkOutAddr in endpoints) and (self.ctrlBulkInAddr in endpoints):
                self.bulkControl = True     # LMS7002M is controlled via bulk USB transfers
                if HW_VER>2:
                    # HW version > 1.2
                    self.bulkCommands = [
                        self.getCommandNumber("CMD_BRDSPI_WR"), 
                        self.getCommandNumber("CMD_BRDSPI_RD"),
                        self.getCommandNumber("CMD_LMS7002_WR"), 
                        self.getCommandNumber("CMD_LMS7002_RD"),
                        self.getCommandNumber("CMD_ANALOG_VAL_WR"), 
                        self.getCommandNumber("CMD_ANALOG_VAL_RD"),
                        self.getCommandNumber("CMD_ADF4002_WR"),
                        self.getCommandNumber("CMD_LMS7002_RST"),
                        self.getCommandNumber("CMD_PROG_MCU")
                    ]
                else:
                    self.bulkCommands = [
                        self.getCommandNumber("CMD_BRDSPI_WR"), 
                        self.getCommandNumber("CMD_BRDSPI_RD"),
                        self.getCommandNumber("CMD_LMS7002_WR"), 
                        self.getCommandNumber("CMD_LMS7002_RD"),
                        self.getCommandNumber("CMD_LMS7002_RST")
                    ]
            else:
                self.bulkControl = False    # LMS7002M is controlled via control USB transfers
        
        #
        # Initialize on-board chips
        #
        if self.usbBackend=="PyUSB":
            self.Si5351 = Si5351(self.Si5351Progam)
            self.Si5351.uploadLimeSDRConfig()
        self.LMS7002 = LMS7002(SPIwriteFn=Proxy(self.LMS7002_Write), SPIreadFn=Proxy(self.LMS7002_Read)
                               , verbose=verbose, MCUProgram=Proxy(self.MCUProgram), fRef = self.fRef)
        self.LMS7002.MIMO = 'MIMO'
        self.ADF4002 = ADF4002(Proxy(self.ADF4002Program))
        self.FPGA = LimeSDR_FPGA(spiRead=Proxy(self.BoardSPI_Read), spiWrite=Proxy(self.BoardSPI_Write), usb=self.usb)
        
    def close(self):
        """
        Close communication with LimeSDR
        """
        if self.usbBackend=="LimeAPI":
            del self.cyDev
        else:
            self.usb.closeDevice()
    
    @staticmethod
    def findLMS7002(backend="PyUSB"):
        if not cyLimeLibPresent or backend=="PyUSB":
            return boardUSB.findLMS7002()
        else:
            return cyLimeLib.getDeviceList()
            
    def log(self, logMsg):
        print(logMsg)

    def getCommandNumber(self, cmdName):
        if cmdName == "CMD_GET_INFO":
            return 0x00
        elif cmdName == "CMD_LMS7002_RST":
            return 0x20
        elif cmdName == "LMS_RST_DEACTIVATE":
            return 0x00
        elif cmdName == "LMS_RST_ACTIVATE":
            return 0x01
        elif cmdName == "LMS_RST_PULSE":
            return 0x02
        elif cmdName == "CMD_LMS7002_WR":
            return 0x21
        elif cmdName == "CMD_LMS7002_RD":
            return 0x22
        elif cmdName == "CMD_PROG_MCU":
            return 0x2C
        elif cmdName == "CMD_ADF4002_WR":
            return 0x31
        elif cmdName == "CMD_SI5351_WR":
            return 0x13
        elif cmdName == "CMD_BRDSPI_WR":
            return 0x55
        elif cmdName == "CMD_BRDSPI_RD":
            return 0x56
        elif cmdName == "CMD_SSTREAM_RST":
            return 0x40
        elif cmdName == "CMD_USB_FIFO_RST":
            return 0x40
        elif cmdName == "CMD_ANALOG_VAL_WR":
            return 0x61
        elif cmdName == "CMD_ANALOG_VAL_RD":
            return 0x62
        else:
            raise ValueError("Unknown command "+cmdName)

    def getLMS7002(self):
        return self.LMS7002
            
    #
    # Low level communication
    #
    
    @staticmethod
    def bytes2string(bytes):
        """
        Convert the byte array to string.
        Used for serial communication.
        """
        s = ""
        for i in range(0,len(bytes)):
            s += chr(bytes[i])
        return s

    @staticmethod
    def string2bytes(string):
        """
        Convert the string to byte array.
        Used for serial communication.
        """
        bytes = [0]*int(len(string))
        for i in range(0, len(string)):
            bytes[i] = ord(string[i])
        return bytes

    def sendCommand(self, command, nDataBlocks=0, periphID=0, data=[]):
        """
        Send the command to LimeSDR.
        Function returns (status, data)
        """
        
        if self.usbBackend=="PyUSB":
            tmp = [0]*64
            tmp[0] = command
            tmp[1] = 0
            tmp[2] = nDataBlocks
            tmp[3] = periphID
            nData = len(data)
            if nData>56:
                raise ValueError("Length of data must be less than 56, "+str(nData)+" bytes given")
            for i in range(0, nData):
                tmp[8+i] = data[i]
            if self.verbose>2:
                self.log("sendCommand:Write    : "+str(tmp))
            toSend = tmp
            if (self.bulkControl==True) and (command in self.bulkCommands):
                self.usb.bulkWrite(self.ctrlBulkOutAddr, toSend)
                tmp = self.usb.bulkRead(self.ctrlBulkInAddr, 64)
            else:        
                self.usb.controlTransfer(0x40, 0xc1, 0, 0, toSend, len(toSend)) 
                tmp = self.usb.controlTransfer(0xc0, 0xc0, 0, 0, 64)
            if len(tmp)<64:
                raise IOError("Lenght of received data "+len(tmp)+"<64 bytes")
            if self.verbose>2:
                self.log("sendCommand:Response : "+str(tmp))
            rxStatus = tmp[1]
            rxData = tmp[8:]
            return (rxStatus, rxData)
        else:
            nData = len(data)
            if nData>56:
                raise ValueError("Length of data must be less than 56, "+str(nData)+" bytes given")
            return self.cyDev.transferLMS64C(command, data)


    #
    # Utility functions
    #

    def getInfo(self):
        """
        Get the information about LimeSDR.
        Function returns 
        (FW_VER, DEV_TYPE, LMS_PROTOCOL_VER, HW_VER, EXP_BOARD)
        """
        command = self.getCommandNumber("CMD_GET_INFO")
        status, rxData = self.sendCommand(command)
        if status != 1:
            raise IOError("Command returned with status "+str(status))
        FW_VER = rxData[0]
        DEV_TYPE = rxData[1]
        LMS_PROTOCOL_VER = rxData[2]
        HW_VER = rxData[3]
        EXP_BOARD = rxData[4]
        return (FW_VER, DEV_TYPE, LMS_PROTOCOL_VER, HW_VER, EXP_BOARD)
   
    def printInfo(self):
        """
        Print info about LimeSDR
        """
        FW_VER, DEV_TYPE, LMS_PROTOCOL_VER, HW_VER, EXP_BOARD = self.getInfo()
        self.log("FW_VER           : "+str(FW_VER))
        self.log("DEV_TYPE         : "+str(DEV_TYPE))
        self.log("LMS_PROTOCOL_VER : " + str(LMS_PROTOCOL_VER))
        self.log("HW_VER           : " + str(HW_VER))
        self.log("EXP_BOARD        : " + str(EXP_BOARD))
        
    def LMS7002_Reset(self, rstType="pulse"):
        """
        Reset LMS7002.
        rstType specifies the type of reset:
            pulse - activate and deactivate reset
            activate - activate reset
            deactivate - deactivate reset
        """
        command = self.getCommandNumber("CMD_LMS7002_RST")
        if rstType=="pulse":
            data = [self.getCommandNumber("LMS_RST_PULSE")]
        elif rstType=="activate":
            data = [self.getCommandNumber("LMS_RST_ACTIVATE")]        
        elif rstType=="deactivate":
            data = [self.getCommandNumber("LMS_RST_DEACTIVATE")]        
        else:
            raise ValueError("Invalid reset type "+str(rstType))
        rxStatus, rxData = self.sendCommand(command, data=data)
        if rxStatus != 1:
            raise IOError("Command returned with status "+str(status))
        self.LMS7002.loadResetValues()

    def LMS7002_Write(self, regList, packetSize=14):
        """
        Write the data to LMS7002 via SPI interface.
        regList is a list of registers to write in the format:
        [ (regAddr, regData), (regAddr, regData), ...]
        packetSize controls the number of register writes in a single USB transfer
        """
        command = self.getCommandNumber("CMD_LMS7002_WR")
        nDataBlocks = len(regList)

        toSend = copy(regList)
       
        while len(toSend)>0:
            nPackets = 0
            data = []
            while nPackets<packetSize and len(toSend)>0:
                regAddr, regData = toSend[0]
                toSend.pop(0)
                regAddrH = regAddr >> 8
                regAddrL = regAddr % 256
                regDataH = regData >> 8
                regDataL = regData % 256
                data += [regAddrH, regAddrL, regDataH, regDataL]
                nPackets += 1
            rxStatus, rxData = self.sendCommand(command, nDataBlocks = nPackets, data=data)
            if rxStatus != 1:
                raise IOError("Command returned with status "+str(rxStatus))

        
    def LMS7002_Read(self, regList, packetSize=14):
        """
        Read the data from LMS7002 via SPI interface.
        regList is a list of registers to read in the format:
        [ regAddr, regAddr, ...]
        packetSize controls the number of register writes in a single USB transfer
        """
        command = self.getCommandNumber("CMD_LMS7002_RD")
        nDataBlocks = len(regList)

        toRead = copy(regList)
        regData = []
       
        while len(toRead)>0:
            nPackets = 0
            data = []
            while nPackets<packetSize and len(toRead)>0:
                regAddr = toRead[0]
                toRead.pop(0)
                regAddrH = regAddr >> 8
                regAddrL = regAddr % 256
                data += [regAddrH, regAddrL]
                nPackets += 1
            rxStatus, rxData = self.sendCommand(command, nDataBlocks = nPackets, data=data)
            if rxStatus != 1:
                raise IOError("Command returned with status "+str(rxStatus))
            for i in range(0, nPackets):
                regDataH = rxData[i*4+2]
                regDataL = rxData[i*4+3]
                regData.append( (regDataH << 8) + regDataL)
        return regData

    #
    # LMS7002 MCU program
    #

    def MCUProgram(self, mcuProgram, Mode):
        if not self.bulkControl and self.usbBackend=="PyUSB":
            # Hardware does not support bulk endpoint control
            self._MCUProgram_FW(mcuProgram, Mode)
        else:
            # Hardware supports bulk endpoint control
            ver, rev, mask = self.getLMS7002().chipInfo
            if mask==1:
                # MCU has 16k RAM
                if len(mcuProgram)>16384:
                    raise ValueError("MCU program for mask 1 chips must be less than 16 kB. Given program size:"+str(len(mcuProgram)))
                if len(mcuProgram)==8192: # Check if program is 8k
                    mcuProgram += [0]*8192 # Extend it to 16k
                self._MCUProgram_Direct(mcuProgram, Mode)
            else:
                # MCU has 8k RAM
                if len(mcuProgram)>8192:
                    raise ValueError("MCU program for mask 0 chips must be less than 8 kB. Given program size:"+str(len(mcuProgram)))
                self._MCUProgram_Direct(mcuProgram, Mode)
        
            
    def _MCUProgram_Direct(self, mcuProgram, Mode):
        """
        Write the data to LMS7002 MCU via SPI interface.
        MCU is programmed directly by using bulk interface MCU commands.
        mcuProgram is 8192 or 16384 bytes long array holding the MCU program.
        mode selects the MCU programming mode.
        """
        if Mode not in [0, 1,2,3, 'EEPROM_AND_SRAM', 'SRAM', 'SRAM_FROM_EEPROM']:
            raise ValueError("Mode should be [1,2,3, 'EEPROM_AND_SRAM', 'SRAM', 'SRAM_FROM_EEPROM']")
        if Mode==0:
            return
        elif Mode==1 or Mode=='EEPROM_AND_SRAM':
            mode = 1
        elif Mode==2 or Mode=='SRAM':
            mode = 2
        else:
            mode = 3

        if len(mcuProgram)!=8192 and len(mcuProgram)!=16384:
            raise ValueError("MCU program should be 8192 or 16384 bytes long")
        
        toSend = [ (2, 0), (2, mode)] # Write 0 to address 2, write mode to address 2 (mSPI_CTRL)
        self.LMS7002_Write(toSend)
        lms7002 = self.getLMS7002()

        pos = 0
        while pos<len(mcuProgram):
            startTime = timer()
            while lms7002.mSPI.EMPTY_WRITE_BUFF==0:
                if timer()-startTime>1:
                    raise IOError("MCU programming timeout")

            for j in range(0, 4):
                toSend = []
                for i in range(0, 8):
                    toSend.append( (4, mcuProgram[pos]) )
                    pos += 1
                self.LMS7002_Write(toSend)
            if mode==3:
                break
        startTime = timer()
        while lms7002.mSPI.PROGRAMMED==0:
            if timer()-startTime>1:
                raise IOError("MCU programming timeout")
    
    def _MCUProgram_FW(self, mcuProgram, Mode):
        """
        Write the data to LMS7002 MCU via SPI interface.
        FX3 firmware programs the MCU.
        mcuProgram is 8192 bytes long array holding the MCU program.
        mode selects the MCU programming mode.
        """
        if Mode not in [0, 1,2,3, 'EEPROM_AND_SRAM', 'SRAM', 'SRAM_FROM_EEPROM']:
            raise ValueError("Mode should be [1,2,3, 'EEPROM_AND_SRAM', 'SRAM', 'SRAM_FROM_EEPROM']")
        if Mode==0:
            return
        elif Mode==1 or Mode=='EEPROM_AND_SRAM':
            mode = 1
        elif Mode==2 or Mode=='SRAM':
            mode = 2
        else:
            mode = 3

        if len(mcuProgram)!=8192:
            raise ValueError("MCU program should be 8192 bytes long")
        
        command = self.getCommandNumber("CMD_PROG_MCU")

        pos = 0
        while pos<8192:
            data = [0]*34
            data[0] = mode
            data[1] = pos//32
            for i in range(0,32):
                data[2+i] = mcuProgram[pos+i]
            rxStatus, rxData = self.sendCommand(command, nDataBlocks=34, data=data)
            if rxStatus != 1:
                raise IOError("Command returned with status "+str(rxStatus))
            pos += 32
            if mode==3:
                break

    #
    # ADF4002 program
    #                

    def ADF4002Program(self, regValues):
        """
        Program ADF4002 with given regValues.
        regValues = [reg1, reg2, reg3, reg4]
        where reg1-4 are integers containing the values of ADF4002 registers (24 bit).
        """
        if len(regValues)!=4:
            raise ValueError("Expected four 24-bit values, got "+str(len(regValues)))
        data = []
        for reg in regValues:
            bits23_16 = (reg >> 16) & 0xFF
            bits15_8 = (reg >> 8) & 0xFF
            bits7_0 = reg & 0xFF
            data += [bits23_16, bits15_8, bits7_0]
        command = self.getCommandNumber("CMD_ADF4002_WR")
        rxStatus, rxData = self.sendCommand(command, nDataBlocks=4, data=data)
        if rxStatus != 1:
            raise IOError("Command returned with status "+str(rxStatus))


    #
    # Si5351
    #        
    def Si5351Progam(self, regList, packetSize=20):
        """
        Program Si5351
        """
        command = self.getCommandNumber("CMD_SI5351_WR")
        nDataBlocks = len(regList)

        toSend = copy(regList)
       
        while len(toSend)>0:
            nPackets = 0
            data = []
            while nPackets<packetSize and len(toSend)>0:
                regAddr, regData = toSend[0]
                toSend.pop(0)
                data += [regAddr, regData]
                nPackets += 1
            rxStatus, rxData = self.sendCommand(command, nDataBlocks = nPackets, data=data)
            if rxStatus != 1:
                raise IOError("Command returned with status "+str(rxStatus))

    #
    # Board SPI
    #  

    def BoardSPI_Write(self, regList, packetSize=14):
        """
        Write the data to board via SPI interface.
        regList is a list of registers to write in the format:
        [ (regAddr, regData), (regAddr, regData), ...]
        packetSize controls the number of register writes in a single USB transfer
        """
        command = self.getCommandNumber("CMD_BRDSPI_WR")
        nDataBlocks = len(regList)

        toSend = copy(regList)
       
        while len(toSend)>0:
            nPackets = 0
            data = []
            while nPackets<packetSize and len(toSend)>0:
                regAddr, regData = toSend[0]
                toSend.pop(0)
                regAddrH = regAddr >> 8
                regAddrL = regAddr % 256
                regDataH = regData >> 8
                regDataL = regData % 256
                data += [regAddrH, regAddrL, regDataH, regDataL]
                nPackets += 1
            rxStatus, rxData = self.sendCommand(command, nDataBlocks = nPackets, data=data)
            if rxStatus != 1:
                raise IOError("Command returned with status "+str(rxStatus))
        
    def BoardSPI_Read(self, regList, packetSize=14):
        """
        Read the data from board via SPI interface.
        regList is a list of registers to read in the format:
        [ regAddr, regAddr, ...]
        packetSize controls the number of register writes in a single USB transfer
        """
        command = self.getCommandNumber("CMD_BRDSPI_RD")
        nDataBlocks = len(regList)

        toRead = copy(regList)
        regData = []
       
        while len(toRead)>0:
            nPackets = 0
            data = []
            while nPackets<packetSize and len(toRead)>0:
                regAddr = toRead[0]
                toRead.pop(0)
                regAddrH = regAddr >> 8
                regAddrL = regAddr % 256
                data += [regAddrH, regAddrL]
                nPackets += 1
            rxStatus, rxData = self.sendCommand(command, nDataBlocks = nPackets, data=data)
            if rxStatus != 1:
                raise IOError("Command returned with status "+str(rxStatus))
            for i in range(0, nPackets):
                regDataH = rxData[i*4+2]
                regDataL = rxData[i*4+3]
                regData.append( (regDataH << 8) + regDataL)
        return regData
        
