from libc.stdlib cimport malloc, free
cimport cyLimeLib

cdef class cyLimeLib:

    cdef lms_device_t* _lms_device
    
    @staticmethod
    def getDeviceList():
        """
        Static method to get the list of devices
        """
        cdef lms_info_str_t devList[8]
        n = LMS_GetDeviceList(devList)
        res = []
        for i in range(0,n):
            res.append(devList[i])
        return res
    
    def __cinit__(self, devStr=None):
        """
        Class constructor.
        Connects to board given in devStr, which is obtained from getDeviceList.
        If devStr is not given connects to first board.
        """
        cdef lms_info_str_t _devStr
        self._lms_device = <lms_device_t*>0
        if devStr == None:
            LMS_Open(&self._lms_device, NULL, NULL)
        else:
            for i in range(0, len(devStr)):
                _devStr[i] = <int>(ord(devStr[i]))
            _devStr[len(devStr)] = 0
            LMS_Open(&self._lms_device, _devStr, NULL)            

    def __dealloc__(self):
        """
        Class destructor.
        Closes connection to the board.
        """
        LMS_Close(self._lms_device)
        
    def transferLMS64C(self, cmd, data):
        cdef uint8_t _data[56]
        cdef size_t dataLen = len(data)
        if dataLen>56:
            raise ValueError("Max 56 bytes per packet")
        for i in range(0, dataLen):
            _data[i] = data[i]
        res = LMS_TransferLMS64C(self._lms_device, cmd, _data, &dataLen)
        res += 1
        resData = []
        for i in range(0, dataLen):
            resData.append(_data[i])
        return [res, resData]
            
    def UploadWFM(self, iq):
        cdef complex16_t* src[2]
        I = iq.I
        Q = iq.Q
        nSamples = len(I)
        src[0] = <complex16_t*> malloc(nSamples * sizeof(complex16_t))
        src[1] = <complex16_t*> malloc(nSamples * sizeof(complex16_t))
        
        for i in range(0, nSamples):
            src[0][i].i = I[i]
            src[0][i].q = Q[i]
            src[0][i].i = 0
            src[0][i].q = 0
        
        status = LMS_UploadWFM(self._lms_device, <const void**>src, 2, nSamples, 0)
        
        free(src[0])
        free(src[1])
    def getDevice(self):
        return <uintptr_t>self._lms_device
        