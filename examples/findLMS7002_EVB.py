from pyLMS7002M import *

print("Searching for LMS7002 EVB...")
ports = LMS7002_EVB.findLMS7002() # Find LMS7002 evaluation boards
if len(ports)==0:
    print "LMS7002 EVB not found"
    exit(1)
if len(ports)>1:
    print "WARNING : Multiple LMS7002 EVBs found : "+str(ports)+".\nSet LMS7002_COMPort to explicit value to use a specific device.\nUsing EVB at port " + ports[0]
LMS7002_COMPort = ports[0]
lms7002_evb = LMS7002_EVB(portName=LMS7002_COMPort) # open communication to LMS7002M board
print("\nLMS7002M_EVB info:")
lms7002_evb.printInfo()                             # print the EVB board info
lms7002_evb.LMS7002_Reset()                         # reset the LMS7002M
lms7002 = lms7002_evb.getLMS7002()                  # get the LMS7002M object
ver, rev, mask = lms7002.chipInfo                   # get the chip info
print("\nLMS7002M info:")
print("VER              : "+str(ver))
print("REV              : "+str(rev))
print("MASK             : "+str(mask))


