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

### Windows

The default driver Windows drivers for LimeSDR boards are not compatible with the Python module
pyUSB. Drivers can be changed by using the Zadig software.

* [Windows Vista/Win7/Win8 32/64](http://zadig.akeo.ie/downloads/zadig_2.1.0.exe)
* [Windows XP](http://zadig.akeo.ie/downloads/zadig_xp_2.1.0.exe)

When Zadig is run, click on Options->List All Devices, as shown in the figure below.

![Zadig List All Devices](/images/ListAllDevices.jpg)

Then select the LimeSDR and libusb-win32 from drop-down lists and click on Replace Driver button.

![Zadig select LimeSDR-USB](/images/LimeSDR-USB.jpg)

## Examples

* basic
** Find LimeSDR
** Find LMS7002EVB
** LimeSDR Tx CW
** LimeSDR Tx CW power out sweep
** LimeSDR Tx NCO 
** LimeSDR Tx NCO hopping
* Vector Network Analyser (VNA)

## Licensing

pyLMS7002M is copyright 2016 Lime Microsystems and provided under the Apache 2.0 License.
