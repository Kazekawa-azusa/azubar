"""
azubar
by Kazekawa-azusa
"""
from .azubar import prange, loop, BarLike, SpinnerLike

__author__ = "kazekawa-azusa"
__version__ = "0.0.3.2"
__license__ = "MIT"
__all__ = ['prange', 'loop', 'BarLike', 'SpinnerLike']

def __dir__():
    return __all__ + ['__author__', '__version__']