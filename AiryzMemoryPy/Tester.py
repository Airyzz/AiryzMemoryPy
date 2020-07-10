from AiryzMemoryPy import *

notepad = AiryzMemory("notepad")

print(notepad.read_float(0x1E03CBC0000))

notepad.write_float(0x1E03CBC0000, 150.0)
notepad.write_vector(0x1E03CBC0000, (150.0, 69.420, 100))
notepad.write_struct('ifff', 0x1E03CBC0000, (10, 100.0, 50.0, 32.0))

hModule = notepad.get_module_handle('notepad.exe')
notepad.get_module_info(hModule)

print(hex(notepad.get_base_address('ntdll.dll')))
print(hex(notepad.get_base_address()))

print("Attached to notepad")