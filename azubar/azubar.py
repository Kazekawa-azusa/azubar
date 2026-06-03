import inspect
from typing import get_args, overload, SupportsIndex, Union, Iterator, Generic, Literal, TypeVar
from collections.abc import Iterable

from azubar.bars import _Formatter, BarLike, SpinnerLike, actual_len
from .helper import ANSI_DICT, Stack, Ansi, _type_checker
from queue import Queue
import atexit
import shutil
import re
from wcwidth import wcswidth

__all__ = ['prange', 'loop']

terminal_size = shutil.get_terminal_size(fallback=(80, 4))
LINE_LENGTH = terminal_size.columns
LINE_COUNT = terminal_size.lines
OPEN_ERR_REMINDER = True
SHOW = True

def real_terminal_len(text: str) -> int:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)
    
    clean_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_text)
    
    width = wcswidth(clean_text)
    
    return width if width >= 0 else len(clean_text)

class AzuBar:
    bars: Stack["prange"] = Stack()
    total = 0
    err: Queue[tuple[int, int, str]] = Queue()

ERRS = Literal['warning', 'notice']
_Status = Literal['done', 'miss', 'over']
IGNORE_ERR: ERRS = None
T = TypeVar("T")

class prange(Generic[T]):
    @overload
    def __init__(self, *,title:str, burn: bool = False, total: int | None = None, bar_style: BarLike | None = None, spinner_style: SpinnerLike | None = None, bar_format: dict | None = None, ignore_err: Iterable[ERRS] | ERRS | None = None) -> None: ...
    @overload
    def __init__(self, stop: SupportsIndex, /, *,title: str, burn: bool = False, total: int | None = None, bar_style: BarLike | None = None, spinner_style: SpinnerLike | None = None, bar_format: dict | None = None, ignore_err: Iterable[ERRS] | ERRS | None = None) -> None: ...
    @overload
    def __init__(self, start: SupportsIndex, stop: SupportsIndex, step: SupportsIndex = ..., /, *,title: str, burn: bool = False, total: int | None = None, bar_style: BarLike | None = None, spinner_style: SpinnerLike | None = None, bar_format: dict | None = None, ignore_err: Iterable[ERRS] | ERRS | None = None) -> None: ...
    @overload
    def __init__(self, obj: Iterable[T], /, *, title: str, burn: bool = False, total: int | None = None, bar_style: BarLike | None = None, spinner_style: SpinnerLike | None = None, bar_format: dict | None = None, ignore_err: Iterable[ERRS] | ERRS | None = None) -> None: ...

    def __init__(self, *obj: Union[Iterable[T], SupportsIndex] ,title: str, burn: bool = False, total: int | None = None, bar_style: BarLike | None = None, spinner_style: SpinnerLike | None = None, bar_format: dict | None = None, ignore_err: Iterable[ERRS] | ERRS | None = None):
        """Show bars while using

        Parameters
        ----------
        *obj : Iterable, SupportsIndex, optional
            Automatically assign to start, stop, step, or obj. by default 1
        title : str
            The name of the bar.
        burn : bool, optional
            While True, ensure that the bar disappears when it reaches the end. by default False
        total : int, optional
            Set the size of the bar when the `obj` is a generator; otherwise, do nothing.
        bar_style : _BarLike, optional
            The style of the bar.
        spinner_style : _SpinnerLike, optional
            The style of the spinner.
        bar_format: dict, optional
            The format of the bar.

        Using
        -----
        - With for-loop

        >>> my_list = ['A','B','C']
            for i in prange(mylist, title='Title')
                ...

        use it like 'range', but 'title' is needed
        >>> for i in prange(5, title='Title')
                ... 
        
        - Without for-loop

        >>> prange(1,6,2, title='Title')
            ...
            loop()
            ...
            loop()
            ...
            loop()
            ...

            Warning:
                You have to add loop() by yourself.
                In this case, the prange run 3 times, so 3 loop() is needed.
        """
        self.auto = False
        self.bar = BarLike(f'{Ansi.BLUE}━{Ansi.RESET}',' ',f"{Ansi.BLUE}>{Ansi.RESET}",f'{Ansi.GREEN}━{Ansi.RESET}') if bar_style is None else bar_style
        self.spinner = SpinnerLike('|/-\\') if spinner_style is None else spinner_style
        self.id = AzuBar.bars.size()
        self.loc = get_lineno()
        self.title = _type_checker(title,'title',str)
        self.burn = _type_checker(burn, 'burn', bool)
        self.status = 'done'
        self.ignor_err = tuple()
        for err in (ignore_err, IGNORE_ERR):
            match err:
                case None:
                    pass
                case str():
                    self.ignor_err += (err,)
                case err if isinstance(err, Iterable):
                    self.ignor_err += tuple((i for i in err))
                case _:
                    err_msg = f"'{ignore_err}' should be type 'None, str, Iterable', but got '{type(ignore_err).__name__}'"
                    raise TypeError(err_msg)

        # generator
        self.is_generator = False
        self.g_temp = None
        self.g_end = False
        self.g_stop = None

        AzuBar.bars.push(self)
        AzuBar.total = max(AzuBar.total,self.id)
        if AzuBar.total >= LINE_COUNT:
            if 'warning' not in self.ignor_err: AzuBar.err.put((0,1,f"Err: The line of the terminal is not enough. (required: {AzuBar.total+1}, now: {LINE_COUNT})"))
        match len(obj):
            case 0:
                self.obj = enumerate(range(0,1,1))
                self.start = 0
                self.stop = 1
                self.step = 1
            case 1:
                if isinstance(obj[0], Iterable):
                    self.obj = enumerate(obj[0])
                    self.start = 0
                    self.step = 1
                    try:
                        self.stop = len(obj[0])
                    except TypeError:
                        # generator
                        self.is_generator = True
                        if total is None:
                            self.stop = float('inf')
                        else:
                            self.stop = total
                            self.g_stop = self.stop
                        try:
                            index, self.g_temp = next(self.obj)
                        except StopIteration:
                            self.stop = 0

                else:
                    self.start = 0
                    self.stop = int(obj[0])
                    self.step = 1
                    self.obj = enumerate(range(self.stop))
            case 2 | 3:
                temp_range = range(int(obj[0]), int(obj[1]), int(obj[2]) if len(obj) == 3 else 1)
                self.obj = enumerate(temp_range)
                self.start = 0
                self.stop = len(temp_range)
                self.step = 1
            case _:
                raise TypeError("prange expected 1, 2 or 3 arguments, got {}".format(len(obj)))
        
        if self.stop == 0:
            self.__cout('init')
            self.__cout('done')
        else:
            self.__cout('init')
    
    def __len__(self):
        # if self.is_generator == True and self.g_stop is None:
        return self.stop

    @property
    def bar_format(self) -> _Formatter:
        """format dict"""
        return _Formatter('[{title}]:[{bar}]{spinner}{YELLOW}{ratio}% {i}/{total}{RESET}')
    
    def __eq__(self, obj):
        if isinstance(obj, prange):
            if self.id == obj.id:
                return True
            else:
                return False
        elif isinstance(obj, int):
            if self.id == obj:
                return True
            else:
                return False
        else:
            raise TypeError('can compare prange, int (not "{}") to prange'.format(type(obj).__name__))
    
    def __str__(self):
        return "prange({})".format(self.__dict__)
    
    def __iter__(self) -> Iterator[T]:
        self.auto = True
        return self

    def __next__(self) -> T:
        if self.stop == 0:
            raise StopIteration

        match self.is_generator:
            case True:
                self.__cout('loop')
                self.start += self.step
                self.stop = self.stop if self.stop > self.start and self.stop != float('inf') else self.start + 1
                if self.g_end == True:
                    self.start -= 1
                    if self.g_stop is not None and self.g_stop != self.start:
                        line_number, filename = self.loc
                        if 'notice' not in self.ignor_err: AzuBar.err.put((line_number,2,f'Notice in "{filename}", line {line_number}:\n  total doesn\'t match the generator. ({self.g_stop} != {self.start})'))
                    self.stop = self.start
                    self.__cout('done')
                    raise StopIteration

                try:
                    val = self.g_temp
                    index, self.g_temp = next(self.obj)
                except StopIteration as e:
                    self.g_end = True
                    if self.auto == False:
                        self.start -= 1
                        next(self)
                return val

            case False:
                if self.start < self.stop:
                    self.__cout('loop')
                    self.start += self.step
                    index, val = next(self.obj)
                    return val
                else:
                    self.__cout('done')
                    raise StopIteration
    
    def __format_num(self, value: float | int, width: int = 5, decimals: int = 0, just: Literal['left', 'right'] = 'right') -> str:
        raw = f"{value:.{decimals}f}"
        trimmed = raw.rstrip(' ').rstrip('.')
        match just:
            case 'left':
                return trimmed.ljust(width)
            case 'right':
                return trimmed.rjust(width)
            case _:
                return trimmed.rjust(width)
    
    def __fill(self, outer_len):
        format_str = self.bar_format
        try:
            self.__len_i = max(len(str(self.stop)), self.__len_i)
        except AttributeError:
            self.__len_i = len(str(self.stop))
        format_str = format_str.pformat(**ANSI_DICT, title= self.title, i=self.__format_num(self.start,self.__len_i), total=self.__format_num(self.stop,self.__len_i, just='left'))
        if self.stop == 0:
            format_str = format_str.pformat(ratio= f'{(100):6.2f}')
        else:
            format_str = format_str.pformat(ratio= f'{(self.start*100/self.stop):6.2f}')
        format_str = format_str.pformat(spinner=" ") if self.start == self.stop else format_str.pformat(spinner= self.spinner.make())
        lenth = real_terminal_len(format_str) + outer_len - 4 # {bar}
        format_str = format_str.format(bar=self.bar.make(self.start, self.stop,LINE_LENGTH-lenth))
        self.status = 'done'
        return format_str

    def __template(self, task: Literal["init","loop","done"], outer_len: int) -> str:
        match task:
            case 'init' | 'loop' | 'done':
                return self.__fill(outer_len)

    def __cout(self, task: Literal["init","loop","done"]) -> None:
        """print control"""
        if SHOW == False:
            if task == 'done':
                AzuBar.bars.pop()
                if AzuBar.bars.is_empty:
                    AzuBar.total = 0
            return

        head = "\r"
        add = " >"*(self.id)
        tail = ""
        match task:
            case "init"|"loop":
                if AzuBar.bars.top() == self.id and task == 'init' and self.id != 0:
                    add = "\n" + add
                elif AzuBar.total > self.id:
                    times = AzuBar.total - self.id
                    for _ in range(times):
                        if AzuBar.bars.top() != self.id:
                            AzuBar.bars.pop()
                            s = '\r' + " "*LINE_LENGTH
                        else:
                            s = "\n" + " "*LINE_LENGTH
                        print(s, end='',flush=True)
                    print(Ansi.UP*times, end="", flush=True)
                    AzuBar.total = self.id
                s = head + add + self.__template(task, self.id*2) + tail

            case "done":
                tail = Ansi.UP
                if AzuBar.bars.size() == 1:
                    for _ in range(AzuBar.total):
                        s = "\n" + " "*LINE_LENGTH
                        print(s, end='',flush=True)
                    print(Ansi.UP*AzuBar.total, end="", flush=True)
                    tail = "\n"
                    AzuBar.total = 0
                if self.burn == True and AzuBar.bars.size() == 1:
                    s = "\r" + " "*LINE_LENGTH
                else:
                    while AzuBar.bars.top() != self.id: # deal with unclosed nested bar
                        s = "\r" + " "*LINE_LENGTH
                        print(s, end=Ansi.UP, flush=True)
                        AzuBar.bars.pop()
                    s = head + add + self.__template(task, len(add)) + tail
                AzuBar.bars.pop()
        
        print(s, end='',flush=True)
        call_err()


