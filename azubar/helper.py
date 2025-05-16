from collections.abc import Iterable
from typing import Generic, TypeVar, Callable, ParamSpec, TypeVar, cast, Any
T = TypeVar("T")

def _type_checker(obj: T, name: str, class_or_tuple: object):
    if isinstance(obj, class_or_tuple):
        return obj
    else:
        if isinstance(class_or_tuple, tuple):
            expected_type = ", ".join(cls.__name__ for cls in class_or_tuple)
        else:
            expected_type = class_or_tuple.__name__

        err_msg = f"'{name}' should be type '{expected_type}', but got '{type(obj).__name__}'"
        raise TypeError(err_msg)

class Stack(Generic[T]):
    def __init__(self, initial_data: T = None):
        self.stack = []
        if initial_data is None: initial_data = []
        self.initial_data = initial_data

        if isinstance(initial_data, Iterable):
            self.stack = list(initial_data)
        else:
            raise NotImplementedError('Initial data must be iterable')
    def __repr__(self):
        return "Stack(initial_data={!r})".format(self.initial_data)
    
    def __str__(self):
        return "stack({})".format(self.stack)

    def __len__(self):
        return len(self.stack)

    def __getitem__(self, i) -> T:
        return self.stack[i]

    @property
    def is_empty(self):
        return len(self.stack) == 0
     
    def push(self, data: T):
        self.stack.append(data)

    def pop(self) -> T:
        if not self.is_empty:
            return self.stack.pop()

    def top(self) -> T:
        if not self.is_empty:
            return self.stack[-1]
    
    def empty(self):
        return len(self.stack) == 0

    def size(self):
        return len(self)
    
    def get(self, i) -> T:
        return self.stack[i]
    
class Ansi():
    PURPLE    = '\033[95m'
    BLUE      = '\033[94m'
    GREEN     = '\033[92m'
    YELLOW    = '\033[93m'
    RED       = '\033[91m'
    UNDERLINE = '\033[4m'
    RESET     = '\033[0m'
    UP        = '\033[A'
    DOWN      = '\033[B'
    RIGHT     = '\033[C'
    LEFT      = '\033[D'
    CLEAR     = '\033[K'
    SET       = '\033[y;xH'
    CLS       = '\033[2J'
    BOLD      = "\033[1m"

ANSI_DICT = {
    key: value
    for key, value in vars(Ansi).items()
    if not key.startswith("__")
}