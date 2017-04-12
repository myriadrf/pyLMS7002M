# LMS7002M Python package

The pyLMS7002M Python package is platform-independent, and is intended for fast prototyping
and algorithm development. It provides low level register access and high level convenience functions
for controlling the LMS7002M chip and evaluation boards. Supported evaluation boards are:

* LMS7002_EVB
* LimeSDR

The package consists of Python classes which correspond to physical or logical entities. For
example, each module of LMS7002M (AFE, SXT, TRF, ...) is a class. The LMS7002M chip is also a
class containing instances of on-chip modules. The evaluation board class contains instances of
on-board chips, such as LMS7002, ADF4002, etc. Classes follow the hierarchy and logical
organization from evaluation board down to on-chip register level.

## Installation

The pyLMS7002M package is installed in a usual way:

  python setup.py install

Module installation can be verified from Python:

  python
  >>> from pyLMS7002M import *

If there is no error, the module is correctly installed.


## USB communications

USB communication can be established in two ways.

### Direct

Python communicates directly to the USB driver. This is the simplest and recommended option.

* Pros: Lightweight solution, simple installation
* Cons: Windows users - other applications that are communicating with LimeSDR (such as
LimeSuiteGUI and PothosSDR) use LimeSDR-USB Windows driver. The pyLMS7002M cannot use this driver. This
means that the user has to change the driver each time he/she switches from using
pyLMS7002M library to using e.g. LimeSuiteGUI, and vice versa.

With Linux use there are no problems, since all applications use the same driver.-

### Via LimeAPI

Python communicates to the LimeAPI library, which communicates to the USB driver.

* Pros: Windows users: No need to change the drivers. LimeSDR-USB Windows drivers can be used both for pyPLS7002M library, and
other applications such as LimeSuiteGUI and PothosSDR.
* Cons: More complicated installation and setup.

With Linux use there is no advantage, since all applications use the same driver.

## Drivers

### Linux

Communication is via libusb and can be direct or via the LimeAPI.

### Windows

#### USB communication via LimeAPI

This option is recommended only for Windows users that frequently use both pyLMS7002M python
library and other applications for communication with LimeSDR, such as LimeSuiteGUI, or
PothosSDR.

### USB direct communication

This is the preferred option.

The default Windows drivers for LimeSDR boards are not compatible with the Python module
pyUSB. Drivers can be changed by using the Zadig software.

* [Windows Vista/Win7/Win8 32/64](http://zadig.akeo.ie/downloads/zadig_2.1.0.exe)
* [Windows XP](http://zadig.akeo.ie/downloads/zadig_xp_2.1.0.exe)

When Zadig is run, click on Options->List All Devices, as shown in the figure below.

![Zadig List All Devices](/images/ListAllDevices.jpg)

Then select the LimeSDR and libusb-win32 from drop-down lists and click on Replace Driver button.

![Zadig select LimeSDR-USB](/images/LimeSDR-USB.jpg)

## Examples

* basic
  * Find LimeSDR
  * Find LMS7002EVB
  * LimeSDR Tx CW
  * LimeSDR Tx CW power out sweep
  * LimeSDR Tx NCO 
  * LimeSDR Tx NCO hopping
* Vector Network Analyser (VNA)

## Licensing

pyLMS7002M is copyright 2016, 2017 Lime Microsystems and provided under the Apache 2.0 License.
