"""
Main entry point for the PEQ Configurator Kivy application.
"""
import os
import sys

# Set up binary paths BEFORE any kivy imports
# This must happen before any kivy imports to fix ANGLE/GLEW/SDL2 binary paths
def _setup_binary_paths():
    """Set up binary paths for kivy_deps modules in PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to binaries in the PyInstaller bundle
    paths_to_add = [
        os.path.join(base_path, 'share', 'angle', 'bin'),
        os.path.join(base_path, 'share', 'glew', 'bin'),
        os.path.join(base_path, 'share', 'sdl2', 'bin'),
    ]
    
    # Add to PATH and DLL search directories
    for path in paths_to_add:
        if os.path.isdir(path):
            os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(path)
                except Exception:
                    pass

# Set up binary paths BEFORE any kivy imports
_setup_binary_paths()

"""
Main entry point for the PEQ Configurator Kivy application.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger

# Import our app modules
from peq_app import PEQConfiguratorApp


def main():
    """Main entry point."""
    Logger.info("PEQ Configurator: Starting application")
    
    # Set window size for desktop testing (will be ignored on Android)
    if not hasattr(sys, 'android'):
        Window.size = (400, 700)
        Window.minimum_width = 360
        Window.minimum_height = 600
    
    app = PEQConfiguratorApp()
    app.run()


if __name__ == '__main__':
    main()