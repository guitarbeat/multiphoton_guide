"""
Pages package for the Multiphoton Microscopy Guide application.
This package contains page modules that are used by the navigation system.
"""

from modules.pages.laser_power_page import laser_power_page
from modules.pages.pulse_width_page import pulse_width_page
from modules.pages.fluorescence_page import fluorescence_page
from modules.pages.rig_log_page import rig_log_page
from modules.pages.reference_page import reference_page
from modules.pages.usaf_analyzer_page import usaf_analyzer_page

__all__ = [
    'laser_power_page',
    'pulse_width_page',
    'fluorescence_page',
    'rig_log_page',
    'reference_page',
    'usaf_analyzer_page'
]
