from pyLMS7002M import *

print("Searching for LimeSDR...")
try:
    limeSDR = LimeSDRMini()
except:
    print("LimeSDRMini not found")
    exit(1)
print("\nLimeSDRMini info:")
limeSDR.printInfo()                                 # print the LimeSDR board info
limeSDR.LMS7002_Reset()                             # reset the LMS7002M
lms7002 = limeSDR.getLMS7002()                      # get the LMS7002M object
ver, rev, mask = lms7002.chipInfo                   # get the chip info
print("\nLMS7002M info:")
print("VER              : "+str(ver))
print("REV              : "+str(rev))
print("MASK             : "+str(mask))

