"""
azubar
by Kazekawa-azusa
"""
from .azubar import prange, loop

__author__ = "kazekawa-azusa"
__version__ = "0.0.3.1"
__license__ = "MIT"
__all__ = ['prange', 'loop']

def __dir__():
    return __all__ + ['__author__', '__version__']