import subprocess;
from ctypes import *
from ctypes.wintypes import *
from struct import *
import platform
import collections

k32 = windll.kernel32

OpenProcess = k32.OpenProcess
OpenProcess.argtypes = [DWORD,BOOL,DWORD]
OpenProcess.restype = HANDLE

IsWow64Process = k32.IsWow64Process

long = c_long
byte = c_byte
double = c_double
char = c_char
short = c_short
ushort = c_ushort

class padding():
    size = 0;
    def __init__(self, _size):
        self.size = _size


ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [HANDLE,LPCVOID,c_void_p,c_size_t,POINTER(c_size_t)]
ReadProcessMemory.restype = BOOL

WriteProcessMemory = k32.WriteProcessMemory
WriteProcessMemory.argtypes = [HANDLE,LPCVOID,c_void_p,c_size_t,POINTER(c_size_t)]

EnumProcessModules = windll.psapi.EnumProcessModules
EnumProcessModulesEx = windll.psapi.EnumProcessModulesEx

GetModuleBaseNameA = windll.psapi.GetModuleBaseNameA
GetModuleBaseNameA.argtypes = [HANDLE,LPCVOID,LPCVOID,DWORD]

GetModuleInformation = windll.psapi.GetModuleInformation
GetModuleInformation.argtypes = [HANDLE,LPCVOID,LPCVOID,POINTER(DWORD)]

