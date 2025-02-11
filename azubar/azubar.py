import inspect
from typing import overload, SupportsIndex, Union, Iterator, Generic, Literal, TypeVar
from collections.abc import Iterable
from .helper import Stack, Ansi
from queue import Queue
import atexit
import shutil

T = TypeVar("T")
terminal_size = shutil.get_terminal_size(fallback=(80, 24))
LINE_LENGTH = terminal_size.columns
LINE_COUNT = terminal_size.lines
OPEN_ERR_REMINDER = True
SHOW = True

class Bar:
    Icon = ['⋮⋰⋯⋱','|/-\\']
    Icon_i = 1
    Style = [['>','\033[D━>','━',' '],['','█','█',' ']]

class AzuBar:
    bars: Stack["prange"] = Stack()
    total = 0
    err: Queue[tuple[int, int, str]] = Queue()

class prange(Generic[T]):
    @overload
    def __init__(self, *,title:str) -> None: ...
    @overload
    def __init__(self, stop: SupportsIndex, /, *,title: str) -> None: ...
    @overload
    def __init__(self, start: SupportsIndex, stop: SupportsIndex, step: SupportsIndex = ..., /, *,title: str) -> None: ...
    @overload
    def __init__(self, obj: Iterable[T], /, *, title: str) -> None: ...

    def __init__(self, *obj: Union[Iterable[T], SupportsIndex] ,title: str):
        """Show bars while using

        Parameters
        ----------
        *obj : Iterable, SupportsIndex, Optional
            Automatically assign to start, stop, step, or obj. by default 1
        title : str
            The name of the bar.

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
        self.bar = Bar()
        self.id = AzuBar.bars.size()
        self.loc = get_lineno()
        self.title = title if isinstance(title, str) else str(title)

        # generator
        self.is_generator = False
        self.g_none = False
        self.g_temp = None
        self.g_end = False

        AzuBar.bars.push(self)
        AzuBar.total = max(AzuBar.total,self.id)
        if AzuBar.total >= LINE_COUNT:
            AzuBar.err.put((0,1,f"Err: The line of the terminal is not enough. (required: {AzuBar.total+1}, now: {LINE_COUNT})"))
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
                        self.stop = float('inf')
                        self.is_generator = True
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
                self.stop = self.start + 1
                if self.g_end == True:
                    self.start -= 1
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

    def __template(self, task: Literal["init","loop","done"]) -> str:
        I = self.start
        Total = self.stop
        bar = self.bar
        match task:
            case 'init' | 'loop':
                if Total == 0:
                    return f'[{self.title}]:[{Ansi.BLUE}>%s{Ansi.RESET}]{bar.Icon[bar.Icon_i][I%4]}{Ansi.YELLOW}%.2f%% {I}/{Total}{Ansi.RESET}                ' % ('\033[D━>' * int(20),float(100))
                else:
                    return f'[{self.title}]:[{Ansi.BLUE}>%s%s{Ansi.RESET}]{bar.Icon[bar.Icon_i][I%4]}{Ansi.YELLOW}%.2f%% {I}/{Total}{Ansi.RESET}                ' % ('\033[D━>' * int(I*20/Total), ' ' * (20-int(I*20/Total)),float(I/Total*100))
            case 'done':
                return f'[{self.title}]:[{Ansi.GREEN}%s{Ansi.RESET}]{Ansi.YELLOW}DONE {I}/{Total}{Ansi.RESET}               ' % ('━' * int(21))

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
                        s = "\n" + " "*LINE_LENGTH
                        print(s, end='',flush=True)
                    print(Ansi.UP*times, end="", flush=True)
                    AzuBar.total = self.id

            case "done":
                tail = Ansi.UP
                AzuBar.bars.pop()
                if AzuBar.bars.is_empty:
                    for _ in range(AzuBar.total):
                        s = "\n" + " "*LINE_LENGTH
                        print(s, end='',flush=True)
                    print(Ansi.UP*AzuBar.total, end="", flush=True)
                    tail = "\n"
                    AzuBar.total = 0

        s = head + add + self.__template(task) + tail
        print(s, end='',flush=True)
        call_err()


def get_lineno(depth: int= 2) -> tuple[int, str]:
    frame = inspect.currentframe()
    for _ in range(depth):
        frame = frame.f_back
    line_number = frame.f_lineno
    filename = inspect.getfile(frame)
    return line_number, filename

def loop(repeat: int= 1):
    """Update the the prange runs out of a for-loop

    Parameters
    ----------
    repeat : int, optional
        Repeat times, by default 1

    Warning:
        - loop() should not be used with for-loop, as for-loop will automatically update the progress bar.
        - loop() is solely responsible for updating the progress bar and does not handle the object's value.
    """
    for _ in range(repeat):
        if AzuBar.bars.is_empty == True:
            if OPEN_ERR_REMINDER == False: continue
            line_number, filename = get_lineno()
            AzuBar.err.put((line_number,2,f'Err in "{filename}"\n  Line {line_number}: Wrong amount of loop().'))
        else:
            self = AzuBar.bars.top()
            if self.auto == True:
                if OPEN_ERR_REMINDER == False: continue
                line_number, filename = get_lineno()
                AzuBar.err.put((line_number,3, f'Err in "{filename}"\n  Line {line_number}: loop() is for prange that is not in a for-loop.'))
            else:
                self.start += 1
                try:
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
        AzuBar.err.put((self.loc[0], 4, f'Err in "{self.loc[1]}"\n  Line {self.loc[0]}: prange( title= "{self.title}" ) didn\'t close.'))
    call_err()

atexit.register(inexit)