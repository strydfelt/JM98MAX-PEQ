"""Runtime hook to fix kivy_deps.angle PATH in PyInstaller onefile builds."""
import sys
import os
from os.path import join, isdir, dirname

# In PyInstaller onefile, sys._MEIPASS points to the extracted bundle
# The ANGLE DLLs are bundled at share/angle/bin relative to sys._MEIPASS
if hasattr(sys, '_MEIPASS'):
    angle_bin = join(sys._MEIPASS, 'share', 'angle', 'bin')
    if isdir(angle_bin):
        os.environ["PATH"] = angle_bin + os.pathsep + os.environ["PATH"]
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(angle_bin)

# Also fix site.USER_BASE if it's None
import site
if site.USER_BASE is None:
    # Set to a dummy path to avoid the TypeError in kivy_deps.angle
    site.USER_BASE = join(os.path.expanduser("~"), "AppData", "Roaming", "Python")