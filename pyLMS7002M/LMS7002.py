#***************************************************************
#* Name:      LMS7002.py
#* Purpose:   LMS7002 
#* Author:    Lime Microsystems ()
#* Created:   2016-11-14
#* Copyright: Lime Microsystems (limemicro.com)
#* License:
#**************************************************************

from LMS7002_REGDESC import *
from LMS7002_REGDESC_MR3 import *
from LMS7002_regDataStructs import *
from LMS7002_regDataStructs import *

# Import core chip modules
from LMS7002_CHIP import *
from LMS7002_LimeLight import *
from LMS7002_IO import *
from LMS7002_NCO import *
from LMS7002_GFIR1 import *
from LMS7002_GFIR2 import *
from LMS7002_GFIR3 import *
from LMS7002_TxTSP import *
from LMS7002_RxTSP import *
from LMS7002_RFE import *
from LMS7002_RBB import *
from LMS7002_TRF import *
from LMS7002_TBB import *
from LMS7002_AFE import *
from LMS7002_BIAS import *
from LMS7002_SX import *
from LMS7002_CGEN import *
from LMS7002_XBUF import *
from LMS7002_CDS import *
from LMS7002_mSPI import *
from LMS7002_DCCAL import *

# Import support modules
from LMS7002_calibration import *

