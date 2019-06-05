import sys
import os


PLUGIN_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(PLUGIN_DIR)

from demo import widgets
