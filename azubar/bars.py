from collections.abc import Iterable
import re
from azubar.helper import Ansi
from itertools import cycle
import string

class  _PartialFormatter(string.Formatter):
    def __init__(self, missing_format='{{{key}}}'):
        super().__init__()
        self.missing_format = missing_format

    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            if key in kwargs:
                return kwargs[key]
            else:
                return self.missing_format.format(key=key)
        return super().get_value(key, args, kwargs)

class _Formatter(str):
    def __new__(cls, content: str, missing_format='{{{key}}}'):
        obj = super().__new__(cls, content)
        obj.__missing_format = missing_format
        return obj

    def pformat(self, **kwargs):
        return _Formatter(_PartialFormatter(self.__missing_format).format(self, **kwargs), self.__missing_format)

class Cycled:
    def __init__(self, data):
        if not data:
            raise ValueError("Cycled cannot be empty.")
        self.data = list(data)

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError("Index must be an integer.")
        return self.data[index % len(self.data)]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        while True:
            for item in self.data:
                yield item

    def __repr__(self):
        return f"Cycled({self.data})"

def actual_len(s: str) -> int:
    """the actual length of the string

    Parameters
    ----------
    s : str
        aim string.

    Returns
    -------
    int
        the length of the string without counting ansi codes
    """
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mKJHABCD]')
    return len(ansi_escape.sub('', s))

class BarLike():
    def __init__(self,
                 left: str | Iterable[str] = "=",
                 right: str | Iterable[str] = " ",
                 mid: str | Iterable[str] = '',
                 end_left: str | Iterable[str] | None = None,
                 ):
        self.bar_l = left
        self.bar_m = mid
        self.bar_r = right
        self.end_l = left if end_left is None else end_left
    
    def make(self, start: int, stop: int, length: int = 20):
        l_len = int(start/stop*length) if stop > start else length
        r_len = length - actual_len(self.bar_m) - l_len
        bar = f'{self.end_l*l_len}' if start == stop else f'{self.bar_l*l_len}'
        bar += f'{self.bar_m}' if stop > start else ''
        bar += f'{self.bar_r*r_len}'
        return bar
    
class SpinnerLike():
    def __init__(self, spinner: Iterable[str], color: Ansi | None = None):
        self.spinner = cycle(spinner)
        self.color = '' if color is None else color

    def make(self, start: int | None = None, stop: int | None = None):
        # if start is None or stop is None:
        return self.color + next(self.spinner) + Ansi.RESET
        # else:
        #     return self.color + self.spinner[int(start/stop)] + Ansi.RESET
