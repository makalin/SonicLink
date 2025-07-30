"""
SonicLink: High-Speed Ultrasonic Data Communication System

A secure, high-speed communication system using ultrasonic sound waves
for data transfer between computers.
"""

__version__ = "1.0.0"
__author__ = "SonicLink Team"
__email__ = "contact@soniclink.dev"

from .core import SonicLinkSender, SonicLinkReceiver
from .compression import HuffmanCompressor
from .encryption import CryptoManager
from .modulation import OFDMModulator, OFDMDemodulator
from .audio import AudioManager
from .utils import FrequencyRange, Config

__all__ = [
    'SonicLinkSender',
    'SonicLinkReceiver', 
    'HuffmanCompressor',
    'CryptoManager',
    'OFDMModulator',
    'OFDMDemodulator',
    'AudioManager',
    'FrequencyRange',
    'Config'
] 