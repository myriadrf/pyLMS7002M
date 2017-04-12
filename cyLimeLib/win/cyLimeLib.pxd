

cdef extern from "LimeSuite.h":
    ctypedef void lms_device_t
    ctypedef unsigned char  uint8_t
    ctypedef  size_t uintptr_t
    ctypedef char* lms_info_str_t

    int LMS_GetDeviceList(lms_info_str_t *dev_list)
    int LMS_Open(lms_device_t **device, lms_info_str_t info, void* args)
    int LMS_TransferLMS64C(lms_device_t *dev, int cmd, uint8_t* data, size_t *len)
    int LMS_Close(lms_device_t *device)

    int LMS_UploadWFM(lms_device_t *device, const void **samples, uint8_t chCount, size_t sample_count, int format)

cdef extern from "dataTypes.h" namespace "lime":
    ctypedef struct complex16_t:
        int i
        int q
    