class LMS7002(object):
    def __init__(self, SPIwriteFn=None, SPIreadFn=None, verbose=0, MCUProgram=None, fRef = 30.72e6):
        if SPIwriteFn==None:
            self._SPIwriteFn = self.debugSPIwrite
        else:
            self._SPIwriteFn = SPIwriteFn
        if SPIreadFn==None:
            self._SPIreadFn = self.debugSPIread
        else:
            self._SPIreadFn = SPIreadFn
        if MCUProgram==None:
            self._MCUProgram = self.debugMCUProgram
        else:
            self._MCUProgram = MCUProgram
        self.fRef = fRef    # Reference frequency
        self._SPIImmediate = True
        self.verbose = verbose
        
        self.chipIDMR2 = 0x3840
        self.chipIDMR3 = 0x3841
        
        self.chipID = self.SPIreadFn([0x2F])[0]
        if self.chipID == self.chipIDMR2:
            regDefList = LMS7002_REGDESC.split('\n')
        elif self.chipID == self.chipIDMR3:
            regDefList = LMS7002_REGDESC_MR3.split('\n')
        else:
            raise ValueError("Unsupported chip. CHIP ID = "+str(self.chipID))
        regParser = regDescParser(regDefList, self)
        self.regDesc = regParser.getRegisterDefinition()
        self.MACReg = self.getRegisterByAddress(0x20)
        self.MAC=1
        
        #
        # Initialize core chip modules
        #
        self.CHIP  = LMS7002_CHIP(self)
        self.LimeLight = LMS7002_LimeLight(self)
        self.IO    = LMS7002_IO(self)
        self.NCO   = { "RXA" : LMS7002_NCO(self, "RX", "A"),
                       "RXB" : LMS7002_NCO(self, "RX", "B"),
                       "TXA" : LMS7002_NCO(self, "TX", "A"),
                       "TXB" : LMS7002_NCO(self, "TX", "B")}
        self.GFIR1 = { "RXA" : LMS7002_GFIR1(self, "RX", "A"),
                       "RXB" : LMS7002_GFIR1(self, "RX", "B"),
                       "TXA" : LMS7002_GFIR1(self, "TX", "A"),
                       "TXB" : LMS7002_GFIR1(self, "TX", "B")}
        self.GFIR2 = { "RXA" : LMS7002_GFIR2(self, "RX", "A"),
                       "RXB" : LMS7002_GFIR2(self, "RX", "B"),
                       "TXA" : LMS7002_GFIR2(self, "TX", "A"),
                       "TXB" : LMS7002_GFIR2(self, "TX", "B")}
        self.GFIR3 = { "RXA" : LMS7002_GFIR3(self, "RX", "A"),
                       "RXB" : LMS7002_GFIR3(self, "RX", "B"),
                       "TXA" : LMS7002_GFIR3(self, "TX", "A"),
                       "TXB" : LMS7002_GFIR3(self, "TX", "B")}
        self.TxTSP = { "A" : LMS7002_TxTSP(self, "A"),
                       "B" : LMS7002_TxTSP(self, "B")}
        self.RxTSP = { "A" : LMS7002_RxTSP(self, "A"),
                       "B" : LMS7002_RxTSP(self, "B")}
        self.RFE   = { "A" : LMS7002_RFE(self, "A"),
                       "B" : LMS7002_RFE(self, "B")}
        self.RBB   = { "A" : LMS7002_RBB(self, "A"),
                       "B" : LMS7002_RBB(self, "B")}
        self.TRF   = { "A" : LMS7002_TRF(self, "A"),
                       "B" : LMS7002_TRF(self, "B")}
        self.TBB   = { "A" : LMS7002_TBB(self, "A"),
                       "B" : LMS7002_TBB(self, "B")}
        self.AFE   = LMS7002_AFE(self)
        self.BIAS  = LMS7002_BIAS(self)
        self.SX    = { "R" : LMS7002_SX(self, "R"),
                       "T" : LMS7002_SX(self, "T")}
        self.CGEN  = LMS7002_CGEN(self)
        self.XBUF  = LMS7002_XBUF(self)
        self.CDS   = LMS7002_CDS(self)
        self.mSPI  = LMS7002_mSPI(self)
        self.DCCAL = LMS7002_DCCAL(self)
        
        
        #
        # Initialize support modules
        #

        self.calibration = LMS7002_calibration(self)

    def debugSPIwrite(self, regList):
        if self.verbose>0:
            for reg in regList:
                addr, data = reg
                self.log("SPIWRITE: ADDR = "+str(addr)+" DATA = "+str(data))

    def debugSPIread(self, regList):                
        ret = []
        if self.verbose>0:
            for addr in regList:
                self.log("SPIREAD: ADDR = "+str(addr))
                ret.append(self.getRegisterByAddress(addr).getValue(noUpdate=True))
        return ret

    def debugMCUProgram(self, data, mode):
        pass

    def enableInteractiveMode(self):
        """
        Enable interactive mode. Every command is immediately sent to the chip.
        """
        if self.verbose>1:
            self.log("Enabling interactive mode")
        self.setImmediateMode(True)
    
    def disableInteractiveMode(self):
        """
        Disable interactive mode. Commands are not sent to the chip, but change the memory content.
        """
        if self.verbose>1:
            self.log("Disabling interactive mode")
        self.setImmediateMode(False)
        
    def isInteractive(self):
        return self.getImmediateMode()

    def getMACfromName(self, value):
        if value not in [1, 2, 'A', 'B', 'R', 'RX', 'T', 'TX']:
            raise ValueError("MAC must be in set [1, 2, 'A', 'B', 'R', 'RX', 'T', 'TX']")
        if value==1 or value==2:
            val = value
        if value=='A':
            val = 1
        if value=='B':
            val = 2
        if value=='R' or value=='RX':
            val = 1
        if value=='T' or value=='TX':
            val = 2
        return val    

    def loadResetValues(self):
        immMode = self.SPIImmediate
        self.SPIImmediate = True        
        prevMAC = self.MAC
        
        self.MIMO = 'MIMO'
        
        self.CGEN.ICT_VCO_CGEN = 16
        #self.BIAS.PD_LDO_SPIBUF = 1
        #self.BIAS.PD_LDO_DIGIp2 = 1
        #self.BIAS.PD_LDO_DIGIp1 = 1
        
        self.TBB['A'].ICT_IAMP_FRP_TBB = 1
        self.TBB['A'].ICT_IAMP_GG_FRP_TBB = 6

        self.TBB['B'].ICT_IAMP_FRP_TBB = 1
        self.TBB['B'].ICT_IAMP_GG_FRP_TBB = 6

        self.RFE['A'].ICT_TIAMAIN_RFE = 2
        self.RFE['A'].ICT_TIAOUT_RFE = 2
        self.RFE['A'].ICT_LNA_RFE = 31

        self.RFE['B'].ICT_TIAMAIN_RFE = 2
        self.RFE['B'].ICT_TIAOUT_RFE = 2
        self.RFE['B'].ICT_LNA_RFE = 31

        self.SX['R'].ICT_VCO = 255
        self.SX['R'].RSEL_LDO_VCO = 6
        self.SX['R'].IOFFSET_CP = 12
        self.SX['R'].IPULSE_CP = 63
        
        self.SX['T'].ICT_VCO = 255
        self.SX['T'].RSEL_LDO_VCO = 6
        self.SX['T'].IOFFSET_CP = 12
        self.SX['T'].IPULSE_CP = 63

        self.MAC = prevMAC
        self.SPIImmediate = immMode

    @property
    def chipInfo(self):
        """
        Returns chip info (VER, REV, MASK)
        """
        return self.CHIP.getChipInfo()

    @property
    def MIMO(self):
        """
        Returns whether the chip works in MIMO mode
        """
        if self['MIMOCFG']==0:
            return True
        else:
            return False
            
    @MIMO.setter
    def MIMO(self, value):
        if value not in [True, False, 'MIMO', 'SISO']:
            raise ValueError("Value must be [True, False, 'MIMO', 'SISO']")
        if value==True or value=='MIMO':
            self['MIMOCFG']=0
        else:
            self['MIMOCFG']=1

    @property
    def MAC(self):
        return (3 & self.MACReg.getValue(noUpdate=True))

    @MAC.setter
    def MAC(self, value):
        val = self.getMACfromName(value)
        tmp = self.MACReg.getValue(noUpdate=True)
        tmp = (~3) & tmp
        tmp = tmp | val
        if self.SPIImmediate:
            self.MACReg.setValue(tmp)
        else:
            self.MACReg.setValue(tmp, noUpdate=True)

    @property
    def SPIImmediate(self):
        return self.getImmediateMode()

    def getImmediateMode(self):
        return self._SPIImmediate

    @SPIImmediate.setter
    def SPIImmediate(self, val):
        self.setImmediateMode(val)

    def setImmediateMode(self, immediateMode):
        self._SPIImmediate=immediateMode

    @property
    def SPIwriteFn(self):
        return self.getSPIwriteFn()
        
    def getSPIwriteFn(self):
        return self._SPIwriteFn

    @property 
    def SPIreadFn(self):
        return self.getSPIreadFn()
    
    def getSPIreadFn(self):
        return self._SPIreadFn
        
    def getRegisterByName(self, regName):
        reg = self.regDesc.getRegisterByName(regName)
        return reg
        
    def getRegisterByAddress(self, regAddr):
        reg = self.regDesc.getRegisterByAddress(regAddr)
        return reg

    def getRegisterBanks(self, nSets=0):
        regBanks = []
        if nSets == 0:
            for rb in self.regDesc.getRegBanks():
                regBanks.append(rb.getName())
        else:
            for rb in self.regDesc.getRegBanks():
                if rb.getNRegisterSets()==nSets:
                    regBanks.append(rb.getName())
        return regBanks

    def log(self, msg, verboseLevel=0):
        if verboseLevel <= self.verbose:
            print msg

    #
    # Auxiliary functions
    #

    @staticmethod
    def intToHex(val, upperCase=True):
        hexVal = hex(val)[2:]
        while len(hexVal)<4:
            hexVal = "0"+hexVal
        if upperCase:
            hexVal = hexVal.upper()
        hexVal = "0x"+hexVal
        return hexVal

    @staticmethod
    def fixLen(string, length, center=True):
        res = string
        if not center:
            while len(res)<length:
                res += " "
        else:
            nSpaces = length-len(string)
            if nSpaces>0:
                if nSpaces%2==1:
                    nLeft = nSpaces//2+1
                    nRight = nSpaces//2
                else:
                    nLeft = nSpaces//2
                    nRight = nSpaces//2
                res = " "*nLeft + res + " "*nRight
        return res
        
    #
    # Register reading/writing functions
    #
        
    def readRegisters(self, regAddrs="ALL", fromMemory=False):
        """
        Read registers from LMS7002 at given addresses.
        regAddrs = [ regAddr, regAddr, ...]
        If regAddrs = "ALL" all registers are read.
        
        Read values are written to registers and returned as a list.
        """
        if self.SPIreadFn==None:
            self.log("SPIreadFn not set, skipping")
            return []
        if regAddrs == "ALL":
            addrList = self.regDesc.getRegisterAddresesByName("ALL")
        else:
            addrList = regAddrs
        if fromMemory:
            regValues = []
            for i in range(0,len(addrList)):
                addr = addrList[i]
                reg = self.getRegisterByAddress(addr)
                regValues.append(reg.getValue(noUpdate=True))
        else:
            regValues = self.SPIreadFn(addrList)
            for i in range(0,len(addrList)):
                addr = addrList[i]
                reg = self.getRegisterByAddress(addr)
                reg.setValue(regValues[i], noUpdate=True)
        return regValues

    def readRegistersByName(self, regNames="ALL", fromMemory=False):
        """
        Read registers from LMS7002 by names.
        regNames = [ regName, regName, ...]
        If regNames = "ALL" all registers are read.
        
        Read values are written to registers and returned as a list.
        """
        if self.SPIreadFn==None:
            self.log("SPIreadFn not set, skipping reading from SPI")
            return []
        addrList = self.regDesc.getRegisterAddresesByName(regNames)
        if fromMemory:
            regValues = []
            for i in range(0,len(addrList)):
                addr = addrList[i]
                reg = self.getRegisterByAddress(addr)
                regValues.append(reg.getValue(noUpdate=True))
        else:
            regValues = self.SPIreadFn(addrList)
            for i in range(0,len(addrList)):
                addr = addrList[i]
                reg = self.getRegisterByAddress(addr)
                reg.setValue(regValues[i], noUpdate=True)
        return regValues

    def writeRegisters(self, regAddrs="ALL"):
        """
        Write registers to LMS7002 at given addresses.
        regAddrs = [ regAddr, regAddr, ... ]
        If regAddrs = "ALL" all registers are written.
        Values to be written are taken from memory.
        """
        if self.SPIwriteFn==None:
            self.log("SPIwriteFn not set, skipping  writing to SPI")
            return
        if regAddrs == "ALL":
            addrList = self.regDesc.getRegisterAddresesByName("ALL")
        else:
            addrList = regAddrs
        toWriteList = []
        for i in range(0, len(addrList)):
            addr = addrList[i]
            reg = self.getRegisterByAddress(addr)
            val = reg.getValue(noUpdate=True)
            toWriteList += [ (addr, val) ]
        self.SPIwriteFn( toWriteList )

    def writeRegistersByName(self, regNames="ALL"):
        """
        Write registers to LMS7002.
        regNames = [ "regName", "regName", ... ]
        If regNames = "ALL" all registers are written.
        Values to be written are taken from memory.
        """
        if self.SPIwriteFn==None:
            self.log("SPIwriteFn not set, skipping writing to SPI")
            return
        addrList = self.regDesc.getRegisterAddresesByName(regNames)
        toWriteList = []
        for i in range(0, len(addrList)):
            addr = addrList[i]
            reg = self.getRegisterByAddress(addr)
            val = reg.getValue(noUpdate=True)
            toWriteList += [ (addr, val) ]
        self.SPIwriteFn( toWriteList )

    def readRegisterBank(self, regBankName, MAC=0, fromMemory=False):
        """
        Read the whole register bank from LMS7002
        If MAC=0, use current MAC, else use the given MAC
        Returns a list of tuples [(addr, val), (addr, val), ...]
        """
        immMode = self.SPIImmediate
        if not fromMemory:
            self.SPIImmediate = True
        prevMAC = self.MAC
        if MAC!=0:
            self.MAC = MAC
        regBankToRead = None
        for regBank in self.regDesc.getRegBanks():
            if regBank.getName()==regBankName:
                regBankToRead = regBank
                break
        if regBankToRead==None:
            raise ValueError("Register bank "+regBankName+" not found")
        regList = []
        for reg in regBankToRead.getRegs():
            regList.append(reg.getAddress())
        regVals = self.readRegisters(regList, fromMemory=fromMemory)
        if MAC!=0:
            self.MAC = prevMAC
        self.SPIImmediate = immMode
        return zip(regList, regVals)

    def writeRegisterBank(self, regBankName, MAC=0):
        """
        Write the whole register bank to LMS7002
        If MAC=0, use current MAC, else use the given MAC
        """
        immMode = self.SPIImmediate
        self.SPIImmediate = True
        prevMAC = self.MAC
        if MAC!=0:
            self.MAC = MAC
        regBankToWrite = None
        for regBank in self.regDesc.getRegBanks():
            if regBank.getName()==regBankName:
                regBankToWrite = regBank
                break
        if regBankToWrite==None:
            raise ValueError("Register bank "+regBankName+" not found")
        regList = []
        for reg in regBankToWrite.getRegs():
            regList.append(reg.getAddress())
        self.writeRegisters(regList)
        if MAC!=0:
            self.MAC = prevMAC
        self.SPIImmediate = immMode

    def readFullChip(self, fromMemory=False):
        """
        Read all LMS7002 registers to memory
        """
        chipState = [ [], [], [] ] # Registers. First entry does not depend on MAC, second is for MAC=1, third for MAC=2
        immMode = self.SPIImmediate
        if not fromMemory:
            self.SPIImmediate = True
        prevMAC = self.MAC
        regBanks = self.getRegisterBanks(nSets=1) # Get register banks unaffected by MAC
        for regBank in regBanks:
            if self.verbose>0:
                self.log("Reading register bank : "+regBank)
            tmp = self.readRegisterBank(regBank, fromMemory=fromMemory)
            chipState[0] += tmp
        regBanks = self.getRegisterBanks(nSets=2) # Get register banks affected by MAC
        for regBank in regBanks:
            self.MAC = 1
            if self.verbose>0:
                self.log("Reading register bank : "+regBank +" MAC = 1")
            tmp = self.readRegisterBank(regBank, fromMemory=fromMemory)
            chipState[1] += tmp
            self.MAC = 2
            if self.verbose>0:
                self.log("Reading register bank : "+regBank +" MAC = 2")
            tmp = self.readRegisterBank(regBank, fromMemory=fromMemory)
            chipState[2] += tmp
        self.MAC = prevMAC
        self.SPIImmediate = immMode        
        return chipState

    def writeFullChip(self):
        """
        Write all registers from memory to LMS7002
        """
        immMode = self.SPIImmediate
        self.SPIImmediate = True
        prevMAC = self.MAC
        regBanks = self.getRegisterBanks(nSets=1) # Get register banks unaffected by MAC
        for regBank in regBanks:
            if regBank == 'uC':
                continue
            if self.verbose>0:
                self.log("Writing register bank : "+regBank)
            self.writeRegisterBank(regBank)
        regBanks = self.getRegisterBanks(nSets=2) # Get register banks affected by MAC
        for regBank in regBanks:
            self.MAC = 1
            if self.verbose>0:
                self.log("Writig register bank : "+regBank +" MAC = 1")
            self.writeRegisterBank(regBank)
            self.MAC = 2
            if self.verbose>0:
                self.log("Writing register bank : "+regBank +" MAC = 2")
            self.writeRegisterBank(regBank)
        self.MAC = prevMAC
        self.SPIImmediate = immMode

    def saveChipState(self, fromMemory=True):
        """
        Save the chip state
        """
        self.chipState = self.readFullChip(fromMemory=fromMemory)
        
    def restoreChipState(self):
        """
        Restore the saved chip state.
        """
        immMode = self.SPIImmediate
        self.SPIImmediate = False        
        prevMAC = self.MAC

        self.MAC = 1         
        regs = self.chipState[0]
        for i in range(0,len(regs)):
            addr = regs[i][0]
            val = regs[i][1]
            reg = self.getRegisterByAddress(addr)
            reg.setValue(val, noUpdate=True)

        regs = self.chipState[1]
        for i in range(0,len(regs)):
            addr = regs[i][0]
            val = regs[i][1]
            reg = self.getRegisterByAddress(addr)
            reg.setValue(val, noUpdate=True)
 
        self.MAC = 2 

        regs = self.chipState[2]
        for i in range(0,len(regs)):
            addr = regs[i][0]
            val = regs[i][1]
            reg = self.getRegisterByAddress(addr)
            reg.setValue(val, noUpdate=True)

        self.writeFullChip()
 
        self.MAC = prevMAC
        self.SPIImmediate = immMode

    def dumpChipState(self, fileName):
        immMode = self.SPIImmediate
        self.SPIImmediate = True
        prevMAC = self.MAC
        txtRes = ""
        regBanks = self.getRegisterBanks(nSets=1) # Get register banks unaffected by MAC
        for regBankName in regBanks:
            if self.verbose>0:
                self.log("Reading register bank : "+regBankName)
            for regBank in self.regDesc.getRegBanks():
                if regBank.getName()==regBankName:
                    regBankToRead = regBank
                    break
            for reg in regBankToRead.getRegs():
                txtRes += reg.__str__()
        regBanks = self.getRegisterBanks(nSets=2) # Get register banks affected by MAC
        for regBankName in regBanks:
            self.MAC = 1
            if self.verbose>0:
                self.log("Reading register bank : "+regBank +" MAC = 1")
            for regBank in self.regDesc.getRegBanks():
                if regBank.getName()==regBankName:
                    regBankToRead = regBank
                    break
            for reg in regBankToRead.getRegs():
                txtRes += reg.__str__()
            self.MAC = 2
            if self.verbose>0:
                self.log("Reading register bank : "+regBank +" MAC = 2")
            for regBank in self.regDesc.getRegBanks():
                if regBank.getName()==regBankName:
                    regBankToRead = regBank
                    break
            for reg in regBankToRead.getRegs():
                txtRes += reg.__str__()
        self.MAC = prevMAC
        self.SPIImmediate = immMode                      
        outFile = open(fileName, 'w')
        outFile.write(txtRes)
        outFile.close()

    #
    # Operator overloading
    #        

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.getRegisterByAddress(key)
        else:
            return self.getRegisterByName(key)
   
    def __setitem__(self, key, val):
        if isinstance(key, int):
            reg = self.getRegisterByAddress(key)
        else:
            reg = self.getRegisterByName(key)
