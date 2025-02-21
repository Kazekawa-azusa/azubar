# azubar
A progerss bar creator.

![411804828-765f16b6-c29e-4305-86d7-bf7e8490b16e](https://github.com/user-attachments/assets/143388f7-6392-41f5-a2c6-599c6bc2a36b)


## How to use
### Import
```
from azubar import prange, loop
```
### Use it like normal Iterable object in a for-loop
```
my_list = ['A','B','C']
for i in prange(mylist, title='Title')
  ...
```
### Use it like `range` in a for-loop
```
for i in prange(5, title='Title')
  ... 
```
### Use it without a for-loop
```
prange(1,6,2, title='Title')
...
loop()
...
loop()
...
loop()
...
```
## Warning
- The terminal must support ANSI escape sequences; otherwise, garbled characters will appear.
- Please refrain from outputting to the terminal while using `prange`, as this functionality is not supported.
- The progress bar will be displayed while you create a `prange` object. Please ensure that you create the `prange` object in the appropriate location.
- If you use `prange` without a for-loop, you need to manually add the correct number of `loop()` calls.
- `azubar` will remind you of the incorrect use of `prange` and `loop` that you make.
- If you would like to opt out of receiving reminders or hide the bars, please use the code provided below.
  ```
  from azubar import azubar
  azubar.OPEN_ERR_REMINDER = False # Close the reminder
  azubar.SHOW = False # Hide the azubar
  ```
  
## Install
```
pip install azubar
```
