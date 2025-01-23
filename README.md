# azubar
A progerss bar creator.

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
- The progress bar will be displayed while you create a `prange` object. Please ensure that you create the `prange` object in the appropriate location.
- If you use `prange` without a for-loop, you need to manually add the correct number of `loop()` calls.
- `azubar` will remind you of the incorrect use of `prange` and `loop` that you make.
- If you would like to opt out of receiving reminders or hide the bars, please use the code provided below.
  ```
  from azubar import azubar
  azubar.OPEN_ERR_REMINDER = False # Close the reminder
  azubar.SHOW = False # Hide the azubar
  ```
