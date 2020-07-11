from AiryzMemoryPy import *
from typing import NamedTuple, get_type_hints
from ctypes import *
from dataclasses import dataclass

import time



class Vector3(metaclass=MetaStruct):
    x = float();
    y = float();
    z = float()

class Camera(metaclass=MetaStruct):
    pos = Vector3()
    ass = padding(4)
    rot = float()

    def print_position(self):
        print("Camera Position -> " + str(self.pos.x) + ', ' + str(self.pos.y) + ', ' + str(self.pos.z))

#Attach to game
bo2 = AiryzMemory("t6mpv43")
notepad = AiryzMemory("notepad")

#Check architecture 

print("Testing camera pointer")
base = bo2.get_base_address()
address = bo2.read_pointer((base + 0x2D83A00, 0xEBC70))

print("Address: " + hex(address))
#data = bo2.read_struct('fff', address)

cam = bo2.read_class(Camera, address)


print("Camera Object:")
print(cam.pos.x)
print(cam.pos.y)
print(cam.pos.z)
print(cam.rot)

cam.print_position()

print('-----')

print("Testing module addresses")

print("t6mpv43.exe = " + hex(bo2.get_base_address()))

print("notepad.exe = " + hex(notepad.get_base_address()))

print("notepad.exe -> ntdll.dll = " + hex(notepad.get_base_address('ntdll.dll')))

