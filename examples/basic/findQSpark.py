from pyLMS7002M import *

print("Searching for QSpark...")
try:
    QSpark = QSpark()
except:
    print("QSpark not found")
    exit(1)
print("\QSpark info:")
QSpark.printInfo()                                 # print the QSpark board info
# QSpark.LMS7002_Reset()                             # reset the LMS7002M
lms7002 = QSpark.getLMS7002()                      # get the LMS7002M object
ver, rev, mask = lms7002.chipInfo                   # get the chip info
print("\nLMS7002M info:")
print("VER              : "+str(ver))
print("REV              : "+str(rev))
print("MASK             : "+str(mask))

