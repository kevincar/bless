import os
import sys

project = "bless"
author = "Kevin Davis"
release = "0.3.0"

os.environ["BLESS_DOCS_BUILD"] = "1"
sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = []

autodoc_mock_imports = [
    "CoreBluetooth",
    "bleak",
    "bleak_winrt",
    "CoreFoundation",
    "dispatch",
    "dbus_next",
    "Foundation",
    "libdispatch",
    "objc",
    "pysetupdi",
    "pywin32",
    "win32api",
    "win32con",
    "win32file",
    "winreg",
    "winrt",
]