def get_lineno(depth: int= 2) -> tuple[int, str]:
    frame = inspect.currentframe()
    for _ in range(depth):
        frame = frame.f_back
    line_number = frame.f_lineno
    filename = inspect.getfile(frame)
    return line_number, filename

def loop(repeat: int= 1, status: _Status= 'done'):
    """Update the the prange runs out of a for-loop

    Parameters
    ----------
    repeat : int, optional
        Repeat times, by default 1

    Warning:
        - loop() should not be used with for-loop, as for-loop will automatically update the progress bar.
        - loop() is solely responsible for updating the progress bar and does not handle the object's value.
    """
    _type_checker(repeat, 'repeat', int)
    _type_checker(status, 'status', str)
    if status not in get_args(_Status): raise ValueError(f"'status' must be '{', '.join(get_args(_Status))}'")
    ignor_err = ''
    for _ in range(repeat):
        if AzuBar.bars.is_empty == True:
            if OPEN_ERR_REMINDER == False: continue
            line_number, filename = get_lineno()
            if 'warning' not in ignor_err: AzuBar.err.put((line_number,2,f'Err in "{filename}", line {line_number}:\n  Wrong amount of loop().'))
        else:
            self = AzuBar.bars.top()
            ignor_err = self.ignor_err
            if self.auto == True:
                if OPEN_ERR_REMINDER == False: continue
                line_number, filename = get_lineno()
                if 'warning' not in self.ignor_err: AzuBar.err.put((line_number,3, f'Err in "{filename}", line {line_number}:\n  loop() is for prange that is not in a for-loop.'))
            else:
                self.start += 1
                try:
                    self.status = status
                    next(self)
                except StopIteration:
                    pass
                self.start -= 1
    call_err()

def call_err():
    """print Err after the prange.
    """
    if SHOW == False or OPEN_ERR_REMINDER == False: return
    
    if AzuBar.bars.is_empty:
        done:set[tuple[int,int]] = set()
        while not AzuBar.err.empty():
            err = AzuBar.err.get()
            if err[0] == -1 or err[0:2] not in done:
                done.add(err[0:2])
                s = Ansi.RED + err[2] + Ansi.RESET
                print(s, flush=True)

def inexit():
    if SHOW == False: return
    if not AzuBar.bars.empty():
        for _ in range(AzuBar.total + 2 - AzuBar.bars.size()):
            print(flush=True)
        AzuBar.total = 0
    
    if OPEN_ERR_REMINDER == False: return
    while not AzuBar.bars.empty():
        self = AzuBar.bars.pop()
        if 'warning' not in self.ignor_err: AzuBar.err.put((self.loc[0], 4, f'Err in "{self.loc[1]}", line {self.loc[0]}:\n  prange( title= "{self.title}" ) didn\'t close.'))
    call_err()

atexit.register(inexit)