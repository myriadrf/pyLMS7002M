
from setuptools import setup, find_packages

setup(
    name='pyLMS7002M',
    version='1.0.0',
    description='Python support for LMS7002M',
    url='https://github.com/myriadrf/pyLMS7002M',
    author='Lime Microsystems',
    packages=['pyLMS7002M'],
    install_requires=['pyserial','pyusb']
)