class MetaStruct(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(self, name, bases, classdict):
        classdict['__ordered__'] = [key for key in classdict.keys()
                if key not in ('__module__', '__qualname__')]
        return type.__new__(self, name, bases, classdict)

class MEMORY_BASIC_INFORMATION(Structure):
    _fields_ = [("BaseAddress", LPVOID), 
                ("AllocationBase", LPVOID),
                ("AllocationProtect", DWORD),
                ("RegionSize", DWORD),
                ("State", DWORD),
                ("Protect", DWORD),
                ("Type", DWORD),]

class MODULEINFO(Structure):
    _fields_ = [("lpBaseOfDll", LPCVOID),
                ("SizeOfImage", DWORD),
                ("EntryPoint", LPCVOID)]

class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [("Length", DWORD),
                ("SecDescriptor", LPVOID),
                ("InheritHandle", BOOL)]

class AiryzMemory():
    
    def __init__(self, processName):
        self.pid = self.get_pid(processName)
        self.get_handle(self.pid)
        
    #Process Info
    def get_pid(self, processName):
        """ Get the ID of the process """
        #Use powershell to get Process ID. its a bit janky, but it was the fastest way I could find
        process=subprocess.Popen(["powershell","get-process " + processName + " | Format-Table -Property ID -HideTableHeaders"],stdout=subprocess.PIPE);
        result=str(process.communicate()[0])

        #filter out all non numerical characters
        pid_string = ''.join(i for i in result if i.isdigit())
        pid = int(pid_string)
        return pid
    
    def get_handle(self, pid):
        """ Get an ALL_ACCESS Handle to the process """
        PROCESS_ALL_ACCESS = 0x001F0FFF
        self.hProcess = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if self.hProcess:
            return
        else:
            print ("Failed: Get Handle - Error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)

    def list_all_modules(self):
        LIST_MODULES_ALL = 0x03
        if self.hProcess:
            hModules = (c_ulonglong * 250)()
           
            needed = DWORD()
            EnumProcessModulesEx(self.hProcess, byref(hModules), sizeof(hModules), byref(needed), LIST_MODULES_ALL)
            return hModules

    def get_module_handle(self, name):
        mod_name = str.encode(name)

        hModules = self.list_all_modules();
        for i in range(len(hModules)):
            if hModules[i] is not 0:
                modname = create_string_buffer(255)
                if(GetModuleBaseNameA(self.hProcess, hModules[i], byref(modname), sizeof(modname)) == 0):
                    print("Failed: Get Module Base Name - Error code: " + str(windll.kernel32.GetLastError()))
                    windll.kernel32.SetLastError(10000)

                if modname.value == mod_name:
                    return hModules[i];
        return 0;
    
    def __is_os_64bit(self):
        return platform.machine().endswith('64')

    def is_process_64bit(self):
        
        if not self.__is_os_64bit():
            return False
        i = c_int()
        IsWow64Process(self.hProcess, byref(i))
        return i.value == 0


    def get_module_info(self, hModule):
        info = MODULEINFO();
        size = DWORD()
        GetModuleInformation(self.hProcess, hModule, byref(info), byref(size))
        return info;

    def get_base_address(self, moduleName=None):
        if moduleName == None:
            modules = self.list_all_modules()
            hModule = modules[0]
            info = self.get_module_info(hModule)
            return info.lpBaseOfDll
        else:
            hModule = self.get_module_handle(moduleName)
            info = self.get_module_info(hModule)
            return info.lpBaseOfDll
        



    type_to_format = {int:'i', float:'f', long:'q', double:'d', char:'c', bool:'?', short:'h', ushort:'H'}

    def get_format_for_struct(self, struct):
    
        template = struct()
        members = [attr for attr in template.__ordered__ if not callable(getattr(template, attr)) and not attr.startswith("__")]
        fmt = ''
    
        for m in members:
            attribute = getattr(template, m)
            t = type(attribute)
            if(isinstance(attribute, padding)):
                size = attribute.size
                fmt += 'B' * size
            elif t in self.type_to_format:
                fmt += self.type_to_format[t]
            else:
                fmt += self.get_format_for_struct(t)
        return fmt 
    
    
    def get_num_of_values(self, struct):
        template = struct()
        members = [attr for attr in template.__ordered__ if not callable(getattr(template, attr)) and not attr.startswith("__")]
        return len(members)
    
    def data_to_class(self, struct, values):
        template = struct()
        members = [attr for attr in template.__ordered__ if not callable(getattr(template, attr)) and not attr.startswith("__")]
    
        value_index = 0
        for i in range(len(members)):
            attribute = getattr(template, members[i])
            t = type(attribute)
            if isinstance(attribute, padding):
                size = attribute.size
                value_index += size
            elif t in self.type_to_format:
                setattr(template, members[i], values[value_index])
                value_index += 1
            else:
                num = self.get_num_of_values(t)
                setattr(template, members[i], self.data_to_class(t, values[value_index:value_index+num]))
                value_index += num
        return template

    def read_class(self, c, address):
        fmt = self.get_format_for_struct(c)
        data = self.read_struct(fmt, address)
        return self.data_to_class(c, data)

    #Reading
    def read_memory(self, address, length):
        """ Read an array of bytes from process memory"""
        data = create_string_buffer(length)
        bytesRead = c_ulonglong()
        result = ReadProcessMemory(self.hProcess, address, byref(data), sizeof(data), byref(bytesRead))

        if result:
            return data.raw
        else:
            print ("Failed: Read Memory - Error Code: ", windll.kernel32.GetLastError())
            windll.kernel32.CloseHandle(self.hProcess)
            windll.kernel32.SetLastError(10000)

    def read_pointer(self, offsets):
        is64 = self.is_process_64bit()
        address = 0
        count = len(offsets)
        for i in range(count):
            if i < count - 1:
                if is64:
                    address = self.read_long(address + offsets[i])
                else:
                    address = self.read_int(address + offsets[i])
            else:
                return address + offsets[i]

    def read_struct(self, format, address):
        """ Read structure from memory address """
        buffer = self.read_memory(address, calcsize(format))
        return unpack(format, buffer)

    def read_float(self, address):
        """ Read a float from a memory address """
        return self.read_struct('f', address)[0]

    def read_int(self, address):
        return self.read_struct('i', address)[0]

    def read_long(self, address):
        return self.read_struct('Q', address)[0]


    #Writing
    def write_memory(self, address, data):
        count = c_ulonglong()
        length = len(data)
        c_data = c_char_p(data[count.value:])

        if not WriteProcessMemory(self.hProcess, address, c_data, length, byref(count)):
            print  ("Failed: Write Memory - Error Code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
        else:
            return False

    def write_float(self, address, value):
        self.write_struct('f', address, value)

    def write_int(self, address, value):
        self.write_struct('i', address, value)

    def write_vector(self, address, value):
        b = pack("<%uf" % len(value), *value)
        self.write_memory(address, b)

    def write_struct(self, format, address, values):
        b = pack(format, *values)
        self.write_memory(address, b)