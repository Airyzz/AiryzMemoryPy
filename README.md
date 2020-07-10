# AiryzMemoryPy
A simple python library for manipulating memory of external processes

## To Do:
- test on x86 applications.
- create read_pointer function
- Make write_struct automatically generate the format string
- NOP function
- Remove / Replace Protection


## How to use:
1. Import the library
```py
from AiryzMemoryPy import *
```

2. Create an instance of AiryzMemory
```py
notepad = AiryzMemory("notepad")
```

- Reading Data:
```py
value = notepad.read_float(address)
value = notepad.read_int(address)
value = notepad.read_struct('fff', address)
```

- Writing Data:
```py
notepad.write_float(address, value)
notepad.write_int(address, value)
notepad.write_vector(address, (value1, value2, value3, [...]))
notepad.write_struct('iff', address, (integer1, float1, float2))
```
