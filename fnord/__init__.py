"""
Fnord Tracker - The Sacred Fnord Database Module

Hail Eris! All Hail Discordia!

This package helps track the elusive fnords that lurk in the corners
of your vision. They are everywhere. They are nowhere. They are fnord.

The fnords thank you for your service.
"""

__version__ = "23.5.0"
__author__ = "The Fnord Keepers"
__license__ = "WTFPL"

# Import the sacred fnord models
from fnord.models import FnordSighting

# All hail the fnord!
__all__ = ["FnordSighting", "__version__"]

# Eris blesses this module
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Fnord!
logger.debug("Fnord tracker initialized. All hail Discordia!")
