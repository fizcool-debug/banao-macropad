# windows.py
#
# Copyright 2026 Bhawesh Kumar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import ctypes
from .base import BaseInputInjector, BaseAudioController, BaseActiveWindowDetector

class WindowsInputInjector(BaseInputInjector):
    """Windows implementation of virtual keyboard input injection.
    
    To implement this in Windows:
    Use `ctypes.windll.user32.SendInput` to simulate key presses at the OS level.
    """
    
    def __init__(self):
        print("[WindowsInput] Initializing Windows input injection interface.")

    def press_combo(self, keys):
        # Developer reference: Implement using ctypes SendInput struct
        # For example, to inject Ctrl+Alt+T:
        # Send keyboard input events for KEYEVENTF_KEYDOWN and KEYEVENTF_KEYUP
        print(f"[WindowsInput] Injecting key combination: {keys}")

    def type_string(self, text):
        print(f"[WindowsInput] Typing string: {text}")

    def close(self):
        pass


class WindowsAudioController(BaseAudioController):
    """Windows implementation of audio control.
    
    To implement this in Windows:
    Install the Pycaw library (`pip install pycaw`) to interface with WASAPI.
    """
    
    def __init__(self):
        print("[WindowsAudio] Initializing Windows Core Audio WASAPI interface.")

    def get_master_volume(self):
        # Developer reference:
        # from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        # devices = AudioUtilities.GetSpeakers()
        # interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        # volume = ctypes.cast(interface, POINTER(IAudioEndpointVolume))
        # return volume.GetMasterVolumeLevelScalar()
        return 0.5

    def set_master_volume(self, volume):
        # volume.SetMasterVolumeLevelScalar(volume, None)
        print(f"[WindowsAudio] Setting master volume to {volume:.2f}")

    def get_app_volume(self, app_name):
        # sessions = AudioUtilities.GetAllSessions()
        # for session in sessions:
        #     volume = session.SimpleAudioVolume
        #     if session.Process and session.Process.name().lower() == f"{app_name}.exe":
        #         return volume.GetMasterVolume()
        return 0.5

    def set_app_volume(self, app_name, volume):
        # sessions = AudioUtilities.GetAllSessions()
        # for session in sessions:
        #     simple_volume = session.SimpleAudioVolume
        #     if session.Process and session.Process.name().lower() == f"{app_name}.exe":
        #         simple_volume.SetMasterVolume(volume, None)
        print(f"[WindowsAudio] Setting app volume for {app_name} to {volume:.2f}")


class WindowsActiveWindowDetector(BaseActiveWindowDetector):
    """Windows implementation of focused window detector using ctypes.
    
    Retrieves the foreground window and queries its process name purely using
    ctypes (no external dependency).
    """

    def get_active_window_class(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "Global"
            
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Open process for name query
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        process_handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not process_handle:
            return "Global"
            
        # Get process binary name
        psapi = ctypes.windll.psapi
        buf = ctypes.create_string_buffer(260)
        size = ctypes.c_ulong(260)
        
        app_name = "Global"
        if psapi.GetModuleBaseNameA(process_handle, None, buf, size):
            binary_name = buf.value.decode('utf-8', errors='ignore')
            # Strip extension (e.g. 'chrome.exe' -> 'chrome')
            if binary_name.lower().endswith(".exe"):
                app_name = binary_name[:-4].lower()
            else:
                app_name = binary_name.lower()
                
        kernel32.CloseHandle(process_handle)
        return app_name
