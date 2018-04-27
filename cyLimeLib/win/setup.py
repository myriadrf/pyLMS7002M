# setup.py file
import sys
import os
import shutil

# from distutils.core import setup
# from distutils.extension import Extension

try:
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension

from Cython.Distutils import build_ext

# clean previous build
for root, dirs, files in os.walk(".", topdown=False):
    for name in files:
        if (name.startswith("cyLimeLib") and not(name.endswith(".pyx") or name.endswith(".pxd"))):
            os.remove(os.path.join(root, name))
    for name in dirs:
        if (name == "build"):
            shutil.rmtree(name)

setup(
    name = "cyLimeLib",
    version='1.0.0',
    description='Cython support for LimeAPI',
    url='https://github.com/myriadrf/pyLMS7002M',
    author='Lime Microsystems',
    cmdclass = {'build_ext': build_ext},
    ext_modules = [
        Extension("cyLimeLib", 
                  sources=["cyLimeLib.pyx"],
                  libraries=["LimeSuite"],
                  language="c++",
                  extra_compile_args=["-O2"]
             )
        ]
)  