#msavic 160606			
        if(reg!=-1):
            reg.setValue(val)

    #
    # ini file read/write
    #
    
    def readIniFile(self, iniFileName, writeToChip=True):
        immMode = self.SPIImmediate
        self.SPIImmediate = False # Turn off immediate mode
        section = None
        iniFile = open(iniFileName, 'r')
        for line in iniFile:
            if line.strip()=="":
                continue
            if "[" in line:
                # Get the section name
                section = (line.strip())[1:-1]
                # msavic 160606
                if (section=="LMS7002 registers ch.A") or (section=="lms7002_registers_a"):
                    self.MAC = 'A'
                # msavic 160606
                if (section=="LMS7002 registers ch.B") or (section=="lms7002_registers_b"):
                    self.MAC = 'B'
            else:
                # Process section data
				# msavic 160606
                if (section=="FILE INFO") or (section=="file_info"):
                    continue 				
                if section=="Frequencies":
                    continue
				# msavic 160606
                if (section=="LMS7002 registers ch.A") or (section=="lms7002_registers_a"):
                    addr, val = line.split("=")
                    self[int(addr,16)] = int(val, 16)
                    continue
				# msavic 160606
                if (section=="LMS7002 registers ch.B") or (section=="lms7002_registers_b"):
                    addr, val = line.split("=")
                    self[int(addr,16)] = int(val, 16)
                    continue
                if section=="NCO Rx ch.A":
                    continue
                if section=="NCO Rx ch.B":
                    continue
                if section=="NCO Tx ch.A":
                    continue
                if section=="NCO Tx ch.B":
                    continue
				# msavic 160606
                if (section=="Reference clocks") or (section=="reference_clocks"):
                    continue
                if section=="TSG_DC_REG":
                    continue
                if section=="gpio_states":
                    continue
                raise ValueError("Unknown section "+section)
        self.SPIImmediate = immMode
        if writeToChip:
            self.writeFullChip()
            

